"""
Google Ads Manager
Handles: OAuth, campaign creation, spend monitoring, auto-pause/resume
"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import yaml
import os
import json
from datetime import datetime, date
from typing import Optional


def get_ads_client(refresh_token: str, customer_id: str = "") -> GoogleAdsClient:
    """Create authenticated Google Ads client from refresh token."""
    config = {
        "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "login_customer_id": os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""),
        "linked_customer_id": customer_id.replace("-", "") if customer_id else "",
        "use_proto_plus": True,
        "transport": "rest",
    }
    # Remove empty linked_customer_id
    if not config["linked_customer_id"]:
        del config["linked_customer_id"]
    return GoogleAdsClient.load_from_dict(config)


# ─── Campaign Creation ────────────────────────────────────────────────────────

def create_campaign_from_report(
    customer_id: str,
    refresh_token: str,
    campaign_name: str,
    daily_budget_usd: float,
    target_countries: list[str],
    keywords: list[str],
    ad_headlines: list[str],
    ad_descriptions: list[str],
    final_url: str,
) -> dict:
    """
    Creates a complete Google Ads campaign:
    1. Budget
    2. Campaign
    3. Ad Group
    4. Keywords
    5. Responsive Search Ad
    """
    client = get_ads_client(refresh_token)
    customer_id = customer_id.replace("-", "")

    try:
        # Step 1: Create budget
        budget_resource = _create_budget(client, customer_id, campaign_name, daily_budget_usd)

        # Step 2: Create campaign
        campaign_resource = _create_campaign(client, customer_id, campaign_name, budget_resource, target_countries)

        # Step 3: Create ad group
        ad_group_resource = _create_ad_group(client, customer_id, campaign_resource)

        # Step 4: Add keywords
        keyword_resources = _add_keywords(client, customer_id, ad_group_resource, keywords)

        # Step 5: Create responsive search ad
        ad_resource = _create_responsive_search_ad(
            client, customer_id, ad_group_resource,
            ad_headlines, ad_descriptions, final_url
        )

        return {
            "success": True,
            "campaign_resource": campaign_resource,
            "ad_group_resource": ad_group_resource,
            "ad_resource": ad_resource,
            "keywords_added": len(keyword_resources),
            "message": f"Campaign '{campaign_name}' created successfully",
        }

    except GoogleAdsException as ex:
        errors = [err.message for err in ex.failure.errors]
        return {"success": False, "errors": errors}


def _create_budget(client, customer_id, name, daily_budget_usd):
    budget_service = client.get_service("CampaignBudgetService")
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.create

    budget.name = f"{name} Budget {datetime.now().strftime('%Y%m%d%H%M%S')}"
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    # Google Ads uses micros (1 USD = 1,000,000 micros)
    budget.amount_micros = int(daily_budget_usd * 1_000_000)
    budget.explicitly_shared = False

    response = budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[budget_op]
    )
    return response.results[0].resource_name


def _create_campaign(client, customer_id, name, budget_resource, target_countries):
    campaign_service = client.get_service("CampaignService")
    geo_service = client.get_service("GeoTargetConstantService")
    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.create

    campaign.name = f"{name} {datetime.now().strftime('%Y%m%d%H%M%S')}"
    campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    campaign.status = client.enums.CampaignStatusEnum.PAUSED  # Start paused for review
    campaign.campaign_budget = budget_resource
    
    # Bidding strategy - Maximize clicks
    campaign.maximize_clicks.CopyFrom(client.get_type("MaximizeClicks"))

    # Network settings
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = True
    campaign.network_settings.target_content_network = False
    campaign.network_settings.target_partner_search_network = False

    response = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[campaign_op]
    )
    return response.results[0].resource_name


def _create_ad_group(client, customer_id, campaign_resource):
    ad_group_service = client.get_service("AdGroupService")
    ad_group_op = client.get_type("AdGroupOperation")
    ad_group = ad_group_op.create

    ad_group.name = f"Ad Group {datetime.now().strftime('%Y%m%d%H%M%S')}"
    ad_group.campaign = campaign_resource
    ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
    ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    ad_group.cpc_bid_micros = 1_000_000  # $1.00 default CPC

    response = ad_group_service.mutate_ad_groups(
        customer_id=customer_id, operations=[ad_group_op]
    )
    return response.results[0].resource_name


def _add_keywords(client, customer_id, ad_group_resource, keywords):
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    operations = []

    for keyword in keywords[:20]:  # Max 20 keywords
        op = client.get_type("AdGroupCriterionOperation")
        criterion = op.create
        criterion.ad_group = ad_group_resource
        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        criterion.keyword.text = keyword
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.PHRASE
        operations.append(op)

    if not operations:
        return []

    response = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=operations
    )
    return [r.resource_name for r in response.results]


def _create_responsive_search_ad(client, customer_id, ad_group_resource, headlines, descriptions, final_url):
    ad_group_ad_service = client.get_service("AdGroupAdService")
    op = client.get_type("AdGroupAdOperation")
    ad_group_ad = op.create

    ad_group_ad.ad_group = ad_group_resource
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

    # Add up to 15 headlines
    for i, text in enumerate(headlines[:15]):
        headline = client.get_type("AdTextAsset")
        headline.text = text[:30]  # Enforce 30 char limit
        ad_group_ad.ad.responsive_search_ad.headlines.append(headline)

    # Add up to 4 descriptions
    for text in descriptions[:4]:
        desc = client.get_type("AdTextAsset")
        desc.text = text[:90]  # Enforce 90 char limit
        ad_group_ad.ad.responsive_search_ad.descriptions.append(desc)

    ad_group_ad.ad.final_urls.append(final_url)

    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id, operations=[op]
    )
    return response.results[0].resource_name


# ─── Campaign Status Control ──────────────────────────────────────────────────

def pause_campaign(customer_id: str, refresh_token: str, campaign_resource_name: str) -> dict:
    """Pause a campaign (called when budget is reached)."""
    client = get_ads_client(refresh_token)
    customer_id = customer_id.replace("-", "")

    try:
        campaign_service = client.get_service("CampaignService")
        op = client.get_type("CampaignOperation")
        campaign = op.update
        campaign.resource_name = campaign_resource_name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED

        from google.protobuf import field_mask_pb2
        op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))

        campaign_service.mutate_campaigns(customer_id=customer_id, operations=[op])
        return {"success": True, "message": "Campaign paused — budget limit reached"}

    except GoogleAdsException as ex:
        return {"success": False, "errors": [e.message for e in ex.failure.errors]}


def enable_campaign(customer_id: str, refresh_token: str, campaign_resource_name: str) -> dict:
    """Resume a paused campaign."""
    client = get_ads_client(refresh_token)
    customer_id = customer_id.replace("-", "")

    try:
        campaign_service = client.get_service("CampaignService")
        op = client.get_type("CampaignOperation")
        campaign = op.update
        campaign.resource_name = campaign_resource_name
        campaign.status = client.enums.CampaignStatusEnum.ENABLED

        from google.protobuf import field_mask_pb2
        op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))

        campaign_service.mutate_campaigns(customer_id=customer_id, operations=[op])
        return {"success": True, "message": "Campaign resumed"}

    except GoogleAdsException as ex:
        return {"success": False, "errors": [e.message for e in ex.failure.errors]}


# ─── Spend Monitoring ─────────────────────────────────────────────────────────

def get_campaign_spend(customer_id: str, refresh_token: str, campaign_resource_name: str) -> dict:
    """Get today's spend for a campaign."""
    client = get_ads_client(refresh_token)
    customer_id = customer_id.replace("-", "")

    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.campaign_budget,
            metrics.cost_micros,
            metrics.clicks,
            metrics.impressions,
            metrics.ctr,
            metrics.average_cpc,
            metrics.conversions
        FROM campaign
        WHERE campaign.resource_name = '{campaign_resource_name}'
        AND segments.date DURING TODAY
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            spend_usd = row.metrics.cost_micros / 1_000_000
            return {
                "success": True,
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "status": row.campaign.status.name,
                "spend_today_usd": round(spend_usd, 2),
                "clicks": row.metrics.clicks,
                "impressions": row.metrics.impressions,
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc_usd": round(row.metrics.average_cpc / 1_000_000, 2),
                "conversions": row.metrics.conversions,
            }
        return {"success": True, "spend_today_usd": 0, "message": "No data yet today"}

    except GoogleAdsException as ex:
        return {"success": False, "errors": [e.message for e in ex.failure.errors]}


