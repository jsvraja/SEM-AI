"""
Google Ads Manager - Direct REST API implementation
Bypasses grpc issues by using httpx REST calls directly
"""

import os
import json
import httpx
from datetime import datetime, date
from typing import Optional

GOOGLE_ADS_BASE = "https://googleads.googleapis.com/v16"


def get_headers(refresh_token: str) -> dict:
    """Get auth headers by refreshing access token."""
    token_url = "https://oauth2.googleapis.com/token"
    print(f"Refreshing access token...")
    resp = httpx.post(token_url, data={
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=15)
    print(f"Token refresh status: {resp.status_code}")
    tokens = resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise Exception(f"Failed to get access token: {tokens}")
    print(f"Got access token: {access_token[:20]}...")

    manager_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
        "Content-Type": "application/json",
    }
    if manager_id:
        headers["login-customer-id"] = manager_id
    print(f"Headers ready. Manager ID: {manager_id}")
    return headers


def gaql_search(customer_id: str, refresh_token: str, query: str) -> list:
    """Execute a GAQL query via REST."""
    headers = get_headers(refresh_token)
    cid = customer_id.replace("-", "")
    url = f"{GOOGLE_ADS_BASE}/customers/{cid}/googleAds:search"
    resp = httpx.post(url, headers=headers, json={"query": query}, timeout=30)
    if resp.status_code != 200:
        print(f"GAQL error {resp.status_code}: {resp.text[:300]}")
        return []
    data = resp.json()
    return data.get("results", [])


# ─── Campaign Operations ──────────────────────────────────────────────────────

def create_campaign_from_report(
    customer_id: str,
    refresh_token: str,
    campaign_name: str,
    daily_budget_usd: float,
    target_countries: list,
    keywords: list,
    ad_headlines: list,
    ad_descriptions: list,
    final_url: str,
) -> dict:
    """Create full campaign via REST API."""
    cid = customer_id.replace("-", "")
    headers = get_headers(refresh_token)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    try:
        # Step 1: Create budget
        print("Step 1: Creating budget...")
        budget_resource = _rest_create_budget(cid, headers, campaign_name, daily_budget_usd, timestamp)
        print(f"Budget: {budget_resource}")

        # Step 2: Create campaign
        print("Step 2: Creating campaign...")
        campaign_resource = _rest_create_campaign(cid, headers, campaign_name, budget_resource, timestamp)
        print(f"Campaign: {campaign_resource}")

        # Step 3: Create ad group
        print("Step 3: Creating ad group...")
        ad_group_resource = _rest_create_ad_group(cid, headers, campaign_resource, timestamp)
        print(f"Ad group: {ad_group_resource}")

        # Step 4: Add keywords
        print("Step 4: Adding keywords...")
        kw_count = _rest_add_keywords(cid, headers, ad_group_resource, keywords)
        print(f"Keywords added: {kw_count}")

        # Step 5: Create ad
        print("Step 5: Creating ad...")
        ad_resource = _rest_create_ad(cid, headers, ad_group_resource, ad_headlines, ad_descriptions, final_url)
        print(f"Ad: {ad_resource}")

        return {
            "success": True,
            "campaign_resource": campaign_resource,
            "ad_group_resource": ad_group_resource,
            "ad_resource": ad_resource,
            "keywords_added": kw_count,
            "message": f"Campaign '{campaign_name}' created successfully",
        }

    except Exception as e:
        print(f"Campaign creation error: {e}")
        return {"success": False, "errors": [str(e)]}


def _rest_create_budget(cid, headers, name, daily_budget_usd, timestamp):
    url = f"{GOOGLE_ADS_BASE}/customers/{cid}/campaignBudgets:mutate"
    body = {"operations": [{"create": {
        "name": f"{name} Budget {timestamp}",
        "amountMicros": str(int(daily_budget_usd * 1_000_000)),
        "deliveryMethod": "STANDARD",
        "explicitlyShared": False,
    }}]}
    print(f"Budget URL: {url}")
    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    print(f"Budget response status: {resp.status_code}")
    print(f"Budget response: {resp.text[:300]}")
    if not resp.text:
        raise Exception(f"Empty response from budget API. Status: {resp.status_code}")
    data = resp.json()
    if resp.status_code != 200:
        raise Exception(f"Budget creation failed: {data}")
    return data["results"][0]["resourceName"]


def _rest_create_campaign(cid, headers, name, budget_resource, timestamp):
    url = f"{GOOGLE_ADS_BASE}/customers/{cid}/campaigns:mutate"
    body = {"operations": [{"create": {
        "name": f"{name} {timestamp}",
        "advertisingChannelType": "SEARCH",
        "status": "PAUSED",
        "campaignBudget": budget_resource,
        "manualCpc": {"enhancedCpcEnabled": False},
        "networkSettings": {
            "targetGoogleSearch": True,
            "targetSearchNetwork": True,
            "targetContentNetwork": False,
            "targetPartnerSearchNetwork": False,
        },
    }}]}
    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    data = resp.json()
    if resp.status_code != 200:
        raise Exception(f"Campaign creation failed: {data}")
    return data["results"][0]["resourceName"]


def _rest_create_ad_group(cid, headers, campaign_resource, timestamp):
    url = f"{GOOGLE_ADS_BASE}/customers/{cid}/adGroups:mutate"
    body = {"operations": [{"create": {
        "name": f"Ad Group {timestamp}",
        "campaign": campaign_resource,
        "status": "ENABLED",
        "type": "SEARCH_STANDARD",
        "cpcBidMicros": str(1_000_000),
    }}]}
    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    data = resp.json()
    if resp.status_code != 200:
        raise Exception(f"Ad group creation failed: {data}")
    return data["results"][0]["resourceName"]


