import httpx
import os

PAGESPEED_API_KEY = os.environ.get("AIzaSyBy29VGo25srMogAolYrnDcESDCgVBmork", "")

async def get_pagespeed_score(url: str) -> dict:
    try:
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        params = {
            "url": url,
            "key": PAGESPEED_API_KEY,
            "strategy": "mobile",
            "category": ["performance", "accessibility", "best-practices", "seo"]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(api_url, params=params)
            data = res.json()

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
        return {
            "performance": 0,
            "accessibility": 0,
            "best_practices": 0,
            "seo": 0,
            "fcp": "N/A",
            "lcp": "N/A",
            "cls": "N/A",
            "tbt": "N/A",
            "error": str(e)
        }
