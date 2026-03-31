from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import json
import re
import asyncio
import os
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# Configure Gemini with new SDK
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-flash"

app = FastAPI(title="SEM AI Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ──────────────────────────────────────────────────────────────────

class FullReportRequest(BaseModel):
    url: str
    business_description: Optional[str] = ""
    target_keywords: Optional[list[str]] = []

# ─── Website Scraper ─────────────────────────────────────────────────────────

async def scrape_website(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SEMBot/1.0)"}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as c:
            response = await c.get(url, headers=headers)
            html = response.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {str(e)}")

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("title")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_kw = soup.find("meta", attrs={"name": "keywords"})
    canonical = soup.find("link", attrs={"rel": "canonical"})
    robots = soup.find("meta", attrs={"name": "robots"})
    viewport = soup.find("meta", attrs={"name": "viewport"})
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")][:10]
    h3s = [h.get_text(strip=True) for h in soup.find_all("h3")][:10]

    all_links = soup.find_all("a", href=True)
    internal_links = [l["href"] for l in all_links if url in l["href"] or l["href"].startswith("/")]
    external_links = [l["href"] for l in all_links if l["href"].startswith("http") and url not in l["href"]]

    images = soup.find_all("img")
    images_without_alt = [img.get("src", "") for img in images if not img.get("alt")]

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = soup.get_text(separator=" ", strip=True)
    body_text = re.sub(r'\s+', ' ', body_text)[:3000]

    schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "meta_description": meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
        "meta_keywords": meta_kw["content"] if meta_kw and meta_kw.get("content") else None,
        "canonical_url": canonical["href"] if canonical and canonical.get("href") else None,
        "robots_meta": robots["content"] if robots and robots.get("content") else None,
        "has_viewport": viewport is not None,
        "og_title": og_title["content"] if og_title and og_title.get("content") else None,
        "og_description": og_desc["content"] if og_desc and og_desc.get("content") else None,
        "h1_tags": h1s,
        "h2_tags": h2s,
        "h3_tags": h3s,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "images_count": len(images),
        "images_without_alt_count": len(images_without_alt),
        "has_schema_markup": len(schema_tags) > 0,
        "body_text_sample": body_text,
        "html_size_kb": round(len(html) / 1024, 1),
    }

# ─── AI Prompts ──────────────────────────────────────────────────────────────

def build_seo_prompt(s: dict) -> str:
    return f"""You are a senior SEO and SEM specialist. Analyze this website data and return a detailed, actionable report.

WEBSITE DATA:
URL: {s['url']}
Title: {s['title']}
Meta Description: {s['meta_description']}
H1 Tags: {s['h1_tags']}
H2 Tags: {s['h2_tags']}
Internal Links: {s['internal_links_count']}
External Links: {s['external_links_count']}
Images: {s['images_count']} total, {s['images_without_alt_count']} missing alt text
Has Schema Markup: {s['has_schema_markup']}
Has Viewport Meta: {s['has_viewport']}
HTML Size: {s['html_size_kb']} KB
Body Text Sample: {s['body_text_sample'][:1500]}

Return ONLY valid JSON with no markdown, no code fences, no explanation. Start your response with {{ and end with }}:
{{
  "overall_seo_score": <integer 0-100>,
  "summary": "<2-3 sentence overall assessment>",
  "strengths": [
    {{"point": "<strength>", "impact": "high"}}
  ],
  "weaknesses": [
    {{"point": "<weakness>", "impact": "high", "fix": "<specific fix>"}}
  ],
  "technical_issues": [
    {{"issue": "<name>", "severity": "critical", "description": "<detail>", "recommendation": "<action>"}}
  ],
  "content_analysis": {{
    "quality_score": <integer 0-100>,
    "readability": "<assessment>",
    "keyword_density": "<assessment>",
    "content_gaps": ["<gap1>", "<gap2>"]
  }},
  "keyword_suggestions": [
    {{"keyword": "<keyword>", "intent": "transactional", "difficulty": "medium", "priority": "primary"}}
  ],
  "sem_recommendations": {{
    "suggested_monthly_budget_usd": {{"min": <int>, "max": <int>}},
    "bidding_strategy": "<strategy name and reason>",
    "target_countries": ["<country1>", "<country2>"],
    "audience_segments": [
      {{"segment": "<name>", "age_range": "<range>", "interests": ["<interest1>", "<interest2>"]}}
    ],
    "estimated_monthly_clicks": {{"min": <int>, "max": <int>}},
    "estimated_cpc_usd": {{"min": <float>, "max": <float>}}
  }},
  "competitor_insights": {{
    "likely_competitors": ["<domain1>", "<domain2>"],
    "positioning_suggestion": "<how to differentiate>"
  }},
  "priority_actions": [
    {{"action": "<action>", "effort": "low", "impact": "high"}}
  ]
}}"""


