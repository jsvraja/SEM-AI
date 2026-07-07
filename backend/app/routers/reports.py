import asyncio
import re
from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.scraper import scrape_website
from app.services.prompts import build_seo_prompt, build_ad_prompt
from app.services.gemini import call_gemini, parse_ai_json

router = APIRouter(prefix="/api", tags=["reports"])


class FullReportRequest(BaseModel):
    url: str
    business_description: Optional[str] = ""
    target_keywords: Optional[list[str]] = []


@router.post("/full-report")
async def full_report(req: FullReportRequest):
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    scraped = await scrape_website(url)

    seo_prompt = build_seo_prompt(scraped)
    ad_prompt = build_ad_prompt(
        scraped,
        req.business_description or scraped.get("title", ""),
        req.target_keywords
    )

    seo_raw, ad_raw = await asyncio.gather(
        call_gemini(seo_prompt),
        call_gemini(ad_prompt)
    )

    try:
        seo_report = parse_ai_json(seo_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SEO JSON parse error: {str(e)}")

    try:
        ad_copy = parse_ai_json(ad_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ad JSON parse error: {str(e)}")

    mock_campaign = {
        "campaign_id": "mock_" + re.sub(r'[^a-z0-9]', '_', url.replace("https://", "").replace("http://", ""))[:20],
        "status": "PREVIEW",
        "network": "Google Search Network",
        "campaign_name": f"SEM-AI — {scraped['title'] or url}",
        "message": "Preview only. Connect Google Ads account to publish.",
    }

    return {
        "url": url,
        "scraped_data": {
            "title": scraped["title"],
            "meta_description": scraped["meta_description"],
            "h1_tags": scraped["h1_tags"],
            "images_count": scraped["images_count"],
            "images_without_alt_count": scraped["images_without_alt_count"],
            "internal_links_count": scraped["internal_links_count"],
            "has_schema_markup": scraped["has_schema_markup"],
            "html_size_kb": scraped["html_size_kb"],
        },
        "seo_report": seo_report,
        "ad_copy": ad_copy,
        "mock_campaign": mock_campaign,
    }