def get_all_campaigns_spend(customer_id: str, refresh_token: str) -> list:
    """Get spend for all campaigns today."""
    client = get_ads_client(refresh_token)
    customer_id = customer_id.replace("-", "")
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.resource_name,
            metrics.cost_micros,
            metrics.clicks,
            metrics.impressions,
            metrics.ctr,
            metrics.conversions
        FROM campaign
        WHERE segments.date DURING TODAY
        AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    # Use customer_id directly, not manager account
    customer_id = customer_id.replace("-", "")

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        results = []
        for row in response:
            results.append({
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "resource_name": row.campaign.resource_name,
                "status": row.campaign.status.name,
                "spend_today_usd": round(row.metrics.cost_micros / 1_000_000, 2),
                "clicks": row.metrics.clicks,
                "impressions": row.metrics.impressions,
                "ctr": round(row.metrics.ctr * 100, 2),
                "conversions": row.metrics.conversions,
            })
        return results
    except GoogleAdsException as ex:
        return []


# ─── Budget Monitor (called by scheduler) ────────────────────────────────────

def check_and_enforce_budgets(customer_id: str, refresh_token: str, budget_rules: list) -> list:
    """
    Check all campaigns against budget rules and pause/resume as needed.

    budget_rules format:
    [
        {
            "campaign_resource_name": "customers/123/campaigns/456",
            "monthly_budget_usd": 500.0,
            "monthly_spend_usd": 480.0,  # fetched from DB
            "status": "ENABLED"
        }
    ]
    """
    actions_taken = []

    for rule in budget_rules:
        resource_name = rule["campaign_resource_name"]
        monthly_budget = rule["monthly_budget_usd"]
        monthly_spend = rule["monthly_spend_usd"]
        current_status = rule["status"]

        spend_pct = (monthly_spend / monthly_budget * 100) if monthly_budget > 0 else 0

        if spend_pct >= 100 and current_status == "ENABLED":
            # Over budget — pause immediately
            result = pause_campaign(customer_id, refresh_token, resource_name)
            actions_taken.append({
                "campaign": resource_name,
                "action": "PAUSED",
                "reason": f"Budget exhausted ({spend_pct:.1f}% spent)",
                "result": result,
            })

        elif spend_pct >= 90 and current_status == "ENABLED":
            # Warning threshold — don't pause yet, just alert
            actions_taken.append({
                "campaign": resource_name,
                "action": "WARNING",
                "reason": f"Approaching budget limit ({spend_pct:.1f}% spent)",
            })

        elif spend_pct < 95 and current_status == "PAUSED":
            # Budget reset (new month) — resume
            result = enable_campaign(customer_id, refresh_token, resource_name)
            actions_taken.append({
                "campaign": resource_name,
                "action": "RESUMED",
                "reason": f"Budget available ({spend_pct:.1f}% spent)",
                "result": result,
            })

    return actions_taken
