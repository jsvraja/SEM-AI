from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.ads_manager import (
    create_campaign_from_report, get_all_campaigns_spend,
    pause_campaign, enable_campaign, get_campaign_performance,
    update_campaign_bid, add_negative_keywords, get_customer_currency
)
import os
import httpx
from app.services.gemini import call_gemini, parse_ai_json

router = APIRouter(prefix="/api/google-ads", tags=["google-ads"])

GOOGLE_ADS_BASE = "https://googleads.googleapis.com/v23"


def get_ads_headers(refresh_token: str) -> dict:
    resp = httpx.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    })
    tokens = resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Failed to refresh Google Ads token")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
        "Content-Type": "application/json",
    }
    manager_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    if manager_id:
        headers["login-customer-id"] = manager_id
    return headers


class PublishCampaignRequest(BaseModel):
    refresh_token: str
    customer_id: Optional[str] = ""
    campaign_name: str
    daily_budget_usd: float = 10.0
    target_countries: List[str] = ["IN"]
    keywords: List[str] = []
    headlines: List[str] = []
    descriptions: List[str] = []
    final_url: str


class CampaignActionRequest(BaseModel):
    refresh_token: str
    customer_id: str
    campaign_resource_name: str


class ABTestRequest(BaseModel):
    refresh_token: str
    customer_id: str
    campaign_resource_name: str
    campaign_name: str
    url: str


class NegativeKeywordsRequest(BaseModel):
    refresh_token: str
    customer_id: str
    campaign_resource_name: str
    keywords: List[str]


class BidAdjustRequest(BaseModel):
    refresh_token: str
    customer_id: str
    campaign_resource_name: str
    new_cpc_inr: float


@router.post("/campaigns")
async def get_campaigns(body: dict):
    refresh_token = body.get("refresh_token", "")
    customer_id = body.get("customer_id", "")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        campaigns = get_all_campaigns_spend(customer_id, refresh_token)
        currency = get_customer_currency(customer_id, refresh_token)
        return {"campaigns": campaigns, "total": len(campaigns), "currency": currency}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/publish")
