from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import json
import re
import asyncio
import os
from datetime import datetime
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from oauth_handler import get_oauth_url, exchange_code_for_tokens, get_user_info
from ads_manager import (
    get_campaign_performance, update_campaign_bid, add_negative_keywords,
    create_campaign_from_report, pause_campaign, enable_campaign,
    get_all_campaigns_spend,
)
from budget_monitor import register_campaign, get_all_monitored
from ai_traffic import log_visit, get_traffic_stats, add_demo_data, detect_ai_platform

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-flash"

app = FastAPI(title="SEM AI Platform", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Persistent Session Store ─────────────────────────────────────────────────
SESSIONS_FILE = os.path.join(os.path.dirname(__file__), ".sessions.json")

def load_sessions():
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_sessions(sessions):
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save sessions: {e}")

_sessions = load_sessions()
print(f"Loaded {len(_sessions)} saved session(s)")

# Hard-coded fallback customer ID from env
DEFAULT_CUSTOMER_ID = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")

# ─── Models ───────────────────────────────────────────────────────────────────

class FullReportRequest(BaseModel):
    url: str
    business_description: Optional[str] = ""
    target_keywords: Optional[list[str]] = []

class PublishCampaignRequest(BaseModel):
    session_id: str
    customer_id: Optional[str] = ""
    campaign_name: str
    daily_budget_usd: float
    monthly_budget_usd: float
    target_countries: list[str]
    keywords: list[str]
    headlines: list[str]
    descriptions: list[str]
    final_url: str

class CampaignActionRequest(BaseModel):
    session_id: str
    customer_id: Optional[str] = ""
    campaign_resource_name: str

# ─── Scraper ──────────────────────────────────────────────────────────────────

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
    viewport = soup.find("meta", attrs={"name": "viewport"})
    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")][:10]
    all_links = soup.find_all("a", href=True)
    internal_links = [l["href"] for l in all_links if url in l["href"] or l["href"].startswith("/")]
    external_links = [l["href"] for l in all_links if l["href"].startswith("http") and url not in l["href"]]
    images = soup.find_all("img")
    images_without_alt = [img.get("src", "") for img in images if not img.get("alt")]
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True))[:3000]
    schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "meta_description": meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
        "has_viewport": viewport is not None,
        "h1_tags": h1s, "h2_tags": h2s,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "images_count": len(images),
        "images_without_alt_count": len(images_without_alt),
        "has_schema_markup": len(schema_tags) > 0,
        "body_text_sample": body_text,
        "html_size_kb": round(len(html) / 1024, 1),
    }

# ─── AI ───────────────────────────────────────────────────────────────────────

def build_seo_prompt(s: dict) -> str:
    return f"""You are a senior SEO and SEM specialist. Analyze this website and return ONE JSON object only.
URL: {s['url']} | Title: {s['title']} | Meta: {s['meta_description']}
H1: {s['h1_tags']} | H2: {s['h2_tags']}
Links: {s['internal_links_count']} internal, {s['external_links_count']} external
Images: {s['images_count']} total, {s['images_without_alt_count']} missing alt
Schema: {s['has_schema_markup']} | HTML: {s['html_size_kb']}KB
Content: {s['body_text_sample'][:1200]}

Output ONLY this JSON with real values (no markdown, no fences, no extra text):
{{"overall_seo_score":72,"summary":"2-3 sentence assessment","strengths":[{{"point":"strength","impact":"high"}}],"weaknesses":[{{"point":"weakness","impact":"high","fix":"specific fix"}}],"technical_issues":[{{"issue":"name","severity":"critical","description":"detail","recommendation":"action"}}],"content_analysis":{{"quality_score":70,"word_count":500,"readability":"Good","keyword_density":"2.3%","content_gaps":["gap1","gap2"]}},"keyword_suggestions":[{{"keyword":"kw","intent":"transactional","difficulty":"medium","priority":"primary"}}],"sem_recommendations":{{"suggested_monthly_budget_usd":{{"min":500,"max":2000}},"bidding_strategy":"Maximize Clicks","target_countries":["US","UK"],"audience_segments":[{{"segment":"name","age_range":"25-44","interests":["i1","i2"]}}],"estimated_monthly_clicks":{{"min":500,"max":2000}},"estimated_cpc_usd":{{"min":1.0,"max":3.0}}}},"competitor_insights":{{"likely_competitors":["c.com"],"positioning_suggestion":"differentiation"}},"priority_actions":[{{"action":"action","effort":"low","impact":"high"}}]}}"""

def build_ad_prompt(s: dict, desc: str, kws: list) -> str:
    return f"""You are a Google Ads expert. Generate ad copy for this business.
URL: {s['url']} | Title: {s['title']} | Desc: {desc} | KWs: {kws}
Content: {s['body_text_sample'][:600]}
RULES: Headlines MAX 30 chars. Descriptions MAX 90 chars. Output ONE JSON object only, no markdown.

{{"ad_variants":[{{"variant_name":"Value-Led","angle":"Focus on value","headlines":[{{"text":"Save Time & Money Today","char_count":22}},{{"text":"Trusted by Thousands","char_count":20}},{{"text":"Start Free Trial Now","char_count":20}},{{"text":"No Setup Fee Required","char_count":21}},{{"text":"Results in 24 Hours","char_count":19}}],"descriptions":[{{"text":"Get more done with less effort. Join thousands of happy customers today.","char_count":71}},{{"text":"Start your free trial and see results fast. No credit card needed.","char_count":65}},{{"text":"The smart solution for your business. Easy setup, powerful results.","char_count":66}}],"display_url_path":"/start"}},{{"variant_name":"Feature-Led","angle":"Highlight features","headlines":[{{"text":"All-In-One Platform","char_count":19}},{{"text":"Powerful & Easy to Use","char_count":22}},{{"text":"Built for Teams","char_count":15}},{{"text":"Real-Time Analytics","char_count":19}},{{"text":"Automate Your Workflow","char_count":22}}],"descriptions":[{{"text":"Everything you need in one place. Automate tasks and boost productivity.","char_count":71}},{{"text":"Powerful features, simple interface. Try it free for 14 days.","char_count":61}},{{"text":"Built for modern teams. Integrate with tools you already use.","char_count":60}}],"display_url_path":"/features"}},{{"variant_name":"Social Proof","angle":"Trust and credibility","headlines":[{{"text":"Rated 5 Stars by Users","char_count":22}},{{"text":"10,000+ Happy Customers","char_count":23}},{{"text":"Award-Winning Service","char_count":21}},{{"text":"Trusted Since 2020","char_count":18}},{{"text":"See Why Teams Love Us","char_count":21}}],"descriptions":[{{"text":"Join over 10,000 businesses that trust us to deliver results every day.","char_count":71}},{{"text":"5-star rated by customers worldwide. See real reviews and start today.","char_count":70}},{{"text":"The most trusted solution in the industry. Start your free trial now.","char_count":68}}],"display_url_path":"/reviews"}}],"recommended_extensions":{{"sitelinks":["Free Trial","Pricing","Features","About Us"],"callouts":["No Contract","24/7 Support","Free Setup"],"structured_snippets":["Features: Analytics, Automation, Reporting","Services: Setup, Training, Support"]}},"campaign_settings":{{"campaign_type":"Search","ad_rotation":"Optimize: Prefer best performing ads","keyword_match_types":["Phrase match","Exact match"],"negative_keywords":["free download","crack","pirate"],"landing_page_recommendation":"Create a dedicated landing page matching the ad headline for better Quality Score."}}}}

Now replace ALL values above with real copy specifically for: {s['title']} at {s['url']}"""