def _rest_add_keywords(cid, headers, ad_group_resource, keywords):
    if not keywords:
        return 0
    url = f"{GOOGLE_ADS_BASE}/customers/{cid}/adGroupCriteria:mutate"
    operations = []
    for kw in keywords[:20]:
        operations.append({"create": {
            "adGroup": ad_group_resource,
            "status": "ENABLED",
            "keyword": {"text": kw, "matchType": "PHRASE"},
        }})
    body = {"operations": operations}
    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    data = resp.json()
    if resp.status_code != 200:
        print(f"Keywords warning: {data}")
        return 0
    return len(data.get("results", []))


def _rest_create_ad(cid, headers, ad_group_resource, headlines, descriptions, final_url):
    url = f"{GOOGLE_ADS_BASE}/customers/{cid}/adGroupAds:mutate"
    rsa_headlines = [{"text": h[:30]} for h in headlines[:15]]
    rsa_descriptions = [{"text": d[:90]} for d in descriptions[:4]]
    body = {"operations": [{"create": {
        "adGroup": ad_group_resource,
        "status": "ENABLED",
        "ad": {
            "finalUrls": [final_url],
            "responsiveSearchAd": {
                "headlines": rsa_headlines,
                "descriptions": rsa_descriptions,
            },
        },
    }}]}
    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    data = resp.json()
    if resp.status_code != 200:
        raise Exception(f"Ad creation failed: {data}")
    return data["results"][0]["resourceName"]


# ─── Campaign Control ─────────────────────────────────────────────────────────

def _update_campaign_status(customer_id: str, refresh_token: str, campaign_resource_name: str, status: str) -> dict:
    cid = customer_id.replace("-", "")
    headers = get_headers(refresh_token)
    url = f"{GOOGLE_ADS_BASE}/customers/{cid}/campaigns:mutate"
    body = {"operations": [{"update": {
        "resourceName": campaign_resource_name,
        "status": status,
    }, "updateMask": "status"}]}
    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    data = resp.json()
    if resp.status_code != 200:
        return {"success": False, "errors": [str(data)]}
    return {"success": True, "message": f"Campaign {status.lower()}"}


def pause_campaign(customer_id: str, refresh_token: str, campaign_resource_name: str) -> dict:
    return _update_campaign_status(customer_id, refresh_token, campaign_resource_name, "PAUSED")


def enable_campaign(customer_id: str, refresh_token: str, campaign_resource_name: str) -> dict:
    return _update_campaign_status(customer_id, refresh_token, campaign_resource_name, "ENABLED")


# ─── Metrics ──────────────────────────────────────────────────────────────────

def get_campaign_spend(customer_id: str, refresh_token: str, campaign_resource_name: str) -> dict:
    query = f"""
        SELECT campaign.id, campaign.name, campaign.status,
               metrics.cost_micros, metrics.clicks, metrics.impressions,
               metrics.ctr, metrics.average_cpc, metrics.conversions
        FROM campaign
        WHERE campaign.resource_name = '{campaign_resource_name}'
        AND segments.date DURING TODAY
    """
    results = gaql_search(customer_id, refresh_token, query)
    if not results:
        return {"success": True, "spend_today_usd": 0, "message": "No data yet"}
    row = results[0]
    campaign = row.get("campaign", {})
    metrics = row.get("metrics", {})
    return {
        "success": True,
        "campaign_id": campaign.get("id"),
        "campaign_name": campaign.get("name"),
        "status": campaign.get("status"),
        "spend_today_usd": round(int(metrics.get("costMicros", 0)) / 1_000_000, 2),
        "clicks": metrics.get("clicks", 0),
        "impressions": metrics.get("impressions", 0),
        "ctr": round(float(metrics.get("ctr", 0)) * 100, 2),
        "avg_cpc_usd": round(int(metrics.get("averageCpc", 0)) / 1_000_000, 2),
        "conversions": metrics.get("conversions", 0),
    }


def get_all_campaigns_spend(customer_id: str, refresh_token: str) -> list:
    """Get all campaigns with today's metrics via REST."""
    cid = customer_id.replace("-", "")
    query = """
        SELECT campaign.id, campaign.name, campaign.status, campaign.resource_name,
               metrics.cost_micros, metrics.clicks, metrics.impressions,
               metrics.ctr, metrics.conversions
        FROM campaign
        WHERE segments.date DURING TODAY
        AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    try:
        results = gaql_search(cid, refresh_token, query)
        campaigns = []
        for row in results:
            campaign = row.get("campaign", {})
            metrics = row.get("metrics", {})
            campaigns.append({
                "campaign_id": campaign.get("id"),
                "campaign_name": campaign.get("name"),
                "resource_name": campaign.get("resourceName"),
                "status": campaign.get("status", "UNKNOWN"),
                "spend_today_usd": round(int(metrics.get("costMicros", 0)) / 1_000_000, 2),
                "clicks": int(metrics.get("clicks", 0)),
                "impressions": int(metrics.get("impressions", 0)),
                "ctr": round(float(metrics.get("ctr", 0)) * 100, 2),
                "conversions": float(metrics.get("conversions", 0)),
            })
        return campaigns
    except Exception as e:
        print(f"get_all_campaigns_spend error: {e}")
        return []
