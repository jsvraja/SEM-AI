import httpx
import os

async def get_pagespeed_score(url: str) -> dict:
    PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", "")
    
    async def fetch(strategy: str) -> dict:
        try:
            params = {
                "url": url,
                "key": PAGESPEED_API_KEY,
                "strategy": strategy,
                "category": ["performance", "accessibility", "best-practices", "seo"]
            }
            async with httpx.AsyncClient(timeout=50.0) as client:
                res = await client.get(
                    "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                    params=params
                )
                data = res.json()
                if "error" in data:
                    return {"performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0, "fcp": "N/A", "lcp": "N/A", "cls": "N/A", "tbt": "N/A"}

            cats = data.get("lighthouseResult", {}).get("categories", {})
            auds = data.get("lighthouseResult", {}).get("audits", {})
            return {
                "performance": round((cats.get("performance", {}).get("score", 0) or 0) * 100),
                "accessibility": round((cats.get("accessibility", {}).get("score", 0) or 0) * 100),
                "best_practices": round((cats.get("best-practices", {}).get("score", 0) or 0) * 100),
                "seo": round((cats.get("seo", {}).get("score", 0) or 0) * 100),
                "fcp": auds.get("first-contentful-paint", {}).get("displayValue", "N/A"),
                "lcp": auds.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                "cls": auds.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                "tbt": auds.get("total-blocking-time", {}).get("displayValue", "N/A"),
            }
        except Exception as e:
            return {"performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0, "fcp": "N/A", "lcp": "N/A", "cls": "N/A", "tbt": "N/A", "error": str(e)}

    # Mobile மட்டும் — faster, one call
    mobile = await fetch("mobile")
    desktop = await fetch("desktop")
    return {"results": {"mobile": mobile, "desktop": desktop}}
