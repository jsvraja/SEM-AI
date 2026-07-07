import httpx
import os
import asyncio

async def fetch_strategy(url: str, strategy: str, key: str) -> dict:
    try:
        params = {
            "url": url,
            "key": key,
            "strategy": strategy,
            "category": ["performance", "accessibility", "best-practices", "seo"]
        }
        async with httpx.AsyncClient(timeout=55.0) as client:
            res = await client.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params=params
            )
            data = res.json()
            if "error" in data:
                return {"performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0, "fcp": "N/A", "lcp": "N/A", "cls": "N/A", "tbt": "N/A"}

        categories = data.get("lighthouseResult", {}).get("categories", {})
        audits = data.get("lighthouseResult", {}).get("audits", {})
        return {
            "performance": round((categories.get("performance", {}).get("score", 0) or 0) * 100),
            "accessibility": round((categories.get("accessibility", {}).get("score", 0) or 0) * 100),
            "best_practices": round((categories.get("best-practices", {}).get("score", 0) or 0) * 100),
            "seo": round((categories.get("seo", {}).get("score", 0) or 0) * 100),
            "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
            "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
            "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
            "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
        }
    except Exception as e:
        return {"performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0, "fcp": "N/A", "lcp": "N/A", "cls": "N/A", "tbt": "N/A", "error": str(e)}


async def get_pagespeed_score(url: str) -> dict:
    PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", "")
    mobile, desktop = await asyncio.gather(
        fetch_strategy(url, "mobile", PAGESPEED_API_KEY),
        fetch_strategy(url, "desktop", PAGESPEED_API_KEY)
    )
    return {"results": {"mobile": mobile, "desktop": desktop}}