async def publish_campaign(req: PublishCampaignRequest):
    try:
        customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "") or req.customer_id
        result = create_campaign_from_report(
            customer_id=customer_id,
            refresh_token=req.refresh_token,
            campaign_name=req.campaign_name,
            daily_budget_inr=req.daily_budget_usd * 83,
            target_countries=req.target_countries,
            keywords=req.keywords,
            ad_headlines=req.headlines,
            ad_descriptions=req.descriptions,
            final_url=req.final_url,
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/pause")
async def pause(req: CampaignActionRequest):
    return pause_campaign(req.customer_id, req.refresh_token, req.campaign_resource_name)


@router.post("/resume")
async def resume(req: CampaignActionRequest):
    return enable_campaign(req.customer_id, req.refresh_token, req.campaign_resource_name)


@router.post("/adjust-bid")
async def adjust_bid(req: BidAdjustRequest):
    new_cpc_micros = int(req.new_cpc_inr * 1_000_000)
    return update_campaign_bid(req.customer_id, req.refresh_token, req.campaign_resource_name, new_cpc_micros)


@router.post("/negative-keywords")
async def negative_kws(req: NegativeKeywordsRequest):
    return add_negative_keywords(req.customer_id, req.refresh_token, req.campaign_resource_name, req.keywords)


@router.post("/ab-test/generate")
async def ab_test_generate(req: ABTestRequest):
    try:
        headers = get_ads_headers(req.refresh_token)
        cid = req.customer_id.replace("-", "")
        
        async with httpx.AsyncClient(timeout=30) as client:
            ads_resp = await client.post(
                f"{GOOGLE_ADS_BASE}/customers/{cid}/googleAds:search",
                headers=headers,
                json={"query": f"""
                    SELECT ad_group_ad.ad.responsive_search_ad.headlines,
                           ad_group_ad.ad.responsive_search_ad.descriptions,
                           ad_group_ad.resource_name,
                           metrics.clicks, metrics.impressions, metrics.ctr
                    FROM ad_group_ad
                    WHERE campaign.resource_name = '{req.campaign_resource_name}'
                    LIMIT 3
                """}
            )
        
        existing_ads = []
        if ads_resp.status_code == 200:
            for row in ads_resp.json().get("results", []):
                ad = row.get("adGroupAd", {}).get("ad", {}).get("responsiveSearchAd", {})
                existing_ads.append({
                    "headlines": [h.get("text") for h in ad.get("headlines", [])],
                    "descriptions": [d.get("text") for d in ad.get("descriptions", [])],
                    "clicks": row.get("metrics", {}).get("clicks", 0),
                    "impressions": row.get("metrics", {}).get("impressions", 0),
                    "ctr": row.get("metrics", {}).get("ctr", 0),
                })

        prompt = f"""You are a Google Ads A/B testing expert. Generate 2 ad variants to test against each other.

Campaign: {req.campaign_name}
URL: {req.url}
Existing ads: {existing_ads}

Return ONLY valid JSON:
{{
  "variant_a": {{
    "name": "Control",
    "angle": "<approach>",
    "headlines": [{{"text": "<max 30 chars>", "char_count": <int>}}],
    "descriptions": [{{"text": "<max 90 chars>", "char_count": <int>}}],
    "hypothesis": "<what we expect to happen>"
  }},
  "variant_b": {{
    "name": "Challenger",
    "angle": "<different approach>",
    "headlines": [{{"text": "<max 30 chars>", "char_count": <int>}}],
    "descriptions": [{{"text": "<max 90 chars>", "char_count": <int>}}],
    "hypothesis": "<what we expect to happen>"
  }},
  "test_duration_days": <int>,
  "success_metric": "<CTR|Conversions|CPC>",
  "recommendation": "<how to determine winner>"
}}"""

        raw = await call_gemini(prompt)
        return parse_ai_json(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def weekly_report(body: dict):
    refresh_token = body.get("refresh_token", "")
    customer_id = body.get("customer_id", "")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    try:
        campaigns = get_all_campaigns_spend(customer_id, refresh_token)
        performance = get_campaign_performance(customer_id, refresh_token)
        
        prompt = f"""You are a Google Ads performance analyst. Generate a weekly performance report.

CAMPAIGNS DATA:
{campaigns}

PERFORMANCE METRICS:
{performance}

Return ONLY valid JSON:
{{
  "summary": "<2-3 sentence overview>",
  "total_spend": <float>,
  "total_clicks": <int>,
  "total_impressions": <int>,
  "avg_ctr": <float>,
  "highlights": ["<highlight1>", "<highlight2>"],
  "issues": ["<issue1>", "<issue2>"],
  "recommendations": [
    {{
      "campaign": "<name>",
      "action": "<action>",
      "reason": "<why>",
      "expected_impact": "<impact>"
    }}
  ],
  "next_week_focus": "<focus area>"
}}"""
        
        raw = await call_gemini(prompt)
        return parse_ai_json(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/autonomous/run")
async def autonomous_run(body: dict):
    refresh_token = body.get("refresh_token", "")
    customer_id = body.get("customer_id", "")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    try:
        campaigns = get_campaign_performance(customer_id, refresh_token)
        
        prompt = f"""You are an autonomous Google Ads optimizer. Analyze campaigns and recommend actions.

CAMPAIGNS:
{campaigns}

Return ONLY valid JSON:
{{
  "actions": [
    {{
      "campaign_resource": "<resource_name>",
      "campaign_name": "<name>",
      "action": "increase_bid|decrease_bid|pause|enable|add_negative_keywords",
      "reason": "<why>",
      "auto_apply": <true if safe change, false if needs approval>,
      "parameters": {{
        "new_cpc_inr": <float or null>,
        "keywords": ["<kw1>"] or null
      }}
    }}
  ],
  "summary": "<what was analyzed>",
  "health_score": <0-100>
}}"""
        
        raw = await call_gemini(prompt)
        result = parse_ai_json(raw)
        
        # Auto-apply safe actions
        applied = []
        pending = []
        for action in result.get("actions", []):
            if action.get("auto_apply") and action["action"] in ["increase_bid", "decrease_bid"]:
                cpc = action.get("parameters", {}).get("new_cpc_inr")
                if cpc:
                    res = update_campaign_bid(
                        customer_id, refresh_token,
                        action["campaign_resource"],
                        int(cpc * 1_000_000)
                    )
                    action["applied"] = res.get("success", False)
                    applied.append(action)
            else:
                pending.append(action)
        
        return {
            "auto_applied": applied,
            "pending_approval": pending,
            "summary": result.get("summary"),
            "health_score": result.get("health_score", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