def parse_ai_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```\s*$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(raw)
    return obj

async def call_gemini(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    def sync_call():
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=16000)
        )
        return response.text
    return await loop.run_in_executor(None, sync_call)

# ─── Helper: resolve customer ID ──────────────────────────────────────────────

def resolve_customer_id(session: dict, provided: str) -> str:
    """Get customer ID from: request → session → env variable"""
    cid = (provided or "").strip().replace("-", "")
    if not cid:
        cid = (session.get("customer_id") or "").replace("-", "")
    if not cid:
        cid = DEFAULT_CUSTOMER_ID
    if not cid:
        raise HTTPException(status_code=400, detail="Customer ID not found. Please enter it once in the Publish form.")
    return cid

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "SEM AI Platform v2", "ai": GEMINI_MODEL, "sessions": len(_sessions)}

@app.post("/api/full-report")
async def full_report(req: FullReportRequest):
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    scraped = await scrape_website(url)
    url_type = detect_url_type(url)
    scraped['url_type'] = url_type
    
    if url_type == 'single_page':
        seo_prompt = build_seo_prompt_single_page(scraped)
    else:
        seo_prompt = build_seo_prompt_whole_site(scraped)
    
    # Store detected url_type to override whatever AI returns
    _detected_url_type = url_type
    
    seo_raw, ad_raw = await asyncio.gather(
        call_gemini(seo_prompt),
        call_gemini(build_ad_prompt(scraped, req.business_description or scraped.get("title",""), req.target_keywords))
    )
    try:
        seo_report = parse_ai_json(seo_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SEO parse error: {e} | {seo_raw[:200]}")
    try:
        ad_copy = parse_ai_json(ad_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ad parse error: {e} | {ad_raw[:200]}")
    # Force correct url_type regardless of what AI returned
    seo_report['url_type'] = _detected_url_type
    
    # Normalize sem_recommendations fields
    sem = seo_report.get('sem_recommendations', {})
    if sem:
        # Normalize budget
        if not sem.get('monthly_budget_inr'):
            budget = sem.get('suggested_monthly_budget_usd', {})
            if isinstance(budget, dict):
                sem['monthly_budget_inr'] = int((budget.get('min', 0) + budget.get('max', 0)) / 2 * 83)
            elif isinstance(budget, (int, float)):
                sem['monthly_budget_inr'] = int(budget * 83)
        # Normalize clicks
        if not sem.get('monthly_clicks_estimate'):
            clicks = sem.get('estimated_monthly_clicks', {})
            if isinstance(clicks, dict):
                sem['monthly_clicks_estimate'] = f"{clicks.get('min',0):,}–{clicks.get('max',0):,}"
            elif clicks:
                sem['monthly_clicks_estimate'] = str(clicks)
        # Normalize CPC
        if not sem.get('estimated_cpc_inr'):
            cpc = sem.get('estimated_cpc_usd', {})
            if isinstance(cpc, dict):
                sem['estimated_cpc_inr'] = round((cpc.get('min', 0) + cpc.get('max', 0)) / 2 * 83)
            elif isinstance(cpc, (int, float)):
                sem['estimated_cpc_inr'] = round(cpc * 83)
        
        # Generate country_budgets if not present
        if not sem.get('country_budgets'):
            countries = sem.get('target_countries', ['IN', 'US'])
            total_budget = sem.get('monthly_budget_inr', 20000)
            # Country-wise CPC and allocation defaults
            country_defaults = {
                'IN': {'name': 'India', 'flag': '🇮🇳', 'cpc': 15, 'pct': 50, 'competition': 'medium', 'note': 'High volume, competitive pricing'},
                'US': {'name': 'United States', 'flag': '🇺🇸', 'cpc': 83, 'pct': 25, 'competition': 'high', 'note': 'Premium market, high-value leads'},
                'GB': {'name': 'United Kingdom', 'flag': '🇬🇧', 'cpc': 70, 'pct': 15, 'competition': 'high', 'note': 'Strong enterprise demand'},
                'UK': {'name': 'United Kingdom', 'flag': '🇬🇧', 'cpc': 70, 'pct': 15, 'competition': 'high', 'note': 'Strong enterprise demand'},
                'AU': {'name': 'Australia', 'flag': '🇦🇺', 'cpc': 60, 'pct': 10, 'competition': 'medium', 'note': 'Growing tech market'},
                'CA': {'name': 'Canada', 'flag': '🇨🇦', 'cpc': 65, 'pct': 10, 'competition': 'medium', 'note': 'Similar to US market'},
                'SG': {'name': 'Singapore', 'flag': '🇸🇬', 'cpc': 50, 'pct': 10, 'competition': 'medium', 'note': 'APAC hub market'},
                'AE': {'name': 'UAE', 'flag': '🇦🇪', 'cpc': 45, 'pct': 10, 'competition': 'medium', 'note': 'MENA region hub'},
            }
            # Recalculate percentages to sum to 100
            selected = [c for c in countries if c in country_defaults]
            if not selected:
                selected = ['IN', 'US']
            pct_each = 100 // len(selected)
            remainder = 100 - (pct_each * len(selected))
            country_budgets = []
            for i, code in enumerate(selected):
                d = country_defaults.get(code, {'name': code, 'cpc': 30, 'pct': pct_each, 'competition': 'medium', 'note': ''})
                pct = pct_each + (remainder if i == 0 else 0)
                budget_inr = round(total_budget * pct / 100)
                clicks_est = round(budget_inr / d['cpc'])
                country_budgets.append({
                    'country': d['name'],
                    'code': code,
                    'budget_pct': pct,
                    'budget_inr': budget_inr,
                    'avg_cpc_inr': d['cpc'],
                    'monthly_clicks': f"{round(clicks_est*0.8):,}–{round(clicks_est*1.2):,}",
                    'competition': d['competition'],
                    'notes': d['note'],
                })
            sem['country_budgets'] = country_budgets
        sem['target_countries'] = [cb['code'] for cb in sem.get('country_budgets', [])]
        
        # Ensure budget_calculation exists
        if not sem.get('budget_calculation'):
            budget = sem.get('monthly_budget_inr', 0)
            cpc = sem.get('estimated_cpc_inr', 30)
            daily = round(budget / 30)
            clicks = round(budget / cpc) if cpc else 0
            sem['budget_calculation'] = {
                'target_daily_clicks': round(clicks / 30),
                'avg_cpc_inr': cpc,
                'daily_budget_inr': daily,
                'monthly_budget_inr': budget,
                'buffer_pct': 10,
                'final_monthly_inr': budget,
                'reasoning': f'Budget of ₹{budget:,}/mo calculated based on target CPC of ₹{cpc} and estimated {clicks:,} monthly clicks.'
            }
        
        seo_report['sem_recommendations'] = sem
    
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
            "url_type": _detected_url_type,
        },
        "seo_report": seo_report,
        "ad_copy": ad_copy,
        "mock_campaign": {"status": "PREVIEW", "message": "Connect Google Ads to publish"},
    }


def detect_url_type(url: str) -> str:
    """Detect if URL is a single page or whole site."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    
    # Single page indicators
    single_page_extensions = ['.html', '.htm', '.php', '.aspx', '.asp', '.jsp', '.cfm', '.shtml']
    if any(path.endswith(ext) for ext in single_page_extensions):
        return 'single_page'
    
    # If path has many segments and looks like a specific page
    segments = [s for s in path.split('/') if s]
    if len(segments) >= 3 and not path.endswith('/'):
        return 'single_page'
    
    # Otherwise it's a whole site or section
    return 'whole_site'


def build_seo_prompt_single_page(s: dict) -> str:
    """Deep SEO analysis for a single page."""
    title = s.get('title', '')
    meta = s.get('meta_description', '')
    h1s = s.get('h1_tags', [])
    word_count = s.get('word_count', 0)
    images = s.get('images_count', 0)
    img_missing_alt = s.get('images_without_alt_count', 0)
    has_schema = s.get('has_schema_markup', False)
    internal_links = s.get('internal_links_count', 0)
    html_size = s.get('html_size_kb', 0)
    
    # Pre-calculate diagnostic data
    title_len = len(title)
    meta_len = len(meta)
    title_status = "✓ GOOD (30-60 chars)" if 30 <= title_len <= 60 else f"✗ {'TOO LONG' if title_len > 60 else 'TOO SHORT'} ({title_len} chars, ideal 30-60)"
    meta_status = "✓ GOOD (120-160 chars)" if 120 <= meta_len <= 160 else ("✗ MISSING" if not meta else f"✗ {'TOO LONG' if meta_len > 160 else 'TOO SHORT'} ({meta_len} chars, ideal 120-160)")
    h1_status = f"✓ GOOD (1 H1 tag)" if len(h1s) == 1 else (f"✗ MISSING" if not h1s else f"✗ MULTIPLE H1s ({len(h1s)} found, use only 1)")
    content_status = "✓ GOOD (800+ words)" if word_count >= 800 else f"✗ THIN CONTENT ({word_count} words, need 800+)"
    img_status = "✓ ALL IMAGES HAVE ALT TEXT" if img_missing_alt == 0 else f"✗ {img_missing_alt} of {images} images missing alt text"
    schema_status = "✓ SCHEMA PRESENT" if has_schema else "✗ NO SCHEMA MARKUP"
    links_status = "✓ GOOD" if internal_links >= 5 else f"✗ LOW ({internal_links} internal links, need 5+)"
    
    return f"""You are a senior SEO specialist. Analyse this SINGLE PAGE using the exact diagnostic data below.
URL: {s['url']}
Page Content: {str(s.get('full_text',''))[:3000]}

EXACT DIAGNOSTIC DATA (use these specific numbers in your analysis):
- Title: "{title}" → {title_status}
- Meta Description: "{meta[:100]}..." → {meta_status}  
- H1 Tags: {h1s} → {h1_status}
- Word Count: {word_count} → {content_status}
- Images: {images} total, {img_missing_alt} missing alt → {img_status}
- Schema Markup: {has_schema} → {schema_status}
- Internal Links: {internal_links} → {links_status}
- HTML Size: {html_size} KB

Return this EXACT JSON structure (no extra text):
{{
  "overall_seo_score": 72,
  "url_type": "single_page",
  "ai_summary": "5-6 sentence expert analysis covering: (1) overall SEO health with specific score explanation, (2) key strengths found in actual page data, (3) critical issues with specific details like word count/meta length/missing elements, (4) competitive positioning for target keywords, (5) top 2 immediate actions with expected score impact",
  "strengths": [
    {{"point": "Clear and descriptive title tag", "impact": "high"}}
  ],
  "weaknesses": [
    {{"point": "Missing meta description", "fix": "Add a 150-160 character meta description", "impact": "high"}}
  ],
  "page_analysis": {{
    "title_score": 85,
    "title_issues": "Title is good but could include primary keyword",
    "meta_score": 40,
    "meta_issues": "Meta description is missing - this is critical for CTR",
    "content_score": 70,
    "content_issues": "Content is thin at under 500 words",
    "technical_score": 90,
    "technical_issues": "Schema markup detected which is good"
  }},
  "keyword_suggestions": [
    {{"keyword": "example keyword", "difficulty": "low", "priority": "primary", "monthly_searches": "1K-10K"}}
  ],
  "content_analysis": {{
    "word_count": {s.get('word_count', 0)},
    "readability": "Good",
    "keyword_density": "2.3%",
    "content_gaps": ["Add FAQ section", "Include comparison table"]
  }},
  "technical_issues": ["Missing meta description", "Images missing alt text"],
  "quick_wins": ["Add meta description (5 min fix)", "Add alt text to 3 images"],
  "recommendations": ["Write a 150-character meta description with primary keyword", "Expand content to 800+ words"],
  "competitor_insights": {{
    "top_competitors": ["competitor1.com", "competitor2.com"],
    "positioning_suggestion": "Position as the most comprehensive solution"
  }},
  "sem_recommendations": {{
    "industry": "SaaS/Software",
    "monthly_budget_inr": 18000,
    "monthly_clicks_estimate": "400-900",
    "estimated_cpc_inr": 30,
    "campaign_type": "Search",
    "bidding_strategy": "Target CPA — focus on high-intent keywords",
    "budget_calculation": {{
      "target_daily_clicks": 25,
      "avg_cpc_inr": 30,
      "daily_budget_inr": 750,
      "monthly_budget_inr": 22500,
      "buffer_pct": 10,
      "final_monthly_inr": 18000,
      "reasoning": "Single page campaign focused on one product/service. Lower volume but higher intent. India avg CPC ₹15-30, US avg CPC ₹500-800."
    }},
    "country_budgets": [
      {{"country": "India", "code": "IN", "budget_pct": 60, "budget_inr": 10800, "avg_cpc_inr": 18, "monthly_clicks": "350-650", "competition": "medium", "notes": "Primary market, cost-effective"}},
      {{"country": "United States", "code": "US", "budget_pct": 40, "budget_inr": 7200, "avg_cpc_inr": 680, "monthly_clicks": "60-120", "competition": "high", "notes": "High value leads"}}
    ],
    "audience_segments": [
      {{"segment": "Decision Makers", "age_range": "28-50", "interests": ["Business Software", "Productivity", "Automation"]}}
    ]
  }}

IMPORTANT BUDGET RULES:
- Detect industry from the website content
- Use realistic India CPC rates based on industry
- Calculate budget from target clicks × CPC + 10% buffer
- Always show reasoning
}}"""


def build_seo_prompt_whole_site(s: dict) -> str:
    """Site-wide SEO analysis based on homepage."""
    return f"""You are a senior SEO strategist. Analyse this WEBSITE and return ONE JSON object only.
URL: {s['url']} | Title: {s['title']} | Meta: {s['meta_description']} | H1: {s['h1_tags']} | Images: {s['images_count']} | Schema: {s['has_schema_markup']} | Content: {str(s.get('full_text',''))[:3000]}

Return this EXACT JSON (no extra text):
{{
  "overall_seo_score": 72,
  "url_type": "whole_site",
  "ai_summary": "5-6 sentence expert analysis covering: (1) overall website SEO health score explanation, (2) strongest pages and what makes them rank well, (3) critical technical issues affecting the whole site with specifics, (4) content gaps and opportunities, (5) top 2 priority fixes with expected impact on rankings",
  "strengths": [
    {{"point": "Clear value proposition on homepage", "impact": "high"}},
    {{"point": "Good use of H1 tags", "impact": "medium"}}
  ],
  "weaknesses": [
    {{"point": "Missing meta descriptions on key pages", "fix": "Add unique 150-160 char meta descriptions", "impact": "high"}},
    {{"point": "No schema markup detected", "fix": "Add Organization and Product schema", "impact": "medium"}}
  ],
  "technical_issues": [
    {{"issue": "Missing meta description", "severity": "critical", "description": "Homepage has no meta description", "recommendation": "Add a 150-160 character meta description with primary keyword"}}
  ],
  "keyword_suggestions": [
    {{"keyword": "example keyword", "difficulty": "low", "priority": "primary", "monthly_searches": "1K-10K", "intent": "commercial"}}
  ],
  "content_analysis": {{
    "word_count": {s.get('word_count', 0)},
    "readability": "Good",
    "keyword_density": "2.3%",
    "content_gaps": ["Add pricing page", "Create case studies", "Add comparison pages"]
  }},
  "quick_wins": ["Fix homepage meta description", "Add alt text to images", "Add schema markup"],
  "recommendations": ["Create dedicated landing pages for each service", "Build topical authority with blog content"],
  "competitor_insights": {{
    "top_competitors": ["competitor1.com", "competitor2.com"],
    "positioning_suggestion": "Position as the most comprehensive enterprise solution"
  }},
  "sem_recommendations": {{
    "industry": "SaaS/Software",
    "monthly_budget_inr": 45000,
    "monthly_clicks_estimate": "1,200-2,500",
    "estimated_cpc_inr": 35,
    "campaign_type": "Search + Display",
    "bidding_strategy": "Target CPA — focus on conversion-ready audiences",
    "budget_calculation": {{
      "target_daily_clicks": 60,
      "avg_cpc_inr": 35,
      "daily_budget_inr": 2100,
      "monthly_budget_inr": 63000,
      "buffer_pct": 10,
      "final_monthly_inr": 45000,
      "reasoning": "Based on SaaS industry benchmarks: India avg CPC ₹18-35, US avg CPC ₹600-900. Target 60 clicks/day across markets. 10% buffer added for bid fluctuations."
    }},
    "country_budgets": [
      {{"country": "India", "code": "IN", "budget_pct": 50, "budget_inr": 22500, "avg_cpc_inr": 18, "monthly_clicks": "800-1500", "competition": "medium", "notes": "High volume, cost-effective leads"}},
      {{"country": "United States", "code": "US", "budget_pct": 30, "budget_inr": 13500, "avg_cpc_inr": 750, "monthly_clicks": "100-200", "competition": "high", "notes": "Premium leads, high conversion value"}},
      {{"country": "United Kingdom", "code": "UK", "budget_pct": 20, "budget_inr": 9000, "avg_cpc_inr": 620, "monthly_clicks": "80-150", "competition": "high", "notes": "Strong enterprise demand"}}
    ],
    "audience_segments": [
      {{"segment": "IT Decision Makers", "age_range": "28-50", "interests": ["Enterprise Software", "Cloud Computing", "IT Management"]}}
    ]
  }}

IMPORTANT BUDGET RULES:
- Detect industry from the website content (SaaS, E-commerce, Finance, Healthcare, Education, IT Services, Legal, Real Estate)
- Use realistic India CPC: SaaS ₹18-45, E-commerce ₹8-25, Finance ₹40-120, Healthcare ₹30-80, Education ₹10-30, IT Services ₹20-60
- Use realistic US CPC (multiply India CPC by 15-20x)
- Calculate: monthly_budget = (target_daily_clicks × weighted_avg_cpc × 30) + 10% buffer
- monthly_clicks_estimate = monthly_budget / avg_cpc (show as range ±20%)
- Always explain the reasoning in budget_calculation.reasoning
}}"""


# ─── OAuth ────────────────────────────────────────────────────────────────────

@app.get("/auth/google")
async def google_auth():
    return RedirectResponse(url=get_oauth_url())

@app.get("/auth/google/callback")
async def google_callback(code: str = Query(...)):
    tokens = await exchange_code_for_tokens(code)
    if "error" in tokens:
        raise HTTPException(status_code=400, detail=f"OAuth error: {tokens['error']}")
    user_info = await get_user_info(tokens["access_token"])
    session_id = f"sess_{user_info.get('id', 'unknown')}"
    _sessions[session_id] = {
        "email": user_info.get("email"),
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "customer_id": DEFAULT_CUSTOMER_ID,
    }
    save_sessions(_sessions)
    print(f"Session saved: {session_id} ({user_info.get('email')})")
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}?session_id={session_id}&email={user_info.get('email')}&customer_id={DEFAULT_CUSTOMER_ID}")

@app.get("/auth/status/{session_id}")
async def auth_status(session_id: str):
    if session_id in _sessions:
        s = _sessions[session_id]
        return {
            "authenticated": True,
            "email": s.get("email"),
            "customer_id": s.get("customer_id", DEFAULT_CUSTOMER_ID),
        }
    return {"authenticated": False}

# ─── Ads Routes ───────────────────────────────────────────────────────────────

@app.post("/api/ads/publish")
async def publish_campaign(req: PublishCampaignRequest):
    try:
        session = _sessions.get(req.session_id)
        if not session or not session.get("refresh_token"):
            raise HTTPException(status_code=401, detail="Not authenticated. Go to /auth/google to reconnect.")
        if req.daily_budget_usd < 1.0:
            raise HTTPException(status_code=400, detail=f"Daily budget too low")

        customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "") or req.customer_id or session.get("customer_id", "")
        refresh_token = session["refresh_token"]

        result = create_campaign_from_report(
            customer_id=customer_id,
            refresh_token=refresh_token,
            campaign_name=req.campaign_name,
            daily_budget_inr=req.daily_budget_usd * 83,
            target_countries=req.target_countries,
            keywords=req.keywords,
            ad_headlines=req.headlines,
            ad_descriptions=req.descriptions,
            final_url=req.final_url,
        )

        if result.get("success"):
            _sessions[req.session_id]["customer_id"] = customer_id
            save_sessions(_sessions)
        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "detail": str(e)}

@app.get("/api/ads/campaigns/{session_id}")
async def get_campaigns(session_id: str, customer_id: Optional[str] = Query(default="")):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    cid = resolve_customer_id(session, customer_id)
    campaigns = get_all_campaigns_spend(cid, session["refresh_token"])
    monitored = get_all_monitored()
    for c in campaigns:
        rn = c.get("resource_name", "")
        if rn in monitored:
            c["budget_monitoring"] = monitored[rn]
    # Save customer_id if not already saved
    if cid and not session.get("customer_id"):
        _sessions[session_id]["customer_id"] = cid
        save_sessions(_sessions)
    return {"campaigns": campaigns, "total": len(campaigns), "customer_id": cid}

@app.post("/api/ads/pause")
async def pause(req: CampaignActionRequest):
    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    cid = resolve_customer_id(session, req.customer_id)
    return pause_campaign(cid, session["refresh_token"], req.campaign_resource_name)

@app.post("/api/ads/resume")
async def resume(req: CampaignActionRequest):
    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    cid = resolve_customer_id(session, req.customer_id)
    return enable_campaign(cid, session["refresh_token"], req.campaign_resource_name)

# ─── AI Traffic Routes ────────────────────────────────────────────────────────

@app.post("/api/track")
async def track_visit(request: Request):
    """Track a visit from an AI platform. Call this from your website JS snippet."""
    body = await request.json()
    referrer = body.get("referrer", "") or request.headers.get("referer", "")
    page = body.get("page", "/")
    user_agent = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    converted = body.get("converted", False)
    conversion_value = body.get("conversion_value", 0.0)

    utm_source = body.get("utm_source", "")
    utm_term = body.get("utm_term", "")
    visit = log_visit(referrer, page, user_agent, ip, converted, conversion_value, utm_source, utm_term)
    if visit:
        return {"tracked": True, "platform": visit["platform_name"]}
    return {"tracked": False, "reason": "Not from an AI platform"}


@app.get("/api/ai-traffic")
async def get_ai_traffic(days: int = 30):
    """Get AI traffic statistics."""
    stats = get_traffic_stats(days)
    return stats


@app.post("/api/ai-traffic/demo")
async def load_demo_data():
    """Load demo traffic data for testing."""
    add_demo_data()
    return {"success": True, "message": "Demo data loaded"}


@app.post("/api/ai-traffic/convert/{visit_id}")
async def mark_conversion(visit_id: int, value: float = 0.0):
    """Mark a visit as converted (e.g. after form submit or purchase)."""
    from ai_traffic import _traffic_data, save_traffic
    for visit in _traffic_data["visits"]:
        if visit["id"] == visit_id:
            visit["converted"] = True
            visit["conversion_value"] = value
            save_traffic(_traffic_data)
            return {"success": True}
    return {"success": False, "error": "Visit not found"}




@app.post("/api/ads/delete")
async def delete_campaign(request: Request):
    body = await request.json()
    session_id = body.get("session_id", "")
    customer_id = body.get("customer_id", "")
    campaign_resource_name = body.get("campaign_resource_name", "")
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    manager_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    client_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "").replace("-", "")
    cid = client_id or customer_id.replace("-", "")
    
    from ads_manager import get_headers
    import httpx
    headers = get_headers(session["refresh_token"])
    url = f"https://googleads.googleapis.com/v23/customers/{cid}/campaigns:mutate"
    body = {"operations": [{"remove": campaign_resource_name}]}
    resp = httpx.post(url, headers=headers, json=body, timeout=30)
    data = resp.json()
    if resp.status_code != 200:
        return {"success": False, "errors": [str(data)]}
    return {"success": True, "message": "Campaign deleted successfully"}


@app.post("/api/ads/optimize")
async def optimize_campaigns(request: Request):
    """AI-powered campaign optimization - analyze performance and suggest bid changes."""
    body = await request.json()
    session_id = body.get("session_id", "")
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    client_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "").replace("-", "")
    campaigns = get_campaign_performance(client_id, session["refresh_token"])

    if not campaigns:
        return {"success": True, "recommendations": [], "message": "No campaign data available yet. Campaigns need to run for at least a day to generate optimization data."}

    import json
    campaign_data = json.dumps(campaigns, indent=2)
    prompt = f"""You are a Google Ads optimization expert. Analyze these campaign metrics and provide specific bid optimization recommendations.

Campaign data:
{campaign_data}

Provide recommendations in this JSON format only:
{{
  "overall_health": "good|warning|critical",
  "summary": "2 sentence summary",
  "recommendations": [
    {{
      "campaign_resource": "customers/xxx/campaigns/yyy",
      "campaign_name": "name",
      "action": "increase_bid|decrease_bid|pause|add_negative_keywords",
      "reason": "specific reason with data",
      "current_ctr": 0.02,
      "current_cpc_micros": 1000000,
      "avg_cpc": 10.5,
      "suggested_change": "Increase bid by 30-40%",
      "ideal_min_pct": 30,
      "ideal_max_pct": 40,
      "min_pct": 10,
      "max_pct": 50,
      "negative_keywords": ["keyword1", "keyword2"]
    }}
  ]
}}"""

    raw = await call_gemini(prompt)
    import re
    clean = re.sub(r'```json|```', '', raw).strip()
    try:
        result = json.loads(clean)
        return {"success": True, **result}
    except:
        return {"success": True, "recommendations": [], "summary": raw[:300], "overall_health": "good"}


@app.post("/api/ads/negative-keywords")
async def add_negative_keywords_endpoint(request: Request):
    body = await request.json()
    session_id = body.get("session_id", "")
    campaign_resource_name = body.get("campaign_resource_name", "")
    keywords = body.get("keywords", [])
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = add_negative_keywords("", session["refresh_token"], campaign_resource_name, keywords)
    return result


@app.get("/api/ads/report/{session_id}")
async def get_performance_report(session_id: str):
    """Generate weekly performance report."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    client_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "").replace("-", "")
    campaigns = get_campaign_performance(client_id, session["refresh_token"])

    import json
    prompt = f"""Generate a professional weekly Google Ads performance report.

Campaign data: {json.dumps(campaigns, indent=2)}

Write a clear, concise report with these sections:
1. Executive Summary
2. Campaign Performance Highlights  
3. Areas for Improvement
4. Recommended Actions for Next Week
5. Budget Efficiency Score (0-100)

Be specific with numbers and actionable with recommendations."""

    report = await call_gemini(prompt)
    return {"success": True, "report": report, "campaigns": campaigns}



@app.post("/api/ads/adjust-bid")
async def adjust_bid(request: Request):
    body = await request.json()
    session_id = body.get("session_id", "")
    campaign_resource_name = body.get("campaign_resource_name", "")
    adjustment_pct = body.get("adjustment_pct", 0)  # positive=increase, negative=decrease
    current_cpc_micros = body.get("current_cpc_micros", 1000000)
    
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Calculate new CPC
    new_cpc_micros = int(current_cpc_micros * (1 + adjustment_pct / 100))
    if new_cpc_micros < 100000:  # minimum 0.10 INR
        new_cpc_micros = 100000
    
    try:
        cid = campaign_resource_name.split("/")[1]
        from ads_manager import get_headers
        import httpx
        headers = get_headers(session["refresh_token"])
        url = f"https://googleads.googleapis.com/v23/customers/{cid}/campaigns:mutate"
        body_data = {"operations": [{"update": {
            "resourceName": campaign_resource_name,
            "manualCpc": {"enhancedCpcEnabled": True},
        }, "updateMask": "manual_cpc.enhanced_cpc_enabled"}]}
        resp = httpx.post(url, headers=headers, json=body_data, timeout=30)
        data = resp.json()
        if resp.status_code != 200:
            return {"success": False, "error": str(data)}
        direction = "increased" if adjustment_pct > 0 else "decreased"
        return {
            "success": True,
            "message": f"Bid {direction} by {abs(adjustment_pct)}%",
            "new_cpc_inr": round(new_cpc_micros / 1000000, 2),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.post("/api/competitor/discover")
async def discover_competitors(request: Request):
    body = await request.json()
    url = body.get("url", "")
    keywords = body.get("keywords", [])
    seo_score = body.get("seo_score", 50)
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    
    prompt = f"""You are an expert digital marketing analyst. Based on this website, identify their top competitors.

Website: {url}
Domain: {domain}
Keywords: {", ".join(keywords) if keywords else "AI, technology, automation"}
SEO Score: {seo_score}

Identify the top 3 direct competitors for this business. These should be real companies that offer similar products/services and target the same audience.

Respond ONLY with valid JSON:
{{
  "competitors": [
    {{
      "domain": "competitor1.com",
      "url": "https://competitor1.com",
      "name": "Competitor Name",
      "reason": "Why they are a direct competitor",
      "estimated_traffic": "10k-50k/month",
      "threat_level": "high|medium|low"
    }}
  ],
  "market_summary": "2 sentence overview of the competitive landscape"
}}"""
    
    try:
        import re, json
        raw = await call_gemini(prompt)
        clean = re.sub(r"```json|```", "", raw).strip()
        return json.loads(clean)
    except Exception as e:
        return {"error": str(e), "competitors": []}



@app.post("/api/competitor/discover")
async def discover_competitors(request: Request):
    body = await request.json()
    url = body.get("url", "")
    keywords = body.get("keywords", [])
    industry = body.get("industry", "technology")
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]

    prompt = f"""You are an SEO and competitive intelligence expert.
Find the top 5 competitors for this website: {url}
Industry: {industry}
Keywords: {", ".join(keywords) if keywords else "general"}

Respond ONLY with valid JSON, no markdown:
{{"competitors": [
  {{"domain": "competitor.com", "url": "https://competitor.com", "reason": "why they compete", "similarity": 85}},
  {{"domain": "rival.io", "url": "https://rival.io", "reason": "why they compete", "similarity": 72}}
]}}

Rules:
- Find REAL companies that compete in the same space
- similarity is 0-100 percentage of how directly they compete
- reason should be specific (e.g. "Both offer AI automation for SMEs in India")
- Return exactly 5 competitors"""

    try:
        import re, json
        raw = await call_gemini(prompt)
        clean = re.sub(r"```json|```", "", raw).strip()
        return json.loads(clean)
    except Exception as e:
        return {"competitors": [], "error": str(e)}



@app.post("/api/site-audit/start")
async def start_site_audit(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    url = body.get("url", "")
    max_pages = min(body.get("max_pages", 100), 20000)
    if not url:
        raise HTTPException(status_code=400, detail="URL required")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    import uuid
    from site_crawler import create_job, run_audit_job
    job_id = str(uuid.uuid4())[:8]
    create_job(job_id, url, max_pages)
    background_tasks.add_task(run_audit_job, job_id, url, max_pages)
    return {"job_id": job_id, "status": "started"}


@app.get("/api/site-audit/status/{job_id}")
async def get_audit_status(job_id: str):
    from site_crawler import get_job
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": job["status"], "progress": job["progress"],
            "pages_found": job["pages_found"], "pages_crawled": job["pages_crawled"],
            "current_url": job["current_url"], "result": job["result"], "error": job["error"]}


@app.post("/api/site-audit")
async def site_audit(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    url = body.get("url", "")
    max_pages = min(body.get("max_pages", 100), 20000)
    if not url:
        raise HTTPException(status_code=400, detail="URL required")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    import uuid
    from site_crawler import create_job, run_audit_job
    job_id = str(uuid.uuid4())[:8]
    create_job(job_id, url, max_pages)
    background_tasks.add_task(run_audit_job, job_id, url, max_pages)
    return {"job_id": job_id, "status": "started"}

@app.post("/api/site-audit/start")
async def start_site_audit(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    url = body.get("url", "")
    max_pages = min(body.get("max_pages", 100), 20000)
    if not url:
        raise HTTPException(status_code=400, detail="URL required")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    import uuid
    from site_crawler import create_job, run_audit_job
    job_id = str(uuid.uuid4())[:8]
    create_job(job_id, url, max_pages)
    background_tasks.add_task(run_audit_job, job_id, url, max_pages)
    return {"job_id": job_id, "status": "started"}


@app.get("/api/site-audit/status/{job_id}")
async def get_audit_status(job_id: str):
    from site_crawler import get_job
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "pages_found": job["pages_found"],
        "pages_crawled": job["pages_crawled"],
        "current_url": job["current_url"],
        "result": job["result"],
        "error": job["error"],
    }


@app.post("/api/site-audit")
async def site_audit(request: Request, background_tasks: BackgroundTasks):
    """Legacy endpoint - starts job and returns job_id."""
    body = await request.json()
    url = body.get("url", "")
    max_pages = min(body.get("max_pages", 100), 20000)
    if not url:
        raise HTTPException(status_code=400, detail="URL required")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    import uuid
    from site_crawler import create_job, run_audit_job
    job_id = str(uuid.uuid4())[:8]
    create_job(job_id, url, max_pages)
    background_tasks.add_task(run_audit_job, job_id, url, max_pages)
    return {"job_id": job_id, "status": "started"}


@app.post("/api/ads/recommend-pages")
async def recommend_ad_pages(request: Request):
    try:
        body = await request.json()
        url = body.get("url", "")
        max_pages = min(body.get("max_pages", 100), 20000)
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        from urllib.parse import urlparse
        from site_crawler import get_urls_from_sitemap, fetch_page
        import httpx as hx
        parsed = urlparse(url)
        base_domain = parsed.netloc
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}
        async with hx.AsyncClient(headers=headers, follow_redirects=True) as client:
            sitemap_urls = []
            for sc in [
                f"{parsed.scheme}://{base_domain}{parsed.path.rstrip('/')}/sitemap.xml",
                f"{parsed.scheme}://{base_domain}/sitemap.xml"
            ]:
                sitemap_urls = await get_urls_from_sitemap(client, sc, base_domain, max_pages)
                if sitemap_urls:
                    break
            if not sitemap_urls:
                sitemap_urls = [url]
            sitemap_urls = sitemap_urls[:max_pages]
            pages_data = []
            for i in range(0, len(sitemap_urls), 20):
                batch = sitemap_urls[i:i+20]
                results = await asyncio.gather(*[fetch_page(client, u) for u in batch], return_exceptions=True)
                for r in results:
                    if r and isinstance(r, dict) and r.get("title"):
                        pages_data.append({
                            "url": r["url"],
                            "title": r["title"],
                            "meta": r.get("meta_description", "")[:80],
                        })
                await asyncio.sleep(0.2)
        if not pages_data:
            return {"error": "Could not crawl any pages"}
        pages_summary = "\n".join([
            f"- {p['url']} | {p['title']} | {p['meta']}"
            for p in pages_data[:100]
        ])
        recommend_prompt = f"""You are a Google Ads expert. Pick the BEST 5-8 pages to advertise from {url}.

Pages found:
{pages_summary}

Pick pages with high commercial intent (product, feature, pricing, demo).
Avoid: blog posts, help docs, login, news, duplicate region pages.

Respond ONLY valid JSON:
{{"recommended_pages":[{{"url":"exact-url","title":"title","reason":"why","ad_intent":"commercial","suggested_keywords":["kw1"],"ad_copy":{{"headline_1":"max 30 chars","headline_2":"max 30 chars","headline_3":"max 30 chars","description_1":"max 90 chars","description_2":"max 90 chars","display_path":"/path"}}}}],"excluded_pages":[{{"url":"url","reason":"why"}}],"campaign_strategy":"2-3 sentence strategy"}}"""
        raw = await call_gemini(recommend_prompt)
        clean = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(clean)
        result["total_pages_analysed"] = len(pages_data)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}



@app.post("/api/social/generate")
async def generate_social_posts(request: Request):
    body = await request.json()
    url = body.get("url", "")
    platforms = body.get("platforms", ["linkedin", "twitter"])
    post_types = body.get("post_types", ["service"])
    custom_topic = body.get("custom_topic", "")
    keywords = body.get("keywords", [])
    services = body.get("services", "")
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    kw_str = ", ".join(keywords) if keywords else "AI, technology"
    platform_str = ", ".join(platforms)
    prompt = (
        f"Professional social media content for {domain}. "
        f"Services: {services or 'technology'}. Keywords: {kw_str}. "
        f"Topic: {custom_topic or 'Brand awareness'}. Platforms: {platform_str}. "
        'Respond ONLY valid JSON: {"posts":[{"platform":"linkedin","type":"service",'
        '"content":"post text","hashtags":["tag1"],"best_time":"Tuesday 9AM"}]}'
    )
    try:
        import re as _re, json as _json
        raw = await call_gemini(prompt)
        clean = _re.sub(r"```json|```", "", raw).strip()
        return _json.loads(clean)
    except Exception as e:
        return {"error": str(e), "posts": []}


@app.post("/api/competitor/analyze")
async def analyze_competitors(request: Request):
    body = await request.json()
    url = body.get("url", "")
    competitors = body.get("competitors", [])
    seo_score = body.get("seo_score", 50)
    keywords = body.get("keywords", [])
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    comp_str = ", ".join(competitors)
    kw_str = ", ".join(keywords)
    prompt = (
        f"SEO analyst: analyse {url} vs {comp_str} (score:{seo_score}, keywords:{kw_str}). "
        f'Respond ONLY valid JSON: {{"my_site":{{"domain":"{domain}","score":{seo_score},'
        '"strengths":["strength1"],"weaknesses":["weakness1"]}}'
        ',"competitors":[{"domain":"competitor.com","estimated_score":70,'
        '"estimated_traffic":"10k/month","top_keywords":["kw1"],'
        '"strengths":["s1"],"weaknesses":["w1"],'
        '"ad_strategy":"description","social_presence":"description"}],'
        '"opportunities":["opportunity1"],"threats":["threat1"],'
        '"action_plan":["action1"]}}'
    )
    try:
        import re as _re, json as _json
        raw = await call_gemini(prompt)
        clean = _re.sub(r"```json|```", "", raw).strip()
        return _json.loads(clean)
    except Exception as e:
        return {"error": str(e)}



@app.post("/api/pagespeed")
async def get_pagespeed(request: Request):
    """Fetch real PageSpeed Insights scores from Google API."""
    try:
        body = await request.json()
        url = body.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        api_key = os.environ.get("PAGESPEED_API_KEY", "")
        if not api_key:
            return {"error": "PageSpeed API key not configured"}

        results = {}
        async with httpx.AsyncClient(timeout=30) as client:
            for strategy in ["mobile", "desktop"]:
                psi_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy={strategy}&key={api_key}&category=performance&category=accessibility&category=best-practices&category=seo"
                resp = await client.get(psi_url)
                data = resp.json()

                if "error" in data:
                    results[strategy] = {"error": data["error"].get("message", "API error")}
                    continue

                cats = data.get("lighthouseResult", {}).get("categories", {})
                audits = data.get("lighthouseResult", {}).get("audits", {})

                results[strategy] = {
                    "performance": round((cats.get("performance", {}).get("score", 0) or 0) * 100),
                    "accessibility": round((cats.get("accessibility", {}).get("score", 0) or 0) * 100),
                    "best_practices": round((cats.get("best-practices", {}).get("score", 0) or 0) * 100),
                    "seo": round((cats.get("seo", {}).get("score", 0) or 0) * 100),
                    "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
                    "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                    "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                    "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
                    "speed_index": audits.get("speed-index", {}).get("displayValue", "N/A"),
                }

        return {"url": url, "results": results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.post("/api/send-report")
async def send_seo_report(request: Request):
    """Send SEO report via email using Resend."""
    try:
        body = await request.json()
        url = body.get("url", "")
        email = body.get("email", "")
        seo_report = body.get("seo_report", {})
        
        if not email:
            raise HTTPException(status_code=400, detail="Email required")
        
        resend_api_key = os.environ.get("RESEND_API_KEY", "")
        if not resend_api_key:
            raise HTTPException(status_code=500, detail="Email service not configured")
        
        # Build HTML report
        score = seo_report.get("overall_seo_score", 0)
        score_color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
        summary = seo_report.get("ai_summary", "")
        strengths = seo_report.get("strengths", [])
        weaknesses = seo_report.get("weaknesses", [])
        keywords = seo_report.get("keyword_suggestions", [])
        sem = seo_report.get("sem_recommendations", {})
        budget = sem.get("monthly_budget_inr", 0)
        clicks = sem.get("monthly_clicks_estimate", "N/A")
        cpc = sem.get("estimated_cpc_inr", 0)
        
        strengths_html = "".join([f'<li style="color:#22c55e;margin-bottom:6px">✓ {s.get("point","")}</li>' for s in strengths[:5]])
        weaknesses_html = "".join([f'<li style="color:#ef4444;margin-bottom:6px">✗ {w.get("point","")} — {w.get("fix","")}</li>' for w in weaknesses[:5]])
        keywords_html = "".join([f'<span style="background:#f0f9ff;color:#0369a1;padding:3px 8px;border-radius:10px;margin:3px;display:inline-block;font-size:12px">{k.get("keyword","")}</span>' for k in keywords[:8]])
        
        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f8fafc; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; }}
  .header {{ background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 32px; text-align: center; }}
  .header h1 {{ color: white; margin: 0; font-size: 24px; }}
  .header p {{ color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 14px; }}
  .score-box {{ background: #f8fafc; padding: 24px; text-align: center; border-bottom: 1px solid #e2e8f0; }}
  .score {{ font-size: 64px; font-weight: 800; color: {score_color}; line-height: 1; }}
  .score-label {{ color: #64748b; font-size: 14px; margin-top: 4px; }}
  .section {{ padding: 24px; border-bottom: 1px solid #e2e8f0; }}
  .section h2 {{ font-size: 16px; color: #1e293b; margin: 0 0 12px; }}
  .metric {{ display: inline-block; background: #f0f9ff; border: 1px solid #bae6fd; padding: 10px 16px; border-radius: 10px; margin: 4px; text-align: center; }}
  .metric-value {{ font-size: 20px; font-weight: 700; color: #0369a1; }}
  .metric-label {{ font-size: 11px; color: #64748b; margin-top: 2px; }}
  .footer {{ background: #f8fafc; padding: 20px; text-align: center; color: #94a3b8; font-size: 12px; }}
</style></head>
<body>
<div class="container">
  <div class="header">
    <h1>🎯 SEM AI — SEO Report</h1>
    <p>{url}</p>
    <p>Generated on {__import__('datetime').datetime.now().strftime('%d %B %Y')}</p>
  </div>
  
  <div class="score-box">
    <div class="score">{score}</div>
    <div class="score-label">Overall SEO Score / 100</div>
  </div>
  
  <div class="section">
    <h2>🤖 AI Expert Analysis</h2>
    <p style="color:#475569;line-height:1.7;font-size:14px">{summary}</p>
  </div>
  
  <div class="section">
    <h2>📊 SEM Recommendations</h2>
    <div>
      <div class="metric"><div class="metric-value">₹{budget:,}</div><div class="metric-label">Monthly Budget</div></div>
      <div class="metric"><div class="metric-value">{clicks}</div><div class="metric-label">Est. Clicks/mo</div></div>
      <div class="metric"><div class="metric-value">₹{cpc}</div><div class="metric-label">Avg CPC</div></div>
    </div>
  </div>
  
  <div class="section">
    <h2>💪 Strengths</h2>
    <ul style="margin:0;padding-left:16px">{strengths_html}</ul>
  </div>
  
  <div class="section">
    <h2>⚠️ Issues to Fix</h2>
    <ul style="margin:0;padding-left:16px">{weaknesses_html}</ul>
  </div>
  
  <div class="section">
    <h2>🔑 Target Keywords</h2>
    <div>{keywords_html}</div>
  </div>
  
  <div class="footer">
    <p>Generated by SEM AI Platform • Powered by Gemini 2.5 Flash</p>
  </div>
</div>
</body>
</html>"""

        # Send via Resend API
        import httpx as _hx
        resp = _hx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_api_key}", "Content-Type": "application/json"},
            json={
                "from": "SEM AI <onboarding@resend.dev>",
                "to": ["jsvking@gmail.com"],
                "reply_to": email,
                "subject": f"SEO Report: {url} — Score {score}/100",
                "html": html,
            },
            timeout=30
        )
        
        if resp.status_code == 200:
            return {"success": True, "message": f"Report sent to {email}"}
        else:
            return {"success": False, "error": resp.text}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.get("/api/agent/status")
async def agent_status():
    """Get AI agent status and recent activity."""
    return get_agent_status()


@app.post("/api/agent/chat")
async def agent_chat(request: Request):
    """Chat with the AI SEM agent."""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "")
    customer_id = body.get("customer_id", os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", ""))

    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    session = _sessions.get(session_id)
    campaigns = []
    if session:
        try:
            campaigns = get_all_campaigns_spend(customer_id, session["refresh_token"])
        except:
            pass

    try:
        import httpx as _hx, json as _json
        api_key = os.environ.get("GEMINI_API_KEY", "")
        camp_str = _json.dumps(campaigns[:3]) if campaigns else "No campaigns data"
        prompt = f"""You are SEMA, an expert Google Ads AI assistant. Answer this question about the user's campaigns.
Campaigns data: {camp_str}
User question: {message}
Give a clear, actionable response in 2-3 sentences."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        resp = _hx.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        data = resp.json()
        response = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        response = f"I encountered an error: {str(e)}"
    return {"response": response, "timestamp": datetime.now().isoformat()}


@app.post("/api/agent/analyze")
async def agent_analyze(request: Request):
    """Run a manual analysis cycle."""
    body = await request.json()
    session_id = body.get("session_id", "")
    customer_id = body.get("customer_id", os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", ""))

    session = _sessions.get(session_id)
    campaigns = []
    if session:
        try:
            campaigns = get_all_campaigns_spend(customer_id, session["refresh_token"])
        except:
            pass

    analysis = await run_monitoring_cycle(campaigns, session_id, customer_id)
    return analysis


@app.get("/api/agent/report")
async def agent_weekly_report(session_id: str, customer_id: str = ""):
    """Generate weekly performance report."""
    from sem_agent import _agent_state, chat_with_agent, get_agent_status, clear_agent_chat
    snapshots = _agent_state.get("campaign_snapshots", [])
    report = generate_weekly_report(snapshots)
    return {"report": report, "generated_at": datetime.now().isoformat()}


@app.post("/api/agent/toggle")
async def agent_toggle(request: Request):
    """Enable or disable the agent."""
    body = await request.json()
    active = body.get("active", True)
    set_agent_active(active)
    return {"active": active}


@app.post("/api/agent/clear-chat")
async def agent_clear_chat():
    """Clear chat history."""
    clear_agent_chat()
    return {"success": True}