def build_ad_prompt(s: dict, desc: str, kws: list) -> str:
    return f"""You are a Google Ads copywriting expert. Generate high-converting, policy-compliant Google Ads content.

BUSINESS INFO:
URL: {s['url']}
Page Title: {s['title']}
Meta Description: {s['meta_description']}
Business Description: {desc}
Target Keywords: {kws}
Content Sample: {s['body_text_sample'][:800]}

STRICT RULES:
- Headlines: MAXIMUM 30 characters each (count carefully, spaces count)
- Descriptions: MAXIMUM 90 characters each (count carefully, spaces count)
- No exclamation marks more than once per ad
- Be specific and benefit-focused
- Each variant must have a distinct angle

Return ONLY valid JSON with no markdown, no code fences, no explanation. Start with {{ and end with }}:
{{
  "ad_variants": [
    {{
      "variant_name": "Value-Led",
      "angle": "<brief angle description>",
      "headlines": [
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}}
      ],
      "descriptions": [
        {{"text": "<max 90 chars>", "char_count": <int>}},
        {{"text": "<max 90 chars>", "char_count": <int>}},
        {{"text": "<max 90 chars>", "char_count": <int>}}
      ],
      "display_url_path": "/free-trial"
    }},
    {{
      "variant_name": "Feature-Led",
      "angle": "<brief angle description>",
      "headlines": [
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}}
      ],
      "descriptions": [
        {{"text": "<max 90 chars>", "char_count": <int>}},
        {{"text": "<max 90 chars>", "char_count": <int>}},
        {{"text": "<max 90 chars>", "char_count": <int>}}
      ],
      "display_url_path": "/features"
    }},
    {{
      "variant_name": "Social Proof",
      "angle": "<brief angle description>",
      "headlines": [
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}},
        {{"text": "<max 30 chars>", "char_count": <int>}}
      ],
      "descriptions": [
        {{"text": "<max 90 chars>", "char_count": <int>}},
        {{"text": "<max 90 chars>", "char_count": <int>}},
        {{"text": "<max 90 chars>", "char_count": <int>}}
      ],
      "display_url_path": "/reviews"
    }}
  ],
  "recommended_extensions": {{
    "sitelinks": ["<sitelink1>", "<sitelink2>", "<sitelink3>", "<sitelink4>"],
    "callouts": ["<callout1>", "<callout2>", "<callout3>"],
    "structured_snippets": ["<snippet1>", "<snippet2>"]
  }},
  "campaign_settings": {{
    "campaign_type": "Search",
    "ad_rotation": "Optimize: Prefer best performing ads",
    "keyword_match_types": ["Phrase match", "Exact match"],
    "negative_keywords": ["<neg1>", "<neg2>", "<neg3>"],
    "landing_page_recommendation": "<recommendation>"
  }}
}}"""


def parse_ai_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```\s*$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()
    return json.loads(raw)


async def call_gemini(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    def sync_call():
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=8000,
            )
        )
        return response.text
    return await loop.run_in_executor(None, sync_call)

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "SEM AI Platform running", "version": "1.0.0", "ai": GEMINI_MODEL}


@app.post("/api/full-report")
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
        raise HTTPException(
            status_code=500,
            detail=f"SEO JSON parse error: {str(e)}\nRaw: {seo_raw[:400]}"
        )

    try:
        ad_copy = parse_ai_json(ad_raw)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ad JSON parse error: {str(e)}\nRaw: {ad_raw[:400]}"
        )

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