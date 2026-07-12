from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
from bs4 import BeautifulSoup
import re
from app.services.gemini import call_gemini, parse_ai_json

router = APIRouter(prefix="/api/ads", tags=["ads"])


class RecommendPagesRequest(BaseModel):
    url: str
    pages_to_scan: int = 50
    token: Optional[str] = ""


@router.post("/recommend-pages")
async def recommend_pages(req: RecommendPagesRequest):
    base_url = req.url.strip().rstrip("/")
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Crawl homepage to find links
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            res = await client.get(base_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {str(e)}")

    # Find internal links
    links = set()
    links.add(base_url)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") and len(href) > 1:
            links.add(base_url + href)
        elif href.startswith(base_url):
            links.add(href)

    links = list(links)[:req.pages_to_scan]

    # Analyze each page briefly
    pages_data = []
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for link in links[:10]:  # Limit to 10 for speed
            try:
                r = await client.get(link, headers=headers)
                s = BeautifulSoup(r.text, "html.parser")
                title = s.find("title")
                meta = s.find("meta", attrs={"name": "description"})
                h1s = [h.get_text(strip=True) for h in s.find_all("h1")][:2]
                for tag in s(["script", "style", "nav", "footer"]):
                    tag.decompose()
                body = re.sub(r'\s+', ' ', s.get_text(separator=" ", strip=True))[:500]
                pages_data.append({
                    "url": link,
                    "title": title.get_text(strip=True) if title else "",
                    "meta": meta["content"] if meta and meta.get("content") else "",
                    "h1": h1s[0] if h1s else "",
                    "content": body
                })
            except:
                continue

    if not pages_data:
        return {"recommended_pages": [], "total_pages_analysed": 0}

    # Ask Gemini which pages are best for ads
    prompt = f"""You are a Google Ads expert. Analyze these pages and recommend the best ones for Google Ads campaigns.

PAGES:
{pages_data}

Return ONLY valid JSON:
{{
  "recommended_pages": [
    {{
      "url": "<page url>",
      "title": "<page title>",
      "reason": "<why this page is good for ads>",
      "ad_copy": {{
        "headline_1": "<max 30 chars>",
        "headline_2": "<max 30 chars>",
        "headline_3": "<max 30 chars>",
        "description_1": "<max 90 chars>",
        "description_2": "<max 90 chars>"
      }},
      "target_keywords": ["<keyword1>", "<keyword2>"],
      "estimated_cpc": "<INR range>"
    }}
  ],
  "total_pages_analysed": {len(pages_data)}
}}"""

    try:
        raw = await call_gemini(prompt)
        result = parse_ai_json(raw)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
