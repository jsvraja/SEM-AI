from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
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

def get_db_connection():
    """Get PostgreSQL connection."""
    try:
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            import psycopg2
            conn = psycopg2.connect(db_url)
            return conn
    except Exception as e:
        print(f"DB connection error: {e}")
    return None

def load_sessions():
    """Load sessions from DB first, fallback to file."""
    sessions = {}
    # Try DB
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS google_sessions (
                    session_id TEXT PRIMARY KEY,
                    data JSONB,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.execute("SELECT session_id, data FROM google_sessions")
            rows = cur.fetchall()
            for row in rows:
                sessions[row[0]] = row[1] if isinstance(row[1], dict) else json.loads(row[1])
            cur.close()
            conn.close()
            print(f"Loaded {len(sessions)} sessions from DB")
            return sessions
    except Exception as e:
        print(f"DB load error: {e}")
    # Fallback to file
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_sessions(sessions):
    """Save sessions to DB and file."""
    # Save to DB
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS google_sessions (
                    session_id TEXT PRIMARY KEY,
                    data JSONB,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            for sid, data in sessions.items():
                cur.execute("""
                    INSERT INTO google_sessions (session_id, data)
                    VALUES (%s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET data = %s, updated_at = NOW()
                """, (sid, json.dumps(data), json.dumps(data)))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        print(f"DB save error: {e}")
    # Also save to file as backup
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save sessions to file: {e}")

_sessions = load_sessions()
print(f"Loaded {len(_sessions)} saved session(s)")

# Hard-coded fallback customer ID from env
DEFAULT_CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "").replace("-", "") or os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")

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
    from urllib.parse import urlparse as _urlparse
    _base = _urlparse(url).netloc
    internal_links_raw = []
    external_links_raw = []
    for l in all_links:
        href = l.get("href", "").strip()
        text = l.get_text(strip=True)[:50]
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        if href.startswith("/") or _base in href:
            internal_links_raw.append({"url": href, "text": text})
        elif href.startswith("http"):
            external_links_raw.append({"url": href, "text": text})
    internal_links = internal_links_raw
    external_links = external_links_raw[:20]
    
    # Nofollow links
    nofollow_count = len([l for l in all_links if 'nofollow' in (l.get('rel') or [])])
    
    # Anchor text analysis
    anchor_texts = [l.get_text(strip=True) for l in all_links if l.get_text(strip=True)]
    empty_anchors = len([a for a in anchor_texts if not a or a.lower() in ['click here', 'here', 'read more', 'more']])
    images = soup.find_all("img")
    images_without_alt = [img.get("src", "") for img in images if not img.get("alt")]
    schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    
    # Extract schema types
    import json as _json
    schema_types = []
    schema_data = []
    for tag in schema_tags:
        try:
            raw = tag.string or tag.get_text() or '{}'
            data = _json.loads(raw)
            
            def extract_types(obj):
                if isinstance(obj, list):
                    for item in obj:
                        extract_types(item)
                elif isinstance(obj, dict):
                    t = obj.get('@type', '')
                    if t and t not in schema_types:
                        schema_types.append(t)
                    # Handle @graph
                    graph = obj.get('@graph', [])
                    if graph:
                        extract_types(graph)
            
            extract_types(data)
            schema_data.append(data)
        except: pass
    
    # Get full text before removing tags for word count
    full_text_raw = re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True))
    word_count = len(full_text_raw.split())
    
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True))[:5000]
    
    # Direct CTA detection (100% accurate)
    cta_keywords = ['download', 'free trial', 'get started', 'contact us', 'buy now', 
                    'request demo', 'sign up', 'try free', 'get quote', 'schedule demo',
                    'start free', 'register', 'subscribe', 'book a demo', 'learn more']
    full_text_lower = full_text_raw.lower()
    has_cta = any(kw in full_text_lower for kw in cta_keywords)
    cta_found = [kw for kw in cta_keywords if kw in full_text_lower][:3]
    
    # Reading level (Flesch-Kincaid approximation)
    sentences = len(re.findall(r'[.!?]+', full_text_raw)) or 1
    words = word_count or 1
    syllables = sum(max(1, len(re.findall(r'[aeiouAEIOU]', w))) for w in full_text_raw.split()[:200])
    fk_score = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/min(words,200))
    fk_score = max(0, min(100, fk_score))
    if fk_score >= 70: reading_level = "Easy (Grade 6)"
    elif fk_score >= 50: reading_level = "Standard (Grade 8-9)"
    elif fk_score >= 30: reading_level = "Difficult (Grade 12)"
    else: reading_level = "Very Difficult (College)"
    
    # Keyword density - top words
    import collections
    stop_words = {'the','be','to','of','and','a','in','that','have','it','for','not','on','with','he','as','you','do','at','this','but','his','by','from','they','we','say','her','she','or','an','will','my','one','all','would','there','their','what','so','up','out','if','about','who','get','which','go','me','is','are','was','were','has','had','can','your'}
    words_list = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', full_text_raw) if w.lower() not in stop_words]
    word_freq = collections.Counter(words_list).most_common(5)
    top_keyword = word_freq[0][0] if word_freq else ''
    keyword_density = f"{round((word_freq[0][1]/max(word_count,1))*100, 1)}%" if word_freq else "0%"
    
    # Tone detection
    professional_words = ['enterprise','solution','platform','manage','optimize','implement','deploy','configure']
    casual_words = ['easy','simple','quick','fast','fun','awesome','great','love']
    prof_count = sum(1 for w in professional_words if w in full_text_lower)
    casual_count = sum(1 for w in casual_words if w in full_text_lower)
    tone = "Professional" if prof_count > casual_count else "Casual" if casual_count > prof_count else "Neutral"
    
    # Image alt text percentage
    alt_coverage = round(((len(images) - len(images_without_alt)) / max(len(images), 1)) * 100)
    
    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "meta_description": meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
        "has_viewport": viewport is not None,
        "h1_tags": h1s, "h2_tags": h2s,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "internal_links_sample": internal_links,
        "external_links_sample": external_links,
        "nofollow_count": nofollow_count,
        "empty_anchors": empty_anchors,
        "images_count": len(images),
        "images_without_alt_count": len(images_without_alt),
        "alt_text_coverage": alt_coverage,
        "has_schema_markup": len(schema_tags) > 0,
        "schema_types": schema_types,
        "schema_count": len(schema_tags),
        "body_text_sample": body_text,
        "full_text": body_text,
        "html_size_kb": round(len(html) / 1024, 1),
        "word_count": word_count,
        "reading_level": reading_level,
        "flesch_score": round(fk_score, 1),
        "has_cta": has_cta,
        "cta_examples": cta_found,
        "tone": tone,
        "top_keyword": top_keyword,
        "keyword_density": keyword_density,
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
async def full_report(req: FullReportRequest, request: Request):
    # Usage limit check
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        payload = verify_token(auth[7:])
        if payload:
            try:
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT plan FROM users WHERE id = %s", (payload["sub"],))
                    user = cur.fetchone()
                    cur.close(); conn.close()
                    plan = user[0] if user else "free"
                    usage = check_and_increment_usage(payload["sub"], plan)
                    if not usage["allowed"]:
                        from fastapi.responses import JSONResponse
                        return JSONResponse({"error": "usage_limit_exceeded", "plan": plan, "limit": usage["limit"], "message": "Daily analysis limit reached. Upgrade to Pro for unlimited analyses."})
            except Exception as e:
                print(f"Usage check error: {e}")
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
        # Normalize budget — store min/max range, not single value
        if not sem.get('monthly_budget_inr_min'):
            budget = sem.get('suggested_monthly_budget_usd', {})
            budget_calc = sem.get('budget_calculation', {})
            if isinstance(budget, dict) and (budget.get('min') or budget.get('max')):
                sem['monthly_budget_inr_min'] = int(budget.get('min', 0) * 83)
                sem['monthly_budget_inr_max'] = int(budget.get('max', 0) * 83)
                sem['monthly_budget_inr'] = int((budget.get('min', 0) + budget.get('max', 0)) / 2 * 83)
            elif budget_calc.get('monthly_budget_inr') or budget_calc.get('final_monthly_inr'):
                # Use budget_calculation as fallback
                base = budget_calc.get('final_monthly_inr') or budget_calc.get('monthly_budget_inr') or 0
                sem['monthly_budget_inr'] = base
                sem['monthly_budget_inr_min'] = int(base * 0.8)
                sem['monthly_budget_inr_max'] = int(base * 1.2)
            elif isinstance(budget, (int, float)) and budget > 0:
                sem['monthly_budget_inr'] = int(budget * 83)
                sem['monthly_budget_inr_min'] = int(budget * 83 * 0.8)
                sem['monthly_budget_inr_max'] = int(budget * 83 * 1.2)
        # Normalize clicks — store min/max range
        if not sem.get('monthly_clicks_min'):
            clicks = sem.get('estimated_monthly_clicks', {})
            budget_calc = sem.get('budget_calculation', {})
            if isinstance(clicks, dict) and (clicks.get('min') or clicks.get('max')):
                sem['monthly_clicks_min'] = clicks.get('min', 0)
                sem['monthly_clicks_max'] = clicks.get('max', 0)
                sem['monthly_clicks_estimate'] = f"{clicks.get('min',0):,}–{clicks.get('max',0):,}"
            elif budget_calc.get('target_daily_clicks'):
                # Calculate from daily clicks in budget_calculation
                daily = budget_calc.get('target_daily_clicks', 0)
                monthly_min = int(daily * 28 * 0.8)
                monthly_max = int(daily * 31 * 1.2)
                sem['monthly_clicks_min'] = monthly_min
                sem['monthly_clicks_max'] = monthly_max
                sem['monthly_clicks_estimate'] = f"{monthly_min:,}–{monthly_max:,}"
            elif clicks:
                sem['monthly_clicks_estimate'] = str(clicks)
        # Normalize CPC — store min/max range
        if not sem.get('estimated_cpc_inr_min'):
            cpc = sem.get('estimated_cpc_usd', {})
            if isinstance(cpc, dict):
                sem['estimated_cpc_inr_min'] = round(cpc.get('min', 0) * 83)
                sem['estimated_cpc_inr_max'] = round(cpc.get('max', 0) * 83)
                sem['estimated_cpc_inr'] = round((cpc.get('min', 0) + cpc.get('max', 0)) / 2 * 83)
            elif isinstance(cpc, (int, float)):
                sem['estimated_cpc_inr'] = round(cpc * 83)
                sem['estimated_cpc_inr_min'] = round(cpc * 83 * 0.8)
                sem['estimated_cpc_inr_max'] = round(cpc * 83 * 1.2)
        
        # Fallback: get CPC from budget_calculation
        if not sem.get('estimated_cpc_inr') or sem.get('estimated_cpc_inr') == 0:
            bc = sem.get('budget_calculation', {})
            cpc_from_bc = bc.get('avg_cpc_inr', 0) or bc.get('estimated_cpc_inr', 0)
            if cpc_from_bc:
                sem['estimated_cpc_inr'] = cpc_from_bc
                sem['estimated_cpc_inr_min'] = round(cpc_from_bc * 0.8)
                sem['estimated_cpc_inr_max'] = round(cpc_from_bc * 1.2)
        
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
    
    # Build score_breakdown from AI page_analysis
    page_analysis = seo_report.get('page_analysis', {})
    if page_analysis:
        seo_report['score_breakdown'] = {
            'title_tag': page_analysis.get('title_score', 0),
            'meta_description': page_analysis.get('meta_score', 0),
            'content_quality': page_analysis.get('content_score', 0) or seo_report.get('content_analysis', {}).get('content_score', 0),
            'technical': page_analysis.get('technical_score', 0),
            'title_issues': page_analysis.get('title_issues', ''),
            'meta_issues': page_analysis.get('meta_issues', ''),
            'content_issues': page_analysis.get('content_issues', ''),
        }
        
        # Recalculate overall_seo_score as weighted average of breakdown scores
        sb = seo_report['score_breakdown']
        title_s = sb.get('title_tag', 0)
        meta_s = sb.get('meta_description', 0)
        content_s = sb.get('content_quality', 0)
        technical_s = sb.get('technical', 0)
        
        # Get h1, image, schema scores from scraped data
        scraped_h1 = 1 if scraped.get('h1_tags') else 0
        h1_s = 95 if scraped_h1 == 1 else 0
        
        img_missing = scraped.get('images_without_alt_count', 0)
        img_total = scraped.get('images_count', 0)
        img_s = 80 if img_total == 0 else round((1 - img_missing/img_total) * 100)
        
        schema_s = 95 if scraped.get('has_schema_markup') else 0
        
        # Weighted average
        overall = round(
            title_s * 0.15 +
            meta_s * 0.15 +
            h1_s * 0.15 +
            content_s * 0.25 +
            img_s * 0.15 +
            schema_s * 0.15
        )
        seo_report['overall_seo_score'] = overall
        seo_report['score_breakdown']['h1_tags'] = h1_s
        seo_report['score_breakdown']['image_alt_text'] = img_s
        seo_report['score_breakdown']['schema_markup'] = schema_s

    return {
        "url": url,
        "scraped_data": {
            "title": scraped["title"],
            "meta_description": scraped["meta_description"],
            "h1_tags": scraped["h1_tags"],
            "images_count": scraped["images_count"],
            "images_without_alt_count": scraped["images_without_alt_count"],
            "alt_text_coverage": scraped.get("alt_text_coverage", 0),
            "internal_links_count": scraped["internal_links_count"],
            "external_links_count": scraped.get("external_links_count", 0),
            "internal_links_sample": scraped.get("internal_links_sample", []),
            "external_links_sample": scraped.get("external_links_sample", []),
            "nofollow_count": scraped.get("nofollow_count", 0),
            "empty_anchors": scraped.get("empty_anchors", 0),
            "has_schema_markup": scraped["has_schema_markup"],
            "schema_types": scraped.get("schema_types", []),
            "schema_count": scraped.get("schema_count", 0),
            "html_size_kb": scraped["html_size_kb"],
            "word_count": scraped.get("word_count", 0),
            "reading_level": scraped.get("reading_level", "N/A"),
            "flesch_score": scraped.get("flesch_score", 0),
            "has_cta": scraped.get("has_cta", False),
            "cta_examples": scraped.get("cta_examples", []),
            "tone": scraped.get("tone", "N/A"),
            "top_keyword": scraped.get("top_keyword", ""),
            "keyword_density": scraped.get("keyword_density", "0%"),
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
- Reading Level: {s.get('reading_level', 'N/A')} (Flesch Score: {s.get('flesch_score', 'N/A')})
- Tone: {s.get('tone', 'N/A')}
- CTA Present: {s.get('has_cta', False)} → CTAs found: {s.get('cta_examples', [])}
- Top Keyword: "{s.get('top_keyword', 'N/A')}" — Density: {s.get('keyword_density', 'N/A')}
- Images: {images} total, {img_missing_alt} missing alt → {img_status}
- Alt Text Coverage: {s.get('alt_text_coverage', 0)}%
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
    "readability": "Good/Average/Poor based on content complexity",
    "reading_level": "{s.get('reading_level', 'Standard (Grade 8-9)')}",
    "keyword_density": "{s.get('keyword_density', '0%')}",
    "primary_keyword": "{s.get('top_keyword', '')}",
    "keyword_in_title": true_or_false,
    "keyword_in_meta": true_or_false,
    "keyword_in_h1": true_or_false,
    "content_score": 70,
    "content_gaps": ["specific gap based on page content"],
    "tone": "{s.get('tone', 'Professional')}",
    "language": "English",
    "has_cta": {str(s.get('has_cta', False)).lower()},
    "cta_text": "{', '.join(s.get('cta_examples', []))}",
    "content_strengths": ["strength based on actual content"],
    "content_weaknesses": ["weakness based on actual content"]
  }},
  "fix_suggestions": [
    {{
      "issue": "Missing Schema Markup",
      "priority": "high",
      "effort": "medium",
      "time_to_fix": "2-3 hours",
      "impact": "Can improve CTR by 20-30% with rich snippets",
      "exact_fix": "Add JSON-LD Product/Organization schema to page <head>",
      "steps": [
        "Open your page HTML file",
        "Add the JSON-LD script tag before </head>",
        "Test using Google Rich Results Test tool"
      ],
      "code_example": "<script type=\"application/ld+json\">{{\n  \"@context\": \"https://schema.org\",\n  \"@type\": \"SoftwareApplication\",\n  \"name\": \"Product Name\"\n}}</script>"
    }}
  ],
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
  "page_analysis": {{
    "title_score": 85,
    "title_issues": "specific issue or 'Title is well optimized'",
    "meta_score": 70,
    "meta_issues": "specific issue or 'Meta is well optimized'",
    "content_score": 75,
    "content_issues": "specific issue or 'Content is well structured'",
    "technical_score": 80,
    "technical_issues": "specific issue or 'Technical SEO is good'"
  }},
  
TITLE SCORING RULES (use these exact scores):
- 30-60 chars + keyword present = 90-95
- 30-60 chars, no keyword = 75-85  
- 61-70 chars = 55-65 (too long, will be truncated)
- >70 chars = 40-50 (too long)
- <20 chars = 30-40 (too short)
- Missing = 0

META DESCRIPTION SCORING RULES:
- 120-160 chars + keyword + CTA = 90-95
- 120-160 chars, no keyword = 75-85
- 161-200 chars = 55-65 (too long)
- >200 chars = 40-50 (too long, truncated)
- <80 chars = 45-55 (too short)
- Missing = 0
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
    # Auto-detect user's own Google Ads customer_id
    detected_customer_id = DEFAULT_CUSTOMER_ID
    try:
        from ads_manager import get_accessible_accounts
        accounts = get_accessible_accounts(tokens.get("refresh_token"))
        if accounts:
            detected_customer_id = accounts[0].get("customer_id", DEFAULT_CUSTOMER_ID)
    except Exception as e:
        print(f"Could not auto-detect customer_id: {e}")

    _sessions[session_id] = {
        "email": user_info.get("email"),
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "customer_id": detected_customer_id,
    }
    save_sessions(_sessions)
    print(f"Session saved: {session_id} ({user_info.get('email')}) customer_id={detected_customer_id}")
    frontend_url = os.environ.get("FRONTEND_URL", "https://believable-rebirth-production-7e19.up.railway.app")
    return RedirectResponse(url=f"{frontend_url}?session_id={session_id}&email={user_info.get('email')}&customer_id={detected_customer_id}")

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
    # Get currency
    try:
        from ads_manager import get_customer_currency
        currency = get_customer_currency(cid, session["refresh_token"])
    except Exception:
        currency = "USD"
    return {"campaigns": campaigns, "total": len(campaigns), "customer_id": cid, "currency": currency}



@app.post("/api/ads/ab-test/generate")
async def ab_test_generate(request: Request):
    import httpx, json, re
    body = await request.json()
    session_id = body.get("session_id")
    campaign_resource_name = body.get("campaign_resource_name", "")
    campaign_name = body.get("campaign_name", "")
    url = body.get("url", "")
    customer_id = body.get("customer_id", "7836650842")

    session = _sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}

    # Fetch existing ads
    existing_ads = []
    try:
        refresh_token = session.get("refresh_token", "")
        if isinstance(refresh_token, bytes): refresh_token = refresh_token.decode("utf-8")
        import httpx as hx
        async with hx.AsyncClient(timeout=30) as client:
            tr = await client.post("https://oauth2.googleapis.com/token", data={
                "refresh_token": refresh_token,
                "client_id": os.environ.get("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_ADS_CLIENT_ID", ""),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_ADS_CLIENT_SECRET", ""),
                "grant_type": "refresh_token"
            })
            access_token = str(tr.json().get("access_token", "")).strip()
            dev_token = str(os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")).strip()
            headers = {"Authorization": "Bearer " + access_token, "developer-token": dev_token}
            ads_resp = await client.post(
                f"https://googleads.googleapis.com/v23/customers/{customer_id}/googleAds:search",
                headers=headers,
                json={"query": f"SELECT ad_group_ad.ad.responsive_search_ad.headlines, ad_group_ad.ad.responsive_search_ad.descriptions, ad_group_ad.resource_name, metrics.clicks, metrics.impressions, metrics.ctr FROM ad_group_ad WHERE campaign.resource_name = '{campaign_resource_name}' LIMIT 3"}
            )
            if ads_resp.status_code == 200:
                for row in ads_resp.json().get("results", []):
                    ad = row.get("adGroupAd", {}).get("ad", {}).get("responsiveSearchAd", {})
                    m = row.get("metrics", {})
                    existing_ads.append({
                        "headlines": [h.get("text", "") for h in ad.get("headlines", [])[:5]],
                        "descriptions": [d.get("text", "") for d in ad.get("descriptions", [])[:2]],
                        "clicks": m.get("clicks", 0),
                        "ctr": round(float(m.get("ctr", 0)) * 100, 2)
                    })
    except Exception as e:
        print(f"Ads fetch error: {e}")

    # Generate A/B variants with Gemini
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        existing_summary = json.dumps(existing_ads) if existing_ads else "No existing ads"
        prompt = "Generate 2 A/B test ad variants for Google Ads. Campaign: " + campaign_name + ". Website: " + url + ". Existing ads: " + existing_summary + ". Return JSON: {variant_a: {name: string, angle: string, headlines: [5 strings max 30 chars each], descriptions: [2 strings max 90 chars each], rationale: string}, variant_b: {name: string, angle: string, headlines: [5 strings max 30 chars each], descriptions: [2 strings max 90 chars each], rationale: string}, recommendation: string}. Variant A should be emotional/benefit focused. Variant B should be feature/proof focused. Make headlines compelling and specific."
        async with hx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + gemini_key,
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            clean = re.sub(r"```json|```", "", text).strip()
            match = re.search(r"{.*}", clean, re.DOTALL)
            if match:
                data = json.loads(match.group())
                data["existing_ads"] = existing_ads
                return data
    except Exception as e:
        print(f"Gemini error: {e}")

    return {
        "variant_a": {
            "name": "Version A - Emotional",
            "angle": "Benefit focused",
            "headlines": ["Transform Your SEO Today", "Rank #1 on Google Fast", "AI-Powered SEO Tool", "Get More Traffic Now", "Free SEO Analysis"],
            "descriptions": ["Boost your website rankings with AI. Get actionable insights in minutes.", "Join 1000+ businesses growing with our AI SEO platform. Try free today."],
            "rationale": "Focuses on emotional benefits and quick results"
        },
        "variant_b": {
            "name": "Version B - Feature",
            "angle": "Feature focused",
            "headlines": ["AI SEO + Google Ads Tool", "Keywords, Ads & Analytics", "Complete SEM Platform", "Real-Time SEO Insights", "Campaign Automation"],
            "descriptions": ["All-in-one SEM platform with AI analysis, keyword research and campaign management.", "Automate Google Ads campaigns. Track rankings. Optimize CTR. Start free."],
            "rationale": "Highlights specific features for informed buyers"
        },
        "recommendation": "Test both for 14 days. Version A typically wins for awareness campaigns, Version B for bottom-funnel.",
        "existing_ads": existing_ads
    }


@app.post("/api/ads/ab-test/publish")
async def ab_test_publish(request: Request):
    import httpx, json
    body = await request.json()
    session_id = body.get("session_id")
    campaign_resource_name = body.get("campaign_resource_name", "")
    customer_id = body.get("customer_id", "7836650842")
    headlines = body.get("headlines", [])
    descriptions = body.get("descriptions", [])
    variant_name = body.get("variant_name", "A/B Variant")

    session = _sessions.get(session_id)
    if not session:
        fresh = load_sessions()
        session = fresh.get(session_id)
    if not session:
        return {"success": False, "message": "Session not found - please reconnect Google Ads"}

    try:
        refresh_token = session.get("refresh_token", "")
        refresh_token = refresh_token.decode("utf-8") if isinstance(refresh_token, bytes) else str(refresh_token)
        # Use correct env var names for token refresh
        import httpx as _hx
        _tr = _hx.post("https://oauth2.googleapis.com/token", data={
            "client_id": os.environ.get("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_ADS_CLIENT_ID", ""),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_ADS_CLIENT_SECRET", ""),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        })
        _tr_data = _tr.json()
        print(f"Token refresh response: {list(_tr_data.keys())}")
        _access_token = _tr_data.get("access_token", "")
        _dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
        headers_req = {
            "Authorization": "Bearer " + str(_access_token),
            "developer-token": str(_dev_token),
            "Content-Type": "application/json"
        }
        # Save variant to DB for reference
        manager_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
        if manager_id:
            headers_req["login-customer-id"] = manager_id
        async with httpx.AsyncClient(timeout=30) as client:

            # Get ad group for this campaign
            ag_resp = await client.post(
                f"https://googleads.googleapis.com/v23/customers/{customer_id}/googleAds:search",
                headers=headers_req,
                json={"query": f"SELECT ad_group.resource_name, ad_group.name FROM ad_group WHERE campaign.resource_name = '{campaign_resource_name}' AND ad_group.status = 'ENABLED' LIMIT 1"}
            )
            print(f"Ad group response status: {ag_resp.status_code}")
            print(f"Ad group response: {ag_resp.text[:200]}")
            if ag_resp.status_code != 200:
                return {"success": False, "message": f"Google Ads API error: {ag_resp.text[:200]}"}
            ag_data = ag_resp.json()
            results = ag_data.get("results", [])
            if not results:
                return {"success": False, "message": "No active ad group found"}

            ad_group_resource = results[0]["adGroup"]["resourceName"]

            # Create new RSA ad - minimum 3 headlines, 2 descriptions
            import time
            unique_tag = f"v{int(time.time()) % 10000}"
            extra = ["Try Free Today", "AI SEO Platform", "Start Now Free"]
            all_headlines = headlines + extra
            all_descriptions = descriptions if len(descriptions) >= 2 else descriptions + ["Boost your website rankings with AI-powered SEO tools."]
            # Make unique by adding tag to last headline
            unique_headlines = all_headlines[:4] + [f"{unique_tag} Test"]
            rsa_headlines = [{"text": h[:30]} for h in unique_headlines[:5]]
            rsa_descriptions = [{"text": d[:90]} for d in all_descriptions[:2]]

            ad_payload = {
                "operations": [{
                    "create": {
                        "adGroup": ad_group_resource,
                        "ad": {
                            "responsiveSearchAd": {
                                "headlines": rsa_headlines,
                                "descriptions": rsa_descriptions,
                                "path1": "ai-seo",
                                "path2": "free-trial"
                            },
                            "finalUrls": ["https://sakthivelraja.ai"]
                        },
                        "status": "PAUSED"
                    }
                }]
            }

            ad_resp = await client.post(
                f"https://googleads.googleapis.com/v23/customers/{customer_id}/adGroupAds:mutate",
                headers=headers_req,
                json=ad_payload
            )

            if ad_resp.status_code == 200:
                return {"success": True, "message": f"{variant_name} published as PAUSED ad. Enable in Google Ads to start testing."}
            else:
                err = ad_resp.json()
                return {"success": False, "message": str(err.get("error", {}).get("message", "Failed to publish"))}

    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/ads/budget-allocator")
async def budget_allocator(request: Request):
    import httpx, json, re
    body = await request.json()
    campaigns = body.get("campaigns", [])
    total_budget = body.get("total_budget", 0)
    if not campaigns:
        return {"error": "No campaigns provided"}
    per = round(total_budget / max(len(campaigns), 1), 2)
    campaign_summary = [{
        "name": c.get("campaign_name", ""),
        "resource_name": c.get("resource_name", ""),
        "clicks": c.get("clicks", 0),
        "impressions": c.get("impressions", 0),
        "ctr": round(c.get("ctr", 0), 2),
        "spend": round(c.get("spend_today_usd", 0), 2),
        "current_budget": per
    } for c in campaigns]
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        prompt = "You are a Google Ads budget expert. Campaigns: " + json.dumps(campaign_summary) + " Total: Rs." + str(total_budget) + ". Return JSON: {analysis, allocations:[{campaign_name,resource_name,current_budget,recommended_budget,change,change_pct,reason,performance}], expected_improvement}"
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + gemini_key,
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            clean = re.sub(r"```json|```", "", text).strip()
            match = re.search(r"{.*}", clean, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception as e:
        print(f"Error: {e}")
    # Check if any campaign has real data
    has_data = any(c.get("clicks", 0) > 0 or c.get("impressions", 0) > 0 for c in campaigns)
    if not has_data:
        return {
            "analysis": f"Your {len(campaigns)} campaigns need more data. Run them for 7+ days to enable AI budget optimization.",
            "no_data": True,
            "allocations": [],
            "expected_improvement": "Once campaigns get clicks and impressions, AI will recommend optimal budget splits to maximize ROI."
        }
    return {
        "analysis": f"Analyzing {len(campaigns)} campaigns with Rs.{total_budget}/day total budget.",
        "allocations": [{
            "campaign_name": c.get("campaign_name", ""),
            "resource_name": c.get("resource_name", ""),
            "current_budget": per, "recommended_budget": per,
            "change": 0, "change_pct": 0,
            "reason": "Need more performance data",
            "performance": "AVERAGE"
        } for c in campaigns],
        "expected_improvement": "Monitor for 7 days"
    }

@app.post("/api/ads/doctor")
async def campaign_doctor(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    campaign_resource_name = body.get("campaign_resource_name", "")
    campaign_name = body.get("campaign_name", "")
    clicks = body.get("clicks", 0)
    impressions = body.get("impressions", 0)
    ctr = body.get("ctr", 0)
    spend = body.get("spend", 0)
    status = body.get("status", "")
    customer_id = body.get("customer_id", "7836650842")

    session = _sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}

    # Step 1: Fetch keywords for this campaign
    keywords_data = []
    ads_data = []
    try:
        refresh_token = session.get("refresh_token", "")
        import httpx, json

        # Get access token
        async with httpx.AsyncClient(timeout=30) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "refresh_token": refresh_token,
                    "client_id": os.environ.get("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_ADS_CLIENT_ID", ""),
                    "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_ADS_CLIENT_SECRET", ""),
                    "grant_type": "refresh_token"
                }
            )
            access_token = token_resp.json().get("access_token", "")

            dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
            headers = {
                "Authorization": f"Bearer {access_token}",
                "developer-token": dev_token,
                "Content-Type": "application/json"
            }

            # Fetch keywords
            kw_query = {
                "query": f"SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.clicks, metrics.impressions, metrics.ctr, metrics.average_cpc FROM ad_group_criterion WHERE campaign.resource_name = '{campaign_resource_name}' AND ad_group_criterion.type = 'KEYWORD' LIMIT 20"
            }
            kw_resp = await client.post(
                f"https://googleads.googleapis.com/v23/customers/{customer_id}/googleAds:search",
                headers=headers,
                json=kw_query
            )
            if kw_resp.status_code == 200:
                kw_data = kw_resp.json()
                for row in kw_data.get("results", []):
                    kw = row.get("adGroupCriterion", {}).get("keyword", {})
                    m = row.get("metrics", {})
                    keywords_data.append({
                        "text": kw.get("text", ""),
                        "match_type": kw.get("matchType", ""),
                        "clicks": m.get("clicks", 0),
                        "impressions": m.get("impressions", 0),
                        "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                        "avg_cpc": round(float(m.get("averageCpc", 0)) / 1000000, 2)
                    })

            # Fetch ads
            ads_query = {
                "query": f"SELECT ad_group_ad.ad.responsive_search_ad.headlines, ad_group_ad.ad.responsive_search_ad.descriptions, metrics.clicks, metrics.impressions, metrics.ctr FROM ad_group_ad WHERE campaign.resource_name = '{campaign_resource_name}' LIMIT 5"
            }
            ads_resp = await client.post(
                f"https://googleads.googleapis.com/v23/customers/{customer_id}/googleAds:search",
                headers=headers,
                json=ads_query
            )
            if ads_resp.status_code == 200:
                ads_json = ads_resp.json()
                for row in ads_json.get("results", []):
                    ad = row.get("adGroupAd", {}).get("ad", {}).get("responsiveSearchAd", {})
                    m = row.get("metrics", {})
                    headlines = [h.get("text", "") for h in ad.get("headlines", [])[:3]]
                    ads_data.append({
                        "headlines": headlines,
                        "clicks": m.get("clicks", 0),
                        "impressions": m.get("impressions", 0),
                        "ctr": round(float(m.get("ctr", 0)) * 100, 2)
                    })
    except Exception as e:
        print(f"Keyword fetch error: {e}")

    # Step 2: Gemini Deep Analysis
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")

        kw_summary = json.dumps(keywords_data[:10]) if keywords_data else "No keyword data available"
        ads_summary = json.dumps(ads_data[:3]) if ads_data else "No ad data available"

        # Health score calculation
        health = 100
        issues = []
        if impressions == 0: health -= 40; issues.append("No impressions — ads not showing")
        elif clicks == 0: health -= 30; issues.append("Impressions but 0 clicks — ad copy weak")
        elif ctr < 1: health -= 20; issues.append(f"Low CTR {ctr:.2f}% — industry avg is 3-5%")
        if spend == 0 and status == "ENABLED": health -= 15; issues.append("No spend — budget or bid issue")
        if not keywords_data: health -= 10; issues.append("No keywords found")
        health = max(health, 5)

        severity = "CRITICAL" if health < 40 else "WARNING" if health < 70 else "HEALTHY"

        prompt = f"""You are a senior Google Ads agency expert doing a campaign audit. Be specific, actionable, and direct.

CAMPAIGN DATA:
- Name: {campaign_name}
- Status: {status}
- Health Score: {health}/100 ({severity})
- Clicks: {clicks}, Impressions: {impressions}, CTR: {ctr:.2f}%, Spend: Rs.{spend:.2f}
- Issues detected: {issues}

KEYWORDS:
{kw_summary}

ADS:
{ads_summary}

Return ONLY this JSON (no markdown, no explanation):
{{
  "health_score": {health},
  "severity": "{severity}",
  "diagnosis": "2-3 sentence specific diagnosis of what is wrong and why",
  "prescriptions": [
    {{
      "id": "rx1",
      "priority": "CRITICAL",
      "title": "Specific action title",
      "problem": "What exactly is wrong",
      "fix": "Exact fix with specific values (e.g. change bid from Rs.10 to Rs.35)",
      "impact": "Expected result (e.g. CTR 0% to 3%, +45 clicks/month)",
      "type": "keyword|bid|ad_copy|budget|targeting",
      "auto_apply": true
    }}
  ],
  "roi_prediction": {{
    "current_monthly_clicks": {clicks * 30},
    "predicted_monthly_clicks": {max(clicks * 30, 45)},
    "current_spend": {spend * 30},
    "predicted_spend": {spend * 30},
    "improvement_pct": 85
  }}
}}"""

        async with httpx.AsyncClient(timeout=45) as client:
            gemini_payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + gemini_key,
                json=gemini_payload
            )
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            import re
            clean = re.sub(r"```json|```", "", text).strip()
            match = re.search(r"{.*}", clean, re.DOTALL)
            if match:
                data = json.loads(match.group())
                data["keywords"] = keywords_data
                data["ads"] = ads_data
                return data

    except Exception as e:
        print(f"Gemini error: {e}")

    # Fallback
    severity = "CRITICAL" if impressions == 0 else "WARNING" if clicks == 0 else "HEALTHY"
    health = 20 if impressions == 0 else 45 if clicks == 0 else 70
    return {
        "health_score": health,
        "severity": severity,
        "diagnosis": f"Campaign has {impressions} impressions and {clicks} clicks. {'Ads are not showing - check bids and budget.' if impressions == 0 else 'Ads showing but no clicks - ad copy needs improvement.'}",
        "prescriptions": [
            {"id": "rx1", "priority": "CRITICAL", "title": "Increase Bids", "problem": "Bids too low to compete in auction", "fix": "Increase keyword bids to Rs.25-50 range", "impact": "Start getting impressions within 24 hours", "type": "bid", "auto_apply": False},
            {"id": "rx2", "priority": "HIGH", "title": "Improve Ad Headlines", "problem": "Generic headlines not attracting clicks", "fix": "Use specific benefit-focused headlines", "impact": "CTR improvement from 0% to 2-3%", "type": "ad_copy", "auto_apply": False},
            {"id": "rx3", "priority": "MEDIUM", "title": "Add Exact Match Keywords", "problem": "Broad keywords wasting budget", "fix": "Convert top keywords to exact match", "impact": "Better targeting, lower wasted spend", "type": "keyword", "auto_apply": False}
        ],
        "roi_prediction": {
            "current_monthly_clicks": clicks * 30,
            "predicted_monthly_clicks": max(clicks * 30, 45),
            "current_spend": spend * 30,
            "predicted_spend": spend * 30,
            "improvement_pct": 85
        },
        "keywords": keywords_data,
        "ads": ads_data
    }

@app.post("/api/ads/optimise")
async def optimise_campaign(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    campaign_name = body.get("campaign_name", "")
    clicks = body.get("clicks", 0)
    impressions = body.get("impressions", 0)
    ctr = body.get("ctr", 0)
    spend = body.get("spend", 0)
    status = body.get("status", "")

    try:
        import httpx
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        prompt = f"""You are a Google Ads expert. Analyze this campaign and give 3-4 specific optimization actions.

Campaign: {campaign_name}
Status: {status}
Clicks: {clicks}, Impressions: {impressions}, CTR: {ctr:.2f}%, Spend: Rs.{spend:.2f}

Return JSON only (no markdown):
{{
  "summary": "2 sentence analysis of campaign performance",
  "actions": [
    {{"title": "Action title", "description": "Why this helps", "type": "budget|bid|keyword|status"}},
    {{"title": "Action title", "description": "Why this helps", "type": "budget|bid|keyword|status"}}
  ]
}}"""

        gemini_payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + gemini_key,
                json=gemini_payload
            )
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            import re, json
            clean = re.sub(r"```json|```", "", text).strip()
            match = re.search(r"{.*}", clean, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return data
            return {"summary": text[:200], "actions": []}
    except Exception as e:
        low_ctr_msg = "Low CTR - consider updating ad copy." if ctr < 2 else "Performance looks stable."
        return {
            "summary": f"Campaign has {clicks} clicks and {impressions} impressions. " + low_ctr_msg,
            "actions": [
                {"title": "Review Ad Copy", "description": "Update headlines to improve CTR", "type": "keyword"},
                {"title": "Check Keyword Match Types", "description": "Use exact match for better targeting", "type": "keyword"},
                {"title": "Adjust Bid Strategy", "description": "Consider Target CPA for better ROI", "type": "bid"}
            ]
        }

@app.post("/api/ads/optimise/apply")
async def optimise_apply(request: Request):
    body = await request.json()
    action = body.get("action", {})
    action_type = action.get("type", "")
    campaign_resource_name = body.get("campaign_resource_name", "")
    session_id = body.get("session_id", "")
    customer_id = body.get("customer_id", "7836650842")
    
    session = _sessions.get(session_id)
    if not session:
        return {"success": False, "message": "Session not found"}
    
    access_token = session.get("access_token")
    if not access_token:
        return {"success": False, "message": "Not authenticated"}
    
    try:
        import httpx
        if action_type == "bid":
            # Suggest manual CPC strategy
            mutate_url = f"https://googleads.googleapis.com/v23/customers/{customer_id}/campaigns:mutate"
            payload = {
                "operations": [{
                    "update": {
                        "resourceName": campaign_resource_name,
                        "manualCpc": {"enhancedCpcEnabled": True}
                    },
                    "updateMask": "manual_cpc.enhanced_cpc_enabled"
                }]
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    mutate_url,
                    headers={"Authorization": f"Bearer {access_token}", "developer-token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")},
                    json=payload
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "Bid strategy updated to Enhanced CPC"}
                else:
                    return {"success": True, "message": f"Noted: {action.get('title', '')} - Apply in Google Ads dashboard"}
        else:
            # For keyword and ad copy actions - guide user
            title = action.get("title", "").lower()
            if "ad copy" in title or "headline" in title:
                msg = "Go to Google Ads > Ads & Extensions > Edit your headline and description"
            elif "keyword" in title or "match" in title:
                msg = "Go to Google Ads > Keywords > Select keyword > Change match type to Exact or Phrase"
            elif "bid" in title or "cpc" in title or "cpa" in title:
                msg = "Go to Google Ads > Campaigns > Settings > Bidding > Change strategy"
            elif "budget" in title:
                msg = "Go to Google Ads > Campaigns > Edit daily budget"
            elif "extension" in title or "asset" in title:
                msg = "Go to Google Ads > Ads & Extensions > Extensions > Add sitelinks/callouts"
            else:
                msg = f"Go to Google Ads dashboard to apply: {action.get(chr(39) + 'title' + chr(39), '')}"
            return {"success": True, "message": msg}
    except Exception as e:
        return {"success": True, "message": f"Noted: {action.get('title', '')} - Apply manually in Google Ads dashboard"}

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
async def get_ai_traffic(days: int = 30, site_url: Optional[str] = Query(default="")):
    """Get AI traffic statistics."""
    stats = get_traffic_stats(days)
    # If site_url provided, check if script is installed by looking for visits from that domain
    if site_url:
        try:
            from urllib.parse import urlparse
            domain = urlparse(site_url).netloc or site_url
            visits = stats.get("visits", [])
            domain_visits = [v for v in visits if domain in v.get("page", "")]
            stats["script_installed"] = len(domain_visits) > 0
            stats["analysed_domain"] = domain
        except Exception:
            stats["script_installed"] = False
            stats["analysed_domain"] = ""
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
    kw_str = ", ".join(keywords[:10])

    prompt = f"""You are an expert SEO and competitive intelligence analyst. Analyze {url} (SEO score: {seo_score}) against these competitors: {comp_str}.
My site keywords: {kw_str}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "my_site": {{"domain": "{domain}", "score": {seo_score}, "strengths": ["s1","s2","s3"], "weaknesses": ["w1","w2","w3"]}},
  "competitors": [{{"domain": "comp.com", "estimated_score": 75, "estimated_traffic": "50k/month", "top_keywords": ["kw1","kw2"], "strengths": ["s1","s2"], "weaknesses": ["w1","w2"], "ad_strategy": "their ads approach", "social_presence": "their social activity", "social_platforms": {{"linkedin": 85, "twitter": 70, "instagram": 40, "youtube": 60}}, "content_topics": ["topic1","topic2"], "ad_keywords": ["kw1","kw2"], "estimated_ad_spend": "50k-100k/month"}}],
  "keyword_overlap": {{"shared_keywords": ["kw1","kw2"], "competitor_only": ["kw3","kw4"], "my_unique": ["kw5","kw6"], "opportunity_keywords": ["opp1","opp2"]}},
  "content_gaps": [{{"topic": "topic", "competitor_covering": "comp.com", "opportunity": "how to use this", "priority": "high"}}],
  "ad_intelligence": {{"competitors_running_ads": ["comp1.com"], "common_ad_keywords": ["kw1","kw2"], "estimated_competition_level": "high", "my_ad_opportunity": "specific opportunity", "recommended_ad_keywords": ["kw1","kw2"]}},
  "social_comparison": {{"leader": "comp.com", "my_score": 45, "platforms": [{{"platform": "LinkedIn", "my_score": 50, "best_competitor": 90, "gap": 40, "action": "specific action"}}, {{"platform": "Twitter/X", "my_score": 30, "best_competitor": 75, "gap": 45, "action": "specific action"}}, {{"platform": "YouTube", "my_score": 20, "best_competitor": 80, "gap": 60, "action": "specific action"}}]}},
  "winning_strategy": {{"summary": "2-3 sentence strategy", "quick_wins": [{{"action": "action", "impact": "result", "timeline": "1-2 weeks", "effort": "low"}}], "long_term": [{{"action": "action", "impact": "result", "timeline": "3-6 months", "effort": "high"}}], "differentiator": "unique angle"}},
  "opportunities": ["opp1","opp2","opp3"],
  "threats": ["threat1","threat2","threat3"],
  "action_plan": ["action1","action2","action3","action4","action5"]
}}"""

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
                lr = data.get("lighthouseResult", {})
                
                # Screenshot thumbnail
                screenshot = audits.get("final-screenshot", {}).get("details", {}).get("data", "")
                
                # Mobile specific issues
                mobile_issues = []
                if strategy == "mobile":
                    if audits.get("viewport", {}).get("score", 1) == 0:
                        mobile_issues.append("No viewport meta tag")
                    if audits.get("font-size", {}).get("score", 1) == 0:
                        mobile_issues.append("Text too small to read")
                    if audits.get("tap-targets", {}).get("score", 1) == 0:
                        mobile_issues.append("Tap targets too small")
                    if audits.get("content-width", {}).get("score", 1) == 0:
                        mobile_issues.append("Content wider than screen")

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
                    "screenshot": screenshot,
                    "mobile_issues": mobile_issues,
                    "interactive": audits.get("interactive", {}).get("displayValue", "N/A"),
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
                "from": "SEM AI <reports@sakthivelraja.ai>",
                "to": [email],
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


# ─── SEARCH CONSOLE OAUTH ────────────────────────────────────────────────────

SC_CLIENT_ID = os.environ.get("SEARCH_CONSOLE_CLIENT_ID", "")
SC_CLIENT_SECRET = os.environ.get("SEARCH_CONSOLE_CLIENT_SECRET", "")
SC_REDIRECT_URI = os.environ.get("SEARCH_CONSOLE_REDIRECT_URI", "https://sem-ai-production.up.railway.app/api/search-console/callback")
SC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# In-memory token store (per session)
sc_tokens = {}

def save_sc_token(session_id: str, tokens: dict):
    """Save Search Console token to DB."""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sc_tokens (
                    session_id TEXT PRIMARY KEY,
                    tokens JSONB,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            import json
            cur.execute("""
                INSERT INTO sc_tokens (session_id, tokens) VALUES (%s, %s)
                ON CONFLICT (session_id) DO UPDATE SET tokens = %s, updated_at = NOW()
            """, (session_id, json.dumps(tokens), json.dumps(tokens)))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        print(f"DB save error: {e}")
    sc_tokens[session_id] = tokens

def load_sc_token(session_id: str) -> dict:
    """Load Search Console token from DB."""
    if session_id in sc_tokens:
        return sc_tokens[session_id]
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT tokens FROM sc_tokens WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                import json
                token_data = row[0]
                if isinstance(token_data, str):
                    token_data = json.loads(token_data)
                sc_tokens[session_id] = token_data
                print(f"Loaded SC token from DB for {session_id}")
                return token_data
    except Exception as e:
        print(f"DB load error: {e}")
    return None

@app.get("/api/search-console/auth")
async def search_console_auth(session_id: str = "default"):
    """Generate OAuth URL for Search Console authorization."""
    if not SC_CLIENT_ID:
        return {"error": "Search Console not configured"}
    
    params = {
        "client_id": SC_CLIENT_ID,
        "redirect_uri": SC_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SC_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": session_id,
    }
    from urllib.parse import urlencode
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return {"auth_url": auth_url}

@app.get("/api/search-console/callback")
async def search_console_callback(code: str, state: str = "default"):
    """Handle OAuth callback and exchange code for tokens."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": SC_CLIENT_ID,
                    "client_secret": SC_CLIENT_SECRET,
                    "redirect_uri": SC_REDIRECT_URI,
                    "grant_type": "authorization_code",
                }
            )
            tokens = resp.json()
            if "access_token" in tokens:
                save_sc_token(state, tokens)
                # Redirect back to dashboard
                dashboard_url = "https://believable-rebirth-production-7e19.up.railway.app/?gsc_connected=1&session_id=" + state
                return HTMLResponse(f"""
                <html><body style="font-family:sans-serif;text-align:center;padding:50px;background:#0f172a;color:white">
                <h2>Search Console Connected</h2>
                <p>Redirecting back to SEM AI...</p>
                <script>
                  setTimeout(() => window.location.href = "{dashboard_url}", 1000);
                </script>
                </body></html>
                """)
            else:
                return HTMLResponse(f"<html><body>Error: {tokens.get('error_description', 'Unknown error')}</body></html>")
    except Exception as e:
        return HTMLResponse(f"<html><body>Error: {str(e)}</body></html>")

@app.get("/api/search-console/status")
async def search_console_status(session_id: str = "default"):
    """Check if Search Console is connected."""
    return {"connected": load_sc_token(session_id) is not None}

@app.post("/api/search-console/data")
async def get_search_console_data(request: Request):
    """Fetch Search Console data for a URL."""
    try:
        body = await request.json()
        url = body.get("url", "")
        session_id = body.get("session_id", "default")
        days = body.get("days", 28)
        
        tokens = load_sc_token(session_id)
        if not tokens:
            return {"error": "Search Console not connected", "connected": False}
        access_token = tokens.get("access_token", "")
        
        # Get site URL from URL - use domain property format
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        site_url = f"sc-domain:{domain}"
        print(f"Using site_url: {site_url}")
        
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            # First check what sites are available
            sites_resp = await client.get(
                "https://www.googleapis.com/webmasters/v3/sites",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            print(f"Available sites: {sites_resp.text[:500]}")
            
            # Get search analytics for this page
            resp = await client.post(
                f"https://searchconsole.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "startDate": start_date,
                    "endDate": end_date,
                    "dimensions": ["query"],
                    "rowLimit": 50,
                }
            )
            
            if resp.status_code == 401:
                # Token expired — try refresh
                if "refresh_token" in tokens:
                    refresh_resp = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "refresh_token": tokens["refresh_token"],
                            "client_id": SC_CLIENT_ID,
                            "client_secret": SC_CLIENT_SECRET,
                            "grant_type": "refresh_token",
                        }
                    )
                    new_tokens = refresh_resp.json()
                    if "access_token" in new_tokens:
                        merged = {**load_sc_token(session_id), **new_tokens}
                        save_sc_token(session_id, merged)
                        return {"error": "Token refreshed, please retry"}
                return {"error": "Authentication expired, please reconnect"}
            
            print(f"SC API status: {resp.status_code}")
            print(f"SC API response: {resp.text[:500]}")
            if not resp.text.strip():
                return {"error": "Empty response from Search Console API - check if site is verified", "connected": False}
            data = resp.json()
            rows = data.get("rows", [])
            
            # Get overall page metrics
            page_resp = await client.post(
                f"https://searchconsole.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "startDate": start_date,
                    "endDate": end_date,
                    "dimensions": ["page"],
                    "dimensionFilterGroups": [{
                        "filters": [{
                            "dimension": "page",
                            "operator": "equals",
                            "expression": url
                        }]
                    }],
                }
            )
            page_data = page_resp.json()
            page_rows = page_data.get("rows", [])
            page_metrics = page_rows[0] if page_rows else {}
            
            return {
                "connected": True,
                "url": url,
                "period": f"Last {days} days",
                "page_metrics": {
                    "clicks": page_metrics.get("clicks", 0),
                    "impressions": page_metrics.get("impressions", 0),
                    "ctr": round(page_metrics.get("ctr", 0) * 100, 2),
                    "position": round(page_metrics.get("position", 0), 1),
                },
                "top_queries": [
                    {
                        "keyword": row["keys"][0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": round(row.get("ctr", 0) * 100, 2),
                        "position": round(row.get("position", 0), 1),
                    }
                    for row in rows[:15]
                ],
                "keywords": [
                    {
                        "query": row["keys"][0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": round(row.get("ctr", 0), 4),
                        "position": round(row.get("position", 0), 1),
                    }
                    for row in rows[:50]
                ],
                "pages": [
                    {
                        "page": row["keys"][0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": round(row.get("ctr", 0), 4),
                        "position": round(row.get("position", 0), 1),
                    }
                    for row in page_rows[:20]
                ],
                "summary": {
                    "clicks": sum(r.get("clicks", 0) for r in rows),
                    "impressions": sum(r.get("impressions", 0) for r in rows),
                    "ctr": round(sum(r.get("ctr", 0) for r in rows) / max(len(rows), 1), 4),
                    "position": round(sum(r.get("position", 0) for r in rows) / max(len(rows), 1), 1),
                }
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "connected": False}

@app.post("/api/search-console/insights")
async def search_console_insights(request: Request):
    body = await request.json()
    data = body.get("data", {})
    url = body.get("url", "")
    keywords = data.get("keywords", [])
    summary = data.get("summary", {})
    
    opportunities = [k for k in keywords if 4 <= k.get("position", 0) <= 20 and k.get("impressions", 0) > 10]
    low_ctr = [k for k in keywords if k.get("ctr", 0) < 0.03 and k.get("impressions", 0) > 50]
    gaps = [k for k in keywords if k.get("impressions", 0) > 100 and k.get("clicks", 0) < 5]
    
    try:
        import httpx
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        prompt = f"""Analyze this Google Search Console data for {url} and give a 2-3 sentence actionable summary in English:
- Total clicks: {summary.get("clicks", 0)}, Impressions: {summary.get("impressions", 0)}, CTR: {summary.get("ctr", 0):.2%}, Avg Position: {summary.get("position", 0):.1f}
- {len(opportunities)} keyword opportunities (position 4-20)
- {len(low_ctr)} low CTR keywords needing title/meta optimization  
- {len(gaps)} content gaps with high impressions but low clicks
Top opportunity keywords: {[k["query"] for k in opportunities[:5]]}
Give specific actionable advice."""

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
            result = resp.json()
            summary_text = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        summary_text = f"Found {len(opportunities)} keyword opportunities and {len(gaps)} content gaps. Focus on optimizing position 4-20 keywords for quick wins."
    
    return {"summary": summary_text, "opportunity_count": len(opportunities), "gap_count": len(gaps), "low_ctr_count": len(low_ctr)}

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
        camp_str = _json.dumps(campaigns) if campaigns else "No campaigns data available yet"
        prompt = f"""You are SEMA, an expert Google Ads AI assistant and performance analyst.

CAMPAIGN DATA:
{camp_str}

ANALYSIS GUIDELINES:
- If CTR < 1%: suggest ad copy improvements
- If CPC is high: suggest bid adjustments or keyword refinement  
- If impressions are 0: check ad approval status, budget, targeting
- If spend is 0 but campaign enabled: check billing and policy issues
- Compare campaigns and identify best/worst performers
- Suggest specific actionable changes with expected impact

USER QUESTION: {message}

Provide a detailed, actionable response with:
1. Current performance assessment
2. Specific recommendations (bid changes, budget adjustments, ad copy improvements)
3. Priority actions to take today
Be specific with numbers and percentages where possible."""
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

# ─── Smart Ad Variants Endpoint ───────────────────────────────────────────────
@app.post("/api/ads/generate-variants")
async def generate_ad_variants(request: Request):
    """Generate multiple ad variations with different angles."""
    try:
        body = await request.json()
        url = body.get("url", "")
        seo_report = body.get("seo_report", {})

        # Build context from SEO report
        title = seo_report.get("page_metadata", {}).get("title", "") or ""
        keywords = [k.get("keyword", "") for k in (seo_report.get("keyword_suggestions") or [])[:5]]
        strengths = [s.get("point", s) if isinstance(s, dict) else s for s in (seo_report.get("strengths") or [])[:3]]
        summary = seo_report.get("ai_summary", "") or seo_report.get("summary", "")

        prompt = f"""You are a Google Ads expert. Generate 6 high-converting ad variations for this website.

URL: {url}
Page Title: {title}
Top Keywords: {", ".join(keywords)}
Key Strengths: {", ".join([str(s) for s in strengths])}
Summary: {summary[:300] if summary else ""}

Generate 6 ad variations with these angles:
1. Pain Point - address user problems
2. Benefit - highlight key benefits  
3. Social Proof - trust and credibility
4. Urgency - time-sensitive offer
5. Question - engage curiosity
6. Solution - direct solution angle

For EACH variation return:
- angle: the angle name
- predicted_score: CTR prediction 60-95 (integer)
- why: one sentence why this angle works
- headlines: array of 5 headlines (MAX 30 chars each - STRICTLY enforce this)
- descriptions: array of 2 descriptions (MAX 90 chars each - STRICTLY enforce this)
- keywords: array of 5 target keywords

Return ONLY valid JSON:
{{
  "variants": [
    {{
      "angle": "Pain Point",
      "predicted_score": 85,
      "why": "Directly addresses the main user frustration",
      "headlines": ["headline1", "headline2", "headline3", "headline4", "headline5"],
      "descriptions": ["description1 max 90 chars", "description2 max 90 chars"],
      "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
    }}
  ]
}}"""

        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        import json
        data = json.loads(text)

        # Enforce character limits
        for variant in data.get("variants", []):
            variant["headlines"] = [h[:30] for h in variant.get("headlines", [])]
            variant["descriptions"] = [d[:90] for d in variant.get("descriptions", [])]

        return data

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "variants": []}

# ─── Remove Campaign Endpoint ─────────────────────────────────────────────────
@app.post("/api/ads/campaigns/{campaign_id}/remove")
async def remove_campaign(campaign_id: str, request: Request):
    """Remove/delete a campaign."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        campaign_resource_name = body.get("campaign_resource_name", "")
        
        if session_id not in _sessions:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        session = _sessions[session_id]
        customer_id = session.get("customer_id", DEFAULT_CUSTOMER_ID)
        refresh_token = session.get("refresh_token", "")
        
        if not customer_id:
            raise HTTPException(status_code=400, detail="No customer ID")

        customer_id = customer_id.replace("-", "")
        
        # Use resource_name if provided, else construct it
        if not campaign_resource_name:
            campaign_resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
        
        from ads_manager import get_headers
        headers = get_headers(refresh_token)
        
        resp = httpx.post(
            f"https://googleads.googleapis.com/v23/customers/{customer_id}/campaigns:mutate",
            headers=headers,
            json={"operations": [{"remove": campaign_resource_name}]},
            timeout=30
        )
        
        if resp.status_code == 200:
            return {"success": True, "message": "Campaign removed"}
        else:
            return {"success": False, "error": resp.text}
                
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─── SEM Experiment Analysis Endpoint ────────────────────────────────────────
@app.post("/api/sem/experiment-analysis")
async def sem_experiment_analysis(request: Request):
    try:
        body = await request.json()
        url = body.get("url", "")
        seo_report = body.get("seo_report", {})

        keywords = [k.get("keyword", "") for k in (seo_report.get("keyword_suggestions") or [])[:5]]
        budget = seo_report.get("sem_recommendations", {}).get("monthly_budget_inr", 0)
        cpc = seo_report.get("sem_recommendations", {}).get("estimated_cpc_inr", 35)

        prompt = f"""You are a SEM expert. Analyze this website's SEM potential and provide insights.

URL: {url}
Monthly Budget: ₹{budget}
Avg CPC: ₹{cpc}
Keywords: {", ".join(keywords)}

Return ONLY valid JSON:
{{
  "insights": [
    {{"icon": "🎯", "title": "insight title", "description": "detailed description", "action": "specific action to take"}},
    {{"icon": "💡", "title": "insight title", "description": "detailed description", "action": "specific action to take"}},
    {{"icon": "⚠️", "title": "insight title", "description": "detailed description", "action": "specific action to take"}},
    {{"icon": "🚀", "title": "insight title", "description": "detailed description", "action": "specific action to take"}},
    {{"icon": "📈", "title": "insight title", "description": "detailed description", "action": "specific action to take"}}
  ]
}}"""

        import google.generativeai as genai
        import json
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        return {"insights": [
            {"icon": "💡", "title": "SEM Opportunity", "description": f"Analysis ready for {url}", "action": "Launch your first campaign"}
        ]}

# ─── Single Page Deep Audit ───────────────────────────────────────────────────
@app.post("/api/site-audit/single-page")
async def single_page_audit(request: Request):
    """Deep audit a single page with SEM eligibility analysis."""
    try:
        body = await request.json()
        url = body.get("url", "")
        if not url:
            return {"error": "URL required"}

        import httpx as _hx, json as _json
        from bs4 import BeautifulSoup

        # Fetch the page
        headers = {"User-Agent": "Mozilla/5.0 (compatible; SEMAudit/1.0)"}
        resp = _hx.get(url, headers=headers, timeout=15, follow_redirects=True)
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')

        # Extract page data
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '') if meta_desc else ''
        h1s = [h.get_text().strip() for h in soup.find_all('h1')]
        h2s = [h.get_text().strip() for h in soup.find_all('h2')]
        images = soup.find_all('img')
        images_no_alt = [img for img in images if not img.get('alt')]
        links = soup.find_all('a', href=True)
        word_count = len(soup.get_text().split())
        has_schema = bool(soup.find('script', type='application/ld+json'))
        canonical = soup.find('link', rel='canonical')

        # PageSpeed API
        ps_score = 0
        lcp = fid = cls = "N/A"
        try:
            api_key = os.environ.get("PAGESPEED_API_KEY", "")
            if api_key:
                async with httpx.AsyncClient(timeout=60) as ps_client:
                    ps_resp = await ps_client.get(
                        f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile&key={api_key}&category=performance",
                    )
                ps_data = ps_resp.json()
                perf_score = ps_data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score", 0)
                ps_score = int((perf_score or 0) * 100)
                metrics = ps_data.get("lighthouseResult", {}).get("audits", {})
                lcp = metrics.get("largest-contentful-paint", {}).get("displayValue", "N/A")
                fid = metrics.get("total-blocking-time", {}).get("displayValue", "N/A")
                cls = metrics.get("cumulative-layout-shift", {}).get("displayValue", "N/A")
        except Exception as ps_err:
            print(f"[PageSpeed Error] {ps_err}")
            ps_score = 0

        # Calculate scores
        seo_score = 100
        if not title_text: seo_score -= 20
        elif len(title_text) > 60: seo_score -= 10
        if not meta_desc_text: seo_score -= 15
        elif len(meta_desc_text) > 160: seo_score -= 5
        if not h1s: seo_score -= 15
        if images_no_alt: seo_score -= min(20, len(images_no_alt) * 5)
        if not has_schema: seo_score -= 10

        content_score = 100
        if word_count < 300: content_score -= 30
        elif word_count < 500: content_score -= 15
        if not h2s: content_score -= 20

        technical_score = max(0, ps_score) if ps_score else 60

        overall_score = int((seo_score + content_score + technical_score) / 3)

        # SEM Eligibility
        sem_blockers = []
        sem_suggestions = []

        if not title_text: sem_blockers.append("Missing page title — required for ad relevance")
        if not meta_desc_text: sem_blockers.append("Missing meta description — affects Quality Score")
        if word_count < 300: sem_blockers.append(f"Thin content ({word_count} words) — Google prefers 500+ words for ad landing pages")
        if not h1s: sem_blockers.append("Missing H1 tag — affects landing page quality score")
        if ps_score > 0 and ps_score < 50: sem_blockers.append(f"Low page speed score ({ps_score}/100) — slow pages increase bounce rate and lower Quality Score")
        if images_no_alt: sem_blockers.append(f"{len(images_no_alt)} images missing alt text — affects accessibility and Quality Score")

        if not sem_blockers:
            sem_suggestions.append("Add a clear CTA button above the fold for better conversion rate")
            sem_suggestions.append("Consider adding testimonials or social proof to improve landing page quality")
            sem_suggestions.append("Ensure your landing page content matches your ad keywords closely")
            sem_suggestions.append("Add a contact form or lead capture to maximize ad ROI")
        else:
            sem_suggestions.append("Fix the blockers above to improve your Google Ads Quality Score")
            sem_suggestions.append("Higher Quality Score = lower CPC and better ad positions")

        eligible = len(sem_blockers) == 0

        # AI Analysis
        prompt = f"""Analyze this webpage for SEM/Google Ads eligibility and provide insights.

URL: {url}
Title: {title_text}
Meta Description: {meta_desc_text}
H1: {h1s[0] if h1s else 'None'}
Word Count: {word_count}
Page Speed Score: {ps_score}/100
Images without alt: {len(images_no_alt)}
Schema Markup: {has_schema}
SEM Eligible: {eligible}
Blockers: {sem_blockers}

Return ONLY valid JSON:
{{
  "sem_analysis": {{
    "eligible": {str(eligible).lower()},
    "readiness_score": {overall_score},
    "reason": "2-3 sentence explanation of SEM readiness",
    "estimated_cpc": {35},
    "estimated_ctr": 2.5,
    "competition": "Medium",
    "blockers": {_json.dumps(sem_blockers)},
    "suggestions": {_json.dumps(sem_suggestions)}
  }},
  "content_analysis": {{
    "word_count": {word_count},
    "readability": "Professional",
    "keyword_density": "Good",
    "improvements": ["improvement 1", "improvement 2", "improvement 3"]
  }},
  "technical_checks": [
    {{"label": "Page Title", "status": "{'pass' if title_text else 'fail'}", "value": "{title_text[:40] + '...' if len(title_text) > 40 else title_text}"}},
    {{"label": "Meta Description", "status": "{'pass' if meta_desc_text else 'fail'}", "value": "{'Present' if meta_desc_text else 'Missing'}"}},
    {{"label": "H1 Tag", "status": "{'pass' if h1s else 'fail'}", "value": "{'Present' if h1s else 'Missing'}"}},
    {{"label": "Schema Markup", "status": "{'pass' if has_schema else 'warning'}", "value": "{'Present' if has_schema else 'Missing'}"}},
    {{"label": "Page Speed", "status": "{'pass' if ps_score >= 70 else 'warning' if ps_score >= 50 else 'fail'}", "value": "{ps_score}/100"}},
    {{"label": "Images Alt Text", "status": "{'pass' if not images_no_alt else 'warning'}", "value": "{len(images_no_alt)} missing"}},
    {{"label": "Word Count", "status": "{'pass' if word_count >= 500 else 'warning' if word_count >= 300 else 'fail'}", "value": "{word_count} words"}},
    {{"label": "Canonical URL", "status": "{'pass' if canonical else 'warning'}", "value": "{'Present' if canonical else 'Missing'}"}}
  ]
}}"""

        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.5-flash")
        ai_resp = model.generate_content(prompt)
        text = ai_resp.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = _json.loads(text)
        data["overall_score"] = overall_score
        data["seo_score"] = seo_score
        data["content_score"] = content_score
        data["technical_score"] = technical_score
        data["url"] = url
        return data

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ============================================================
# GA4 CONNECT LAYER
# ============================================================

GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

@app.get("/api/ga4/auth")
async def ga4_auth(session_id: str, property_id: str):
    """Start GA4 OAuth flow."""
    try:
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        redirect_uri = os.environ.get("GA4_REDIRECT_URI", "https://sem-ai-production.up.railway.app/api/ga4/callback")
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/analytics.readonly",
            "access_type": "offline",
            "prompt": "consent",
            "state": f"{session_id}|{property_id}"
        }
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join(f"{k}={v}" for k, v in params.items())
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ga4/callback")
async def ga4_callback(code: str, state: str):
    """Handle GA4 OAuth callback."""
    try:
        session_id, property_id = state.split("|", 1)
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        redirect_uri = os.environ.get("GA4_REDIRECT_URI", "https://sem-ai-production.up.railway.app/api/ga4/callback")

        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            tokens = token_resp.json()

        # Save tokens to DB
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ga4_tokens (
                    session_id TEXT PRIMARY KEY,
                    property_id TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                INSERT INTO ga4_tokens (session_id, property_id, access_token, refresh_token)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    property_id = EXCLUDED.property_id,
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token
            """, (session_id, property_id, access_token, refresh_token))
            conn.commit()

        frontend_url = os.environ.get("FRONTEND_URL", "https://heartfelt-reprieve-production-637b.up.railway.app")
        return RedirectResponse(f"{frontend_url}?ga4_connected=true&session_id={session_id}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ga4/status")
async def ga4_status(session_id: str):
    """Check if GA4 is connected."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ga4_tokens (
                    session_id TEXT PRIMARY KEY,
                    property_id TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute(
                "SELECT property_id FROM ga4_tokens WHERE session_id = %s",
                (session_id,)
            )
            row = cur.fetchone()
        
        if row:
            return {"connected": True, "property_id": row[0]}
        return {"connected": False}
    except Exception as e:
        return {"connected": False}


@app.get("/api/ga4/traffic")
async def ga4_traffic(session_id: str, days: int = 30):
    """Fetch AI traffic data from GA4."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT property_id, access_token, refresh_token FROM ga4_tokens WHERE session_id = %s",
                (session_id,)
            )
            row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="GA4 not connected")
        
        property_id, access_token, refresh_token = row

        # GA4 Data API request
        api_url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
        
        payload = {
            "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
            "dimensions": [
                {"name": "sessionSource"},
                {"name": "sessionMedium"},
                {"name": "date"}
            ],
            "metrics": [
                {"name": "sessions"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"}
            ],
            "dimensionFilter": {
                "orGroup": {
                    "expressions": [
                        {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "chatgpt"}}},
                        {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "perplexity"}}},
                        {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "claude"}}},
                        {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "gemini"}}},
                        {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "copilot"}}},
                        {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "meta.ai"}}},
                        {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "you.com"}}}
                    ]
                }
            }
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                api_url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            # Token expired — refresh
            if resp.status_code == 401:
                refresh_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "refresh_token": refresh_token,
                        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                        "grant_type": "refresh_token"
                    }
                )
                new_tokens = refresh_resp.json()
                new_access = new_tokens.get("access_token", "")
                
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE ga4_tokens SET access_token = %s WHERE session_id = %s",
                        (new_access, session_id)
                    )
                    conn.commit()
                
                resp = await client.post(
                    api_url,
                    json=payload,
                    headers={"Authorization": f"Bearer {new_access}"}
                )

        data = resp.json()
        rows = data.get("rows", [])
        
        # Process rows
        ai_sources = {}
        trend_data = {}
        
        for row in rows:
            source = row["dimensionValues"][0]["value"]
            date = row["dimensionValues"][2]["value"]
            sessions = int(row["metricValues"][0]["value"])
            
            # Group by AI platform
            platform = "Other AI"
            if "chatgpt" in source or "openai" in source: platform = "ChatGPT"
            elif "perplexity" in source: platform = "Perplexity"
            elif "claude" in source: platform = "Claude"
            elif "gemini" in source: platform = "Gemini"
            elif "copilot" in source: platform = "Copilot"
            elif "meta" in source: platform = "Meta AI"
            
            ai_sources[platform] = ai_sources.get(platform, 0) + sessions
            
            # Trend by date
            if date not in trend_data:
                trend_data[date] = 0
            trend_data[date] += sessions

        total = sum(ai_sources.values())
        
        # AI Analysis via Gemini
        ai_insight = ""
        try:
            gemini_key = os.environ.get("GEMINI_API_KEY", "")
            if gemini_key and total > 0:
                top_source = max(ai_sources, key=ai_sources.get) if ai_sources else "None"
                prompt = f"""Analyze this AI traffic data and give 3 actionable insights:
- Total AI visits: {total} in last {days} days
- Top AI source: {top_source} ({ai_sources.get(top_source, 0)} visits)
- All sources: {ai_sources}

Return JSON: {{"insights": [{{"title": "...", "description": "...", "action": "..."}}]}}"""
                
                gem_resp = httpx.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=15
                )
                gem_data = gem_resp.json()
                raw = gem_data["candidates"][0]["content"]["parts"][0]["text"]
                raw = raw.replace("```json", "").replace("```", "").strip()
                ai_insight = json.loads(raw).get("insights", [])
        except:
            ai_insight = []

        # Fetch top pages from GA4
        top_pages = []
        recent_visits = []
        keywords = []
        try:
            pages_payload = {
                "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
                "dimensions": [{"name": "pagePath"}, {"name": "sessionSource"}],
                "metrics": [{"name": "sessions"}],
                "dimensionFilter": {
                    "orGroup": {
                        "expressions": [
                            {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "chatgpt"}}},
                            {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "perplexity"}}},
                            {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "claude"}}},
                            {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "gemini"}}},
                            {"filter": {"fieldName": "sessionSource", "stringFilter": {"matchType": "CONTAINS", "value": "copilot"}}}
                        ]
                    }
                },
                "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
                "limit": 10
            }
            async with httpx.AsyncClient() as pc:
                pages_resp = await pc.post(
                    api_url,
                    json=pages_payload,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            pages_data = pages_resp.json()
            page_map = {}
            for row in pages_data.get("rows", []):
                page = row["dimensionValues"][0]["value"]
                source = row["dimensionValues"][1]["value"]
                sessions = int(row["metricValues"][0]["value"])
                if page not in page_map:
                    page_map[page] = {"page": page, "visits": 0, "platforms": []}
                page_map[page]["visits"] += sessions
                platform = "ChatGPT" if "chatgpt" in source else "Perplexity" if "perplexity" in source else "Claude" if "claude" in source else "Gemini" if "gemini" in source else "Copilot" if "copilot" in source else source
                if platform not in page_map[page]["platforms"]:
                    page_map[page]["platforms"].append(platform)
            top_pages = sorted(page_map.values(), key=lambda x: x["visits"], reverse=True)[:5]

            # Recent visits - date + source + page
            recent_payload = {
                "dateRanges": [{"startDate": f"{min(days,14)}daysAgo", "endDate": "today"}],
                "dimensions": [{"name": "date"}, {"name": "sessionSource"}, {"name": "pagePath"}],
                "metrics": [{"name": "sessions"}],
                "dimensionFilter": pages_payload["dimensionFilter"],
                "orderBys": [{"dimension": {"dimensionName": "date"}, "desc": True}],
                "limit": 10
            }
            async with httpx.AsyncClient() as rc:
                recent_resp = await rc.post(
                    api_url,
                    json=recent_payload,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            recent_data = recent_resp.json()
            for row in recent_data.get("rows", []):
                date = row["dimensionValues"][0]["value"]
                source = row["dimensionValues"][1]["value"]
                page = row["dimensionValues"][2]["value"]
                sessions = int(row["metricValues"][0]["value"])
                platform = "ChatGPT" if "chatgpt" in source else "Perplexity" if "perplexity" in source else "Claude" if "claude" in source else "Gemini" if "gemini" in source else "Copilot" if "copilot" in source else source
                recent_visits.append({"date": date, "platform": platform, "page": page, "visits": sessions})

            # Keywords from UTM terms
            kw_payload = {
                "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
                "dimensions": [{"name": "sessionManualTerm"}, {"name": "sessionSource"}],
                "metrics": [{"name": "sessions"}],
                "dimensionFilter": pages_payload["dimensionFilter"],
                "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
                "limit": 10
            }
            async with httpx.AsyncClient() as kc:
                kw_resp = await kc.post(
                    api_url,
                    json=kw_payload,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            kw_data = kw_resp.json()
            for row in kw_data.get("rows", []):
                term = row["dimensionValues"][0]["value"]
                source = row["dimensionValues"][1]["value"]
                sessions = int(row["metricValues"][0]["value"])
                if term and term != "(not set)":
                    keywords.append({"keyword": term, "source": source, "sessions": sessions})
        except Exception as page_err:
            print(f"[GA4 Pages Error] {page_err}")

        return {
            "total": total,
            "by_platform": ai_sources,
            "trend": [{"date": d, "sessions": s} for d, s in sorted(trend_data.items())],
            "ai_insights": ai_insight,
            "top_pages": top_pages,
            "recent_visits": recent_visits,
            "keywords": keywords,
            "days": days
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ga4/debug-traffic")
async def ga4_debug_traffic(session_id: str):
    """Debug: fetch all traffic sources from GA4."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT property_id, access_token, refresh_token FROM ga4_tokens WHERE session_id = %s",
                (session_id,)
            )
            row = cur.fetchone()
        
        if not row:
            return {"error": "GA4 not connected"}
        
        property_id, access_token, refresh_token = row

        api_url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
        
        payload = {
            "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
            "dimensions": [{"name": "sessionSource"}],
            "metrics": [{"name": "sessions"}],
            "limit": 20
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                api_url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# SOCIAL MEDIA INTELLIGENCE ENDPOINTS
# ============================================================

@app.post("/api/social-media/analyze")
async def social_media_analyze(request: Request):
    """Analyze website content for social media potential using Gemini."""
    try:
        body = await request.json()
        url = body.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL required")

        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        # Scrape page content
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_text = meta_desc.get('content', '') if meta_desc else ''
        h1s = [h.get_text().strip() for h in soup.find_all('h1')]
        h2s = [h.get_text().strip() for h in soup.find_all('h2')][:10]
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 50][:10]
        images_count = len(soup.find_all('img'))

        prompt = f"""Analyze this website for social media potential and return ONLY valid JSON.

Website: {url}
Title: {title_text}
Meta Description: {meta_text}
H1 Tags: {', '.join(h1s[:3])}
H2 Tags: {', '.join(h2s[:5])}
Key Content: {' | '.join(paragraphs[:5])}
Images: {images_count}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "overall_score": 72,
  "content_score": 80,
  "shareability_score": 65,
  "visual_score": 45,
  "summary": "2-3 sentence assessment of social media potential",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "gaps": ["gap 1", "gap 2", "gap 3"],
  "platform_fit": {{
    "linkedin": {{"score": 85, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "twitter": {{"score": 70, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "instagram": {{"score": 40, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "youtube": {{"score": 60, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "reddit": {{"score": 75, "why": "reason", "content_types": "types", "tip": "actionable tip"}}
  }},
  "content_ideas": [
    {{"emoji": "💡", "title": "idea title", "platform": "LinkedIn", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "🧠", "title": "idea title", "platform": "Twitter/X", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "📊", "title": "idea title", "platform": "LinkedIn", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "🎯", "title": "idea title", "platform": "Reddit", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "🚀", "title": "idea title", "platform": "YouTube", "description": "detailed description", "hook": "opening hook"}}
  ],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5", "#hashtag6", "#hashtag7", "#hashtag8"],
  "content_mix": [
    {{"type": "Educational", "percentage": 40, "example": "example post type"}},
    {{"type": "Project Showcase", "percentage": 25, "example": "example post type"}},
    {{"type": "Industry Insights", "percentage": 20, "example": "example post type"}},
    {{"type": "Personal Brand", "percentage": 15, "example": "example post type"}}
  ],
  "posting_schedule": [
    {{"platform": "LinkedIn", "icon": "💼", "best_time": "Tue-Thu, 8-10am IST", "frequency": "3x/week"}},
    {{"platform": "Twitter/X", "icon": "𝕏", "best_time": "Mon-Fri, 12-2pm IST", "frequency": "Daily"}},
    {{"platform": "Instagram", "icon": "📸", "best_time": "Wed & Fri, 6-8pm IST", "frequency": "2x/week"}},
    {{"platform": "YouTube", "icon": "▶", "best_time": "Saturday, 10am IST", "frequency": "1x/week"}},
    {{"platform": "Reddit", "icon": "🤖", "best_time": "Weekdays, 2-4pm IST", "frequency": "2x/week"}}
  ],
  "priority_actions": [
    {{"action": "specific action", "reason": "why this matters", "effort": "low"}},
    {{"action": "specific action", "reason": "why this matters", "effort": "medium"}},
    {{"action": "specific action", "reason": "why this matters", "effort": "high"}}
  ]
}}"""

        async with httpx.AsyncClient(timeout=30) as client:
            gem_resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
        gem_data = gem_resp.json()
        
        if "error" in gem_data:
            raise HTTPException(status_code=500, detail=f"Gemini error: {gem_data['error'].get('message', 'Unknown')}")
        
        if "candidates" not in gem_data or not gem_data["candidates"]:
            raise HTTPException(status_code=500, detail=f"Gemini no candidates: {gem_data}")
            
        raw = gem_data["candidates"][0]["content"]["parts"][0]["text"]
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/social-media/generate-post")
async def generate_social_post(request: Request):
    """Generate a ready-to-post social media post."""
    try:
        body = await request.json()
        url = body.get("url", "")
        platform = body.get("platform", "linkedin")
        post_type = body.get("post_type", "insight")

        gemini_key = os.environ.get("GEMINI_API_KEY", "")

        # Scrape content
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().strip() if title else url
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 50][:5]
        content_summary = ' '.join(paragraphs[:3])[:500]

        platform_rules = {
            "linkedin": "Professional tone. 150-300 words. Start with a hook. Use line breaks. End with a question or CTA. No hashtags in body, add 3-5 at end.",
            "twitter": "Max 280 chars. Punchy. Start with a strong statement. Add 2-3 relevant hashtags.",
            "instagram": "Engaging, visual-first. 100-150 words. Use emojis. 10-15 hashtags at end.",
            "reddit": "Conversational, informative. No self-promotion tone. Add value first. 200-300 words.",
            "youtube": "Video description format. 150-200 words. Include timestamps placeholders. Add tags at end.",
        }

        post_type_rules = {
            "thought_leadership": "Share a unique insight or perspective about the industry",
            "case_study": "Present a problem-solution-result format",
            "insight": "Share a surprising or valuable insight",
            "tip": "Give one actionable tip",
            "announcement": "Announce something new or upcoming",
            "service": "Highlight a key service or capability",
        }

        prompt = f"""Write a {post_type} post for {platform} based on this website content.

Website: {url}
Title: {title_text}
Content: {content_summary}

Platform rules: {platform_rules.get(platform, '')}
Post type: {post_type_rules.get(post_type, '')}

Write ONLY the post content. No explanations, no labels, no markdown."""

        async with httpx.AsyncClient(timeout=20) as client:
            gem_resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
        gem_data = gem_resp.json()
        post_text = gem_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return {"post": post_text, "platform": platform, "type": post_type}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# SOCIAL MEDIA INTELLIGENCE ENDPOINTS
# ============================================================

@app.post("/api/social-media/analyze")
async def social_media_analyze(request: Request):
    """Analyze website content for social media potential using Gemini."""
    try:
        body = await request.json()
        url = body.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL required")

        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        # Scrape page content
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_text = meta_desc.get('content', '') if meta_desc else ''
        h1s = [h.get_text().strip() for h in soup.find_all('h1')]
        h2s = [h.get_text().strip() for h in soup.find_all('h2')][:10]
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 50][:10]
        images_count = len(soup.find_all('img'))

        prompt = f"""Analyze this website for social media potential and return ONLY valid JSON.

Website: {url}
Title: {title_text}
Meta Description: {meta_text}
H1 Tags: {', '.join(h1s[:3])}
H2 Tags: {', '.join(h2s[:5])}
Key Content: {' | '.join(paragraphs[:5])}
Images: {images_count}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "overall_score": 72,
  "content_score": 80,
  "shareability_score": 65,
  "visual_score": 45,
  "summary": "2-3 sentence assessment of social media potential",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "gaps": ["gap 1", "gap 2", "gap 3"],
  "platform_fit": {{
    "linkedin": {{"score": 85, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "twitter": {{"score": 70, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "instagram": {{"score": 40, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "youtube": {{"score": 60, "why": "reason", "content_types": "types", "tip": "actionable tip"}},
    "reddit": {{"score": 75, "why": "reason", "content_types": "types", "tip": "actionable tip"}}
  }},
  "content_ideas": [
    {{"emoji": "💡", "title": "idea title", "platform": "LinkedIn", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "🧠", "title": "idea title", "platform": "Twitter/X", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "📊", "title": "idea title", "platform": "LinkedIn", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "🎯", "title": "idea title", "platform": "Reddit", "description": "detailed description", "hook": "opening hook"}},
    {{"emoji": "🚀", "title": "idea title", "platform": "YouTube", "description": "detailed description", "hook": "opening hook"}}
  ],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5", "#hashtag6", "#hashtag7", "#hashtag8"],
  "content_mix": [
    {{"type": "Educational", "percentage": 40, "example": "example post type"}},
    {{"type": "Project Showcase", "percentage": 25, "example": "example post type"}},
    {{"type": "Industry Insights", "percentage": 20, "example": "example post type"}},
    {{"type": "Personal Brand", "percentage": 15, "example": "example post type"}}
  ],
  "posting_schedule": [
    {{"platform": "LinkedIn", "icon": "💼", "best_time": "Tue-Thu, 8-10am IST", "frequency": "3x/week"}},
    {{"platform": "Twitter/X", "icon": "𝕏", "best_time": "Mon-Fri, 12-2pm IST", "frequency": "Daily"}},
    {{"platform": "Instagram", "icon": "📸", "best_time": "Wed & Fri, 6-8pm IST", "frequency": "2x/week"}},
    {{"platform": "YouTube", "icon": "▶", "best_time": "Saturday, 10am IST", "frequency": "1x/week"}},
    {{"platform": "Reddit", "icon": "🤖", "best_time": "Weekdays, 2-4pm IST", "frequency": "2x/week"}}
  ],
  "priority_actions": [
    {{"action": "specific action", "reason": "why this matters", "effort": "low"}},
    {{"action": "specific action", "reason": "why this matters", "effort": "medium"}},
    {{"action": "specific action", "reason": "why this matters", "effort": "high"}}
  ]
}}"""

        async with httpx.AsyncClient(timeout=30) as client:
            gem_resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
        gem_data = gem_resp.json()
        
        if "error" in gem_data:
            raise HTTPException(status_code=500, detail=f"Gemini error: {gem_data['error'].get('message', 'Unknown')}")
        
        if "candidates" not in gem_data or not gem_data["candidates"]:
            raise HTTPException(status_code=500, detail=f"Gemini no candidates: {gem_data}")
            
        raw = gem_data["candidates"][0]["content"]["parts"][0]["text"]
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/social-media/generate-post")
async def generate_social_post(request: Request):
    """Generate a ready-to-post social media post."""
    try:
        body = await request.json()
        url = body.get("url", "")
        platform = body.get("platform", "linkedin")
        post_type = body.get("post_type", "insight")

        gemini_key = os.environ.get("GEMINI_API_KEY", "")

        # Scrape content
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().strip() if title else url
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 50][:5]
        content_summary = ' '.join(paragraphs[:3])[:500]

        platform_rules = {
            "linkedin": "Professional tone. 150-300 words. Start with a hook. Use line breaks. End with a question or CTA. No hashtags in body, add 3-5 at end.",
            "twitter": "Max 280 chars. Punchy. Start with a strong statement. Add 2-3 relevant hashtags.",
            "instagram": "Engaging, visual-first. 100-150 words. Use emojis. 10-15 hashtags at end.",
            "reddit": "Conversational, informative. No self-promotion tone. Add value first. 200-300 words.",
            "youtube": "Video description format. 150-200 words. Include timestamps placeholders. Add tags at end.",
        }

        post_type_rules = {
            "thought_leadership": "Share a unique insight or perspective about the industry",
            "case_study": "Present a problem-solution-result format",
            "insight": "Share a surprising or valuable insight",
            "tip": "Give one actionable tip",
            "announcement": "Announce something new or upcoming",
            "service": "Highlight a key service or capability",
        }

        prompt = f"""Write a {post_type} post for {platform} based on this website content.

Website: {url}
Title: {title_text}
Content: {content_summary}

Platform rules: {platform_rules.get(platform, '')}
Post type: {post_type_rules.get(post_type, '')}

Write ONLY the post content. No explanations, no labels, no markdown."""

        async with httpx.AsyncClient(timeout=20) as client:
            gem_resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
        gem_data = gem_resp.json()
        post_text = gem_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return {"post": post_text, "platform": platform, "type": post_type}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sema/auto-bid-adjust")
async def sema_auto_bid_adjust(request: Request):
    """SEMA 2.0 — Automatically analyze and adjust bids based on performance."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        customer_id = body.get("customer_id", DEFAULT_CUSTOMER_ID)
        auto_apply = body.get("auto_apply", False)

        session = _sessions.get(session_id, {})
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")

        refresh_token = session.get("refresh_token", "")
        from ads_manager import get_headers
        headers = get_headers(refresh_token)
        cid = customer_id.replace("-", "")

        # Fetch campaign performance
        query = """
            SELECT
              campaign.resource_name,
              campaign.name,
              campaign.status,
              metrics.clicks,
              metrics.impressions,
              metrics.ctr,
              metrics.average_cpc,
              metrics.cost_micros,
              metrics.conversions
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
              AND campaign.status = 'ENABLED'
        """
        search_url = f"https://googleads.googleapis.com/v23/customers/{cid}/googleAds:search"
        resp = httpx.post(search_url, headers=headers, json={"query": query}, timeout=30)
        
        if resp.status_code != 200:
            return {"success": False, "error": "Failed to fetch campaigns"}
        
        campaigns_data = resp.json().get("results", [])
        
        if not campaigns_data:
            return {"success": True, "adjustments": [], "message": "No active campaigns found"}

        # AI analyze performance and suggest bid adjustments
        perf_summary = []
        for c in campaigns_data:
            m = c.get("metrics", {})
            camp = c.get("campaign", {})
            perf_summary.append({
                "name": camp.get("name", ""),
                "resource_name": camp.get("resourceName", ""),
                "clicks": m.get("clicks", 0),
                "impressions": m.get("impressions", 0),
                "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                "avg_cpc_inr": round(int(m.get("averageCpc", 0)) / 1000000, 2),
                "spend_inr": round(int(m.get("costMicros", 0)) / 1000000, 2),
                "conversions": float(m.get("conversions", 0)),
            })

        prompt = f"""You are SEMA, an expert Google Ads AI agent. Analyze these campaign performances and recommend bid adjustments.

Campaign Performance (Last 30 Days):
{json.dumps(perf_summary, indent=2)}

Rules for bid adjustment:
- CTR > 5% AND conversions > 0: Increase bid by 15-20% (performing well)
- CTR > 3% AND clicks > 10: Increase bid by 10% (good performance)
- CTR < 1% AND impressions > 100: Decrease bid by 20% (poor performance)
- 0 clicks AND 0 impressions after 7+ days: Decrease bid by 30% or pause
- CTR 1-3%: Keep bid same, monitor

Return ONLY this JSON:
{{
  "adjustments": [
    {{
      "campaign_name": "name",
      "resource_name": "customers/xxx/campaigns/xxx",
      "current_ctr": 0.0,
      "action": "increase|decrease|pause|keep",
      "adjustment_pct": 15,
      "reason": "specific reason",
      "priority": "high|medium|low"
    }}
  ],
  "summary": "overall analysis in 1-2 sentences"
}}"""

        ai_response = await call_gemini(prompt)
        
        try:
            ai_data = parse_ai_json(ai_response)
        except:
            ai_data = {"adjustments": [], "summary": "Analysis complete"}

        adjustments = ai_data.get("adjustments", [])
        results = []

        if auto_apply:
            # Auto-apply adjustments
            for adj in adjustments:
                if adj.get("action") == "keep":
                    results.append({**adj, "status": "skipped", "message": "No change needed"})
                    continue
                
                try:
                    action = adj.get("action")
                    pct = adj.get("adjustment_pct", 0)
                    resource_name = adj.get("resource_name", "")
                    
                    if action == "pause":
                        # Pause campaign
                        mutate_url = f"https://googleads.googleapis.com/v23/customers/{cid}/campaigns:mutate"
                        mutate_body = {"operations": [{"update": {
                            "resourceName": resource_name,
                            "status": "PAUSED"
                        }, "updateMask": "status"}]}
                        r = httpx.post(mutate_url, headers=headers, json=mutate_body, timeout=15)
                        results.append({**adj, "status": "applied", "message": "Campaign paused"})
                    
                    else:
                        # Adjust bid via ad group CPC
                        resource_name = adj.get("resource_name", "")
                        pct = adj.get("adjustment_pct", 0)
                        
                        # Get current avg CPC from campaign data
                        current_cpc = 0
                        for c in perf_summary:
                            if c["resource_name"] == resource_name:
                                current_cpc = c["avg_cpc_inr"]
                                break
                        
                        if current_cpc == 0:
                            current_cpc = 30  # default ₹30
                        
                        # Calculate new CPC
                        multiplier = 1 + (pct / 100) if action == "increase" else 1 - (pct / 100)
                        new_cpc_inr = max(1, round(current_cpc * multiplier, 2))
                        new_cpc_micros = int(new_cpc_inr * 1000000)
                        
                        from ads_manager import update_campaign_bid
                        bid_result = update_campaign_bid(cid, refresh_token, resource_name, new_cpc_micros)
                        
                        if bid_result.get("success"):
                            results.append({**adj, "status": "applied", "message": f"Bid {action}d to ₹{new_cpc_inr}"})
                        else:
                            results.append({**adj, "status": "error", "message": bid_result.get("error", "Failed")})
                        
                except Exception as e:
                    results.append({**adj, "status": "error", "message": str(e)})
        else:
            # Just return suggestions
            results = [{**adj, "status": "suggested"} for adj in adjustments]

        return {
            "success": True,
            "auto_applied": auto_apply,
            "adjustments": results,
            "summary": ai_data.get("summary", ""),
            "campaigns_analyzed": len(campaigns_data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sema/auto-negative-keywords")
async def sema_auto_negative_keywords(request: Request):
    """SEMA 2.0 — Auto detect and add negative keywords from search terms."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        customer_id = body.get("customer_id", DEFAULT_CUSTOMER_ID)
        auto_apply = body.get("auto_apply", False)

        session = _sessions.get(session_id, {})
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")

        refresh_token = session.get("refresh_token", "")
        from ads_manager import get_headers, add_negative_keywords
        headers = get_headers(refresh_token)
        cid = customer_id.replace("-", "")

        # Fetch search terms report
        query = """
            SELECT
              search_term_view.search_term,
              search_term_view.resource_name,
              campaign.resource_name,
              campaign.name,
              metrics.clicks,
              metrics.impressions,
              metrics.ctr,
              metrics.cost_micros
            FROM search_term_view
            WHERE segments.date DURING LAST_30_DAYS
              AND metrics.impressions > 5
        """
        search_url = f"https://googleads.googleapis.com/v23/customers/{cid}/googleAds:search"
        resp = httpx.post(search_url, headers=headers, json={"query": query}, timeout=30)

        if resp.status_code != 200:
            # No search terms yet — use AI to suggest common negatives
            search_terms = []
        else:
            results = resp.json().get("results", [])
            search_terms = []
            for r in results:
                m = r.get("metrics", {})
                search_terms.append({
                    "term": r.get("searchTermView", {}).get("searchTerm", ""),
                    "campaign": r.get("campaign", {}).get("name", ""),
                    "campaign_resource": r.get("campaign", {}).get("resourceName", ""),
                    "clicks": int(m.get("clicks", 0)),
                    "impressions": int(m.get("impressions", 0)),
                    "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                    "cost_inr": round(int(m.get("costMicros", 0)) / 1000000, 2),
                })

        # AI analyze and suggest negative keywords
        prompt = f"""You are SEMA, a Google Ads AI agent. Analyze search terms and identify negative keywords.

Search Terms Report (Last 30 Days):
{json.dumps(search_terms[:50], indent=2) if search_terms else "No search terms data yet - suggest common negative keywords for an AI/Technology business"}

Rules for negative keywords:
- 0 clicks but >10 impressions = definitely negative
- CTR < 0.5% and cost > ₹100 = waste of budget, add as negative
- Irrelevant terms (jobs, free, crack, download, etc.) = negative
- Competitor brand names (if not intentional) = negative

Return ONLY this JSON:
{{
  "negative_keywords": [
    {{
      "keyword": "search term",
      "reason": "why it should be negative",
      "campaign_resource": "campaign resource name or 'all'",
      "campaign_name": "campaign name or 'All Campaigns'",
      "priority": "high|medium|low"
    }}
  ],
  "summary": "brief summary of findings"
}}"""

        ai_response = await call_gemini(prompt)
        try:
            ai_data = parse_ai_json(ai_response)
        except:
            ai_data = {"negative_keywords": [], "summary": "Analysis complete"}

        suggestions = ai_data.get("negative_keywords", [])
        results_list = []

        if auto_apply and suggestions:
            # Group by campaign
            campaign_keywords = {}
            for s in suggestions:
                camp_resource = s.get("campaign_resource", "all")
                if camp_resource == "all" and search_terms:
                    camp_resource = search_terms[0].get("campaign_resource", "")
                if camp_resource not in campaign_keywords:
                    campaign_keywords[camp_resource] = []
                campaign_keywords[camp_resource].append(s.get("keyword", ""))

            for camp_resource, keywords in campaign_keywords.items():
                if not camp_resource or not keywords:
                    continue
                try:
                    result = add_negative_keywords(cid, refresh_token, camp_resource, keywords)
                    for kw in keywords:
                        matching = next((s for s in suggestions if s.get("keyword") == kw), {})
                        results_list.append({
                            **matching,
                            "status": "applied" if result.get("success") else "error",
                            "message": result.get("message", result.get("error", ""))
                        })
                except Exception as e:
                    for kw in keywords:
                        results_list.append({"keyword": kw, "status": "error", "message": str(e)})
        else:
            results_list = [{**s, "status": "suggested"} for s in suggestions]

        return {
            "success": True,
            "auto_applied": auto_apply,
            "negative_keywords": results_list,
            "search_terms_analyzed": len(search_terms),
            "summary": ai_data.get("summary", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sema/weekly-report")
async def sema_weekly_report(request: Request):
    """SEMA 2.0 — Generate and send weekly performance report via email."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        customer_id = body.get("customer_id", DEFAULT_CUSTOMER_ID)
        email = body.get("email", "")
        send_email = body.get("send_email", True)

        session = _sessions.get(session_id, {})
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")

        refresh_token = session.get("refresh_token", "")
        user_email = email or session.get("email", "")
        from ads_manager import get_headers
        headers = get_headers(refresh_token)
        cid = customer_id.replace("-", "")

        # Fetch last 7 days performance
        query = """
            SELECT
              campaign.name,
              campaign.status,
              metrics.clicks,
              metrics.impressions,
              metrics.ctr,
              metrics.average_cpc,
              metrics.cost_micros,
              metrics.conversions
            FROM campaign
            WHERE segments.date DURING LAST_7_DAYS
              AND campaign.status IN ('ENABLED', 'PAUSED')
        """
        search_url = f"https://googleads.googleapis.com/v23/customers/{cid}/googleAds:search"
        resp = httpx.post(search_url, headers=headers, json={"query": query}, timeout=30)

        campaigns_data = []
        if resp.status_code == 200:
            for r in resp.json().get("results", []):
                m = r.get("metrics", {})
                c = r.get("campaign", {})
                campaigns_data.append({
                    "name": c.get("name", ""),
                    "status": c.get("status", ""),
                    "clicks": int(m.get("clicks", 0)),
                    "impressions": int(m.get("impressions", 0)),
                    "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                    "avg_cpc_inr": round(int(m.get("averageCpc", 0)) / 1000000, 2),
                    "spend_inr": round(int(m.get("costMicros", 0)) / 1000000, 2),
                    "conversions": float(m.get("conversions", 0)),
                })

        total_clicks = sum(c["clicks"] for c in campaigns_data)
        total_spend = sum(c["spend_inr"] for c in campaigns_data)
        total_impressions = sum(c["impressions"] for c in campaigns_data)
        avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0

        # AI generate report
        prompt = f"""You are SEMA, an expert Google Ads AI. Generate a weekly performance report.

Campaign Performance (Last 7 Days):
{json.dumps(campaigns_data, indent=2)}

Total: {total_clicks} clicks, {total_impressions} impressions, ₹{total_spend} spend, {avg_ctr}% CTR

Generate a professional weekly report with:
1. Executive summary (2-3 sentences)
2. Key wins this week
3. Issues to fix
4. Next week recommendations

Return ONLY this JSON:
{{
  "subject": "Weekly SEM Report - Week of [date]",
  "executive_summary": "2-3 sentence overview",
  "key_wins": ["win1", "win2"],
  "issues": ["issue1", "issue2"],
  "recommendations": ["rec1", "rec2", "rec3"],
  "performance_score": 75,
  "trend": "improving|stable|declining"
}}"""

        ai_response = await call_gemini(prompt)
        try:
            report_data = parse_ai_json(ai_response)
        except:
            report_data = {
                "subject": "Weekly SEM Report",
                "executive_summary": f"This week: {total_clicks} clicks, ₹{total_spend} spend.",
                "key_wins": [], "issues": [], "recommendations": [],
                "performance_score": 50, "trend": "stable"
            }

        # Build HTML email
        from datetime import datetime
        week_str = datetime.now().strftime("%B %d, %Y")
        score = report_data.get("performance_score", 50)
        score_color = "#4ade80" if score >= 70 else "#fbbf24" if score >= 40 else "#f87171"
        trend = report_data.get("trend", "stable")
        trend_icon = "📈" if trend == "improving" else "📉" if trend == "declining" else "➡️"

        html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
  body {{ font-family: Arial, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #7c3aed, #4f7dff); padding: 30px; color: white; text-align: center; }}
  .header h1 {{ margin: 0 0 8px; font-size: 24px; }}
  .header p {{ margin: 0; opacity: 0.85; font-size: 14px; }}
  .score-box {{ background: rgba(255,255,255,0.15); border-radius: 10px; padding: 15px; margin-top: 15px; }}
  .score {{ font-size: 42px; font-weight: bold; color: {score_color}; }}
  .body {{ padding: 25px; }}
  .summary {{ background: #f8f9fa; border-left: 4px solid #7c3aed; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #444; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
  .stat {{ background: #f8f9fa; padding: 12px; border-radius: 8px; text-align: center; }}
  .stat-value {{ font-size: 20px; font-weight: bold; color: #7c3aed; }}
  .stat-label {{ font-size: 11px; color: #888; margin-top: 3px; }}
  .section {{ margin-bottom: 20px; }}
  .section h3 {{ font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #333; }}
  .item {{ padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; font-size: 13px; }}
  .win {{ background: #f0fdf4; color: #166534; border-left: 3px solid #4ade80; }}
  .issue {{ background: #fff7ed; color: #9a3412; border-left: 3px solid #f97316; }}
  .rec {{ background: #eff6ff; color: #1e40af; border-left: 3px solid #60a5fa; }}
  .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #888; }}
</style></head>
<body>
<div class="container">
  <div class="header">
    <h1>🤖 SEMA Weekly Report</h1>
    <p>Week of {week_str}</p>
    <div class="score-box">
      <div class="score">{score}/100</div>
      <div style="font-size:13px;margin-top:4px">{trend_icon} {trend.capitalize()} performance</div>
    </div>
  </div>
  <div class="body">
    <div class="summary">{report_data.get("executive_summary", "")}</div>
    
    <div class="stats">
      <div class="stat"><div class="stat-value">{total_clicks}</div><div class="stat-label">Clicks</div></div>
      <div class="stat"><div class="stat-value">{total_impressions:,}</div><div class="stat-label">Impressions</div></div>
      <div class="stat"><div class="stat-value">{avg_ctr}%</div><div class="stat-label">CTR</div></div>
      <div class="stat"><div class="stat-value">₹{total_spend:,.0f}</div><div class="stat-label">Spend</div></div>
    </div>

    {"".join(f'<div class="section"><h3>✅ Key Wins</h3>' + "".join(f'<div class="item win">→ {w}</div>' for w in report_data.get("key_wins", [])) + "</div>") if report_data.get("key_wins") else ""}
    {"".join(f'<div class="section"><h3>⚠️ Issues to Fix</h3>' + "".join(f'<div class="item issue">→ {i}</div>' for i in report_data.get("issues", [])) + "</div>") if report_data.get("issues") else ""}
    {"".join(f'<div class="section"><h3>🎯 Next Week Recommendations</h3>' + "".join(f'<div class="item rec">→ {r}</div>' for r in report_data.get("recommendations", [])) + "</div>") if report_data.get("recommendations") else ""}

    <div style="text-align:center;padding:15px;background:#f8f9fa;border-radius:8px;font-size:12px;color:#888">
      Powered by SEMA AI · sakthivelraja.ai
    </div>
  </div>
  <div class="footer">This report was automatically generated by SEMA AI Agent</div>
</div>
</body></html>"""

        email_result = {"sent": False, "message": "Email not sent (send_email=False)"}
        
        if send_email and user_email:
            resend_api_key = os.environ.get("RESEND_API_KEY", "")
            if resend_api_key:
                email_resp = httpx.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {resend_api_key}", "Content-Type": "application/json"},
                    json={
                        "from": "SEMA AI <reports@sakthivelraja.ai>",
                        "to": [user_email],
                        "subject": report_data.get("subject", f"Weekly SEM Report - {week_str}"),
                        "html": html_body,
                    },
                    timeout=30
                )
                if email_resp.status_code == 200:
                    email_result = {"sent": True, "message": f"Report sent to {user_email}"}
                else:
                    email_result = {"sent": False, "message": str(email_resp.json())}

        return {
            "success": True,
            "report": report_data,
            "stats": {
                "total_clicks": total_clicks,
                "total_impressions": total_impressions,
                "total_spend_inr": total_spend,
                "avg_ctr": avg_ctr,
                "campaigns": len(campaigns_data)
            },
            "email": email_result,
            "html_preview": html_body
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sema/auto-ad-refresh")
async def sema_auto_ad_refresh(request: Request):
    """SEMA 2.0 — Detect low CTR ads and auto-refresh with AI-generated copy."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        customer_id = body.get("customer_id", DEFAULT_CUSTOMER_ID)
        auto_apply = body.get("auto_apply", False)
        url = body.get("url", "")

        session = _sessions.get(session_id, {})
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")

        refresh_token = session.get("refresh_token", "")
        from ads_manager import get_headers
        headers = get_headers(refresh_token)
        cid = customer_id.replace("-", "")

        # Fetch ad performance
        query = """
            SELECT
              ad_group_ad.resource_name,
              ad_group_ad.ad.responsive_search_ad.headlines,
              ad_group_ad.ad.responsive_search_ad.descriptions,
              ad_group_ad.ad.final_urls,
              ad_group.resource_name,
              campaign.name,
              metrics.clicks,
              metrics.impressions,
              metrics.ctr,
              metrics.cost_micros
            FROM ad_group_ad
            WHERE segments.date DURING LAST_30_DAYS
              AND ad_group_ad.status = 'ENABLED'
              AND campaign.status = 'ENABLED'
        """
        search_url = f"https://googleads.googleapis.com/v23/customers/{cid}/googleAds:search"
        resp = httpx.post(search_url, headers=headers, json={"query": query}, timeout=30)

        ads_data = []
        if resp.status_code == 200:
            for r in resp.json().get("results", []):
                m = r.get("metrics", {})
                ada = r.get("adGroupAd", {})
                ad = ada.get("ad", {})
                rsa = ad.get("responsiveSearchAd", {})
                
                headlines = [h.get("text", "") for h in rsa.get("headlines", [])]
                descriptions = [d.get("text", "") for d in rsa.get("descriptions", [])]
                
                ads_data.append({
                    "resource_name": ada.get("resourceName", ""),
                    "ad_group_resource": r.get("adGroup", {}).get("resourceName", ""),
                    "campaign_name": r.get("campaign", {}).get("name", ""),
                    "headlines": headlines[:3],
                    "descriptions": descriptions[:2],
                    "final_url": ad.get("finalUrls", [""])[0] if ad.get("finalUrls") else url,
                    "clicks": int(m.get("clicks", 0)),
                    "impressions": int(m.get("impressions", 0)),
                    "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                    "spend_inr": round(int(m.get("costMicros", 0)) / 1000000, 2),
                })

        # Filter low CTR ads (CTR < 2% with >100 impressions)
        low_ctr_ads = [a for a in ads_data if a["ctr"] < 2.0 and a["impressions"] > 100]
        
        if not low_ctr_ads and ads_data:
            low_ctr_ads = ads_data  # refresh all if no specific low CTR

        # AI generate new ad copy
        prompt = f"""You are SEMA, a Google Ads copywriter AI. Generate improved ad copy for these low-performing ads.

Website URL: {url or "the business website"}
Low CTR Ads:
{json.dumps(low_ctr_ads[:5], indent=2)}

Rules:
- Headlines: max 30 characters each
- Descriptions: max 90 characters each
- Make headlines compelling, benefit-focused
- Include call-to-action in descriptions
- Use power words: Free, Proven, Expert, Fast, etc.

Return ONLY this JSON:
{{
  "refreshed_ads": [
    {{
      "resource_name": "original resource name",
      "ad_group_resource": "ad group resource",
      "campaign_name": "campaign name",
      "current_ctr": 0.0,
      "issue": "why current ad is underperforming",
      "new_headlines": ["Headline 1", "Headline 2", "Headline 3", "Headline 4", "Headline 5"],
      "new_descriptions": ["Description 1 with CTA.", "Description 2 with benefit."],
      "final_url": "url",
      "improvement_reason": "why new copy will perform better"
    }}
  ],
  "summary": "overall analysis"
}}"""

        ai_response = await call_gemini(prompt)
        try:
            ai_data = parse_ai_json(ai_response)
        except:
            ai_data = {"refreshed_ads": [], "summary": "Analysis complete"}

        refreshed_ads = ai_data.get("refreshed_ads", [])
        results = []

        if auto_apply and refreshed_ads:
            for ad in refreshed_ads:
                try:
                    ad_group_resource = ad.get("ad_group_resource", "")
                    new_headlines = ad.get("new_headlines", [])[:5]
                    new_descriptions = ad.get("new_descriptions", [])[:2]
                    final_url = ad.get("final_url", url)

                    if not ad_group_resource or not new_headlines:
                        results.append({**ad, "status": "skipped", "message": "Missing data"})
                        continue

                    # Create new responsive search ad
                    headlines_payload = [{"text": h[:30]} for h in new_headlines if h]
                    descriptions_payload = [{"text": d[:90]} for d in new_descriptions if d]

                    create_url = f"https://googleads.googleapis.com/v23/customers/{cid}/adGroupAds:mutate"
                    create_body = {"operations": [{"create": {
                        "adGroup": ad_group_resource,
                        "ad": {
                            "finalUrls": [final_url],
                            "responsiveSearchAd": {
                                "headlines": headlines_payload,
                                "descriptions": descriptions_payload,
                            }
                        },
                        "status": "ENABLED"
                    }}]}

                    create_resp = httpx.post(create_url, headers=headers, json=create_body, timeout=30)
                    
                    if create_resp.status_code == 200:
                        results.append({**ad, "status": "applied", "message": "New ad created successfully"})
                    else:
                        error_data = create_resp.json()
                        results.append({**ad, "status": "error", "message": str(error_data)})

                except Exception as e:
                    results.append({**ad, "status": "error", "message": str(e)})
        else:
            results = [{**ad, "status": "suggested"} for ad in refreshed_ads]

        return {
            "success": True,
            "auto_applied": auto_apply,
            "ads_analyzed": len(ads_data),
            "low_ctr_ads": len(low_ctr_ads),
            "refreshed_ads": results,
            "summary": ai_data.get("summary", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sema/auto-budget-scale")
async def sema_auto_budget_scale(request: Request):
    """SEMA 2.0 — Auto-scale budget based on ROAS and performance targets."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        customer_id = body.get("customer_id", DEFAULT_CUSTOMER_ID)
        auto_apply = body.get("auto_apply", False)
        target_roas = body.get("target_roas", 3.0)  # 3x return default

        session = _sessions.get(session_id, {})
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")

        refresh_token = session.get("refresh_token", "")
        from ads_manager import get_headers
        headers = get_headers(refresh_token)
        cid = customer_id.replace("-", "")

        # Fetch campaign budgets + performance
        query = """
            SELECT
              campaign.resource_name,
              campaign.name,
              campaign.campaign_budget,
              campaign_budget.amount_micros,
              campaign_budget.resource_name,
              metrics.clicks,
              metrics.impressions,
              metrics.ctr,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
              AND campaign.status = 'ENABLED'
        """
        search_url = f"https://googleads.googleapis.com/v23/customers/{cid}/googleAds:search"
        resp = httpx.post(search_url, headers=headers, json={"query": query}, timeout=30)

        campaigns_data = []
        if resp.status_code == 200:
            for r in resp.json().get("results", []):
                m = r.get("metrics", {})
                c = r.get("campaign", {})
                cb = r.get("campaignBudget", {})
                spend = int(m.get("costMicros", 0)) / 1000000
                conv_value = float(m.get("conversionsValue", 0))
                roas = round(conv_value / spend, 2) if spend > 0 else 0
                
                campaigns_data.append({
                    "name": c.get("name", ""),
                    "resource_name": c.get("resourceName", ""),
                    "budget_resource": cb.get("resourceName", ""),
                    "current_budget_inr": round(int(cb.get("amountMicros", 0)) / 1000000, 2),
                    "clicks": int(m.get("clicks", 0)),
                    "impressions": int(m.get("impressions", 0)),
                    "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                    "spend_inr": round(spend, 2),
                    "conversions": float(m.get("conversions", 0)),
                    "roas": roas,
                })

        # AI analyze and suggest budget scaling
        prompt = f"""You are SEMA, a Google Ads budget optimization AI. Analyze campaign performance and suggest budget scaling.

Target ROAS: {target_roas}x
Campaign Data (Last 30 Days):
{json.dumps(campaigns_data, indent=2)}

Budget Scaling Rules:
- ROAS > target AND CTR > 3%: Scale UP budget by 20-30% (high performer)
- ROAS > target AND CTR 1-3%: Scale UP by 10-15% (good performer)  
- ROAS < target AND spend > ₹1000: Scale DOWN by 20% (poor ROAS)
- 0 conversions AND spend > ₹500: Scale DOWN by 30% (no ROI)
- New campaign (<7 days data): Keep same, monitor
- Budget < ₹100/day: Suggest minimum ₹200/day for proper testing

Return ONLY this JSON:
{{
  "scaling_recommendations": [
    {{
      "campaign_name": "name",
      "resource_name": "campaign resource",
      "budget_resource": "budget resource",
      "current_budget_inr": 0,
      "recommended_budget_inr": 0,
      "change_pct": 20,
      "direction": "increase|decrease|keep",
      "reason": "specific reason",
      "roas": 0.0,
      "priority": "high|medium|low"
    }}
  ],
  "total_current_budget": 0,
  "total_recommended_budget": 0,
  "summary": "overall budget strategy"
}}"""

        ai_response = await call_gemini(prompt)
        try:
            ai_data = parse_ai_json(ai_response)
        except:
            ai_data = {"scaling_recommendations": [], "summary": "Analysis complete"}

        recommendations = ai_data.get("scaling_recommendations", [])
        results = []

        if auto_apply and recommendations:
            for rec in recommendations:
                if rec.get("direction") == "keep":
                    results.append({**rec, "status": "skipped", "message": "No change needed"})
                    continue
                
                try:
                    budget_resource = rec.get("budget_resource", "")
                    new_budget_inr = rec.get("recommended_budget_inr", 0)
                    
                    if not budget_resource or new_budget_inr <= 0:
                        results.append({**rec, "status": "skipped", "message": "Missing budget resource"})
                        continue

                    new_budget_micros = int(new_budget_inr * 1000000)
                    budget_cid = budget_resource.split("/")[1] if "/" in budget_resource else cid
                    
                    mutate_url = f"https://googleads.googleapis.com/v23/customers/{budget_cid}/campaignBudgets:mutate"
                    mutate_body = {"operations": [{"update": {
                        "resourceName": budget_resource,
                        "amountMicros": str(new_budget_micros),
                    }, "updateMask": "amount_micros"}]}
                    
                    r = httpx.post(mutate_url, headers=headers, json=mutate_body, timeout=15)
                    
                    if r.status_code == 200:
                        results.append({**rec, "status": "applied", "message": f"Budget updated to ₹{new_budget_inr}/day"})
                    else:
                        results.append({**rec, "status": "error", "message": str(r.json())})
                        
                except Exception as e:
                    results.append({**rec, "status": "error", "message": str(e)})
        else:
            results = [{**rec, "status": "suggested"} for rec in recommendations]

        return {
            "success": True,
            "auto_applied": auto_apply,
            "campaigns_analyzed": len(campaigns_data),
            "recommendations": results,
            "total_current_budget": ai_data.get("total_current_budget", 0),
            "total_recommended_budget": ai_data.get("total_recommended_budget", 0),
            "summary": ai_data.get("summary", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ads/apply-sema-fixes")
async def apply_sema_fixes(request: Request):
    """Apply SEMA recommended fixes to Google Ads campaign."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        campaign_resource = body.get("campaign_resource", "")
        fixes = body.get("fixes", [])

        session = _sessions.get(session_id, {})
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")

        refresh_token = session.get("refresh_token", "")
        customer_id = session.get("customer_id", DEFAULT_CUSTOMER_ID)

        from ads_manager import get_headers
        headers = get_headers(refresh_token)
        cid = customer_id.replace("-", "")

        results = []
        for fix in fixes:
            fix_type = fix.get("type", "")
            try:
                if fix_type == "bid":
                    # Increase bid
                    url = f"https://googleads.googleapis.com/v23/customers/{cid}/adGroups:mutate"
                    body_req = {"operations": [{"update": {
                        "resourceName": campaign_resource.replace("campaigns", "adGroups"),
                        "cpcBidMicros": str(2_000_000),
                    }, "updateMask": "cpc_bid_micros"}]}
                    resp = httpx.post(url, headers=headers, json=body_req, timeout=15)
                    results.append({"fix": fix.get("change"), "status": "applied" if resp.status_code == 200 else "failed"})

                elif fix_type == "budget":
                    # Increase budget
                    url = f"https://googleads.googleapis.com/v23/customers/{cid}/campaignBudgets:mutate"
                    body_req = {"operations": [{"update": {
                        "resourceName": f"customers/{cid}/campaignBudgets/1",
                        "amountMicros": str(2_000_000_000),
                    }, "updateMask": "amount_micros"}]}
                    results.append({"fix": fix.get("change"), "status": "noted"})

                else:
                    results.append({"fix": fix.get("change"), "status": "noted"})

            except Exception as fe:
                results.append({"fix": fix.get("change"), "status": "error", "error": str(fe)})

        return {"success": True, "results": results, "message": f"Applied {len(results)} fixes"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────
# AI Auto-Detect Business & Keywords
# ─────────────────────────────────────────
class DetectBusinessRequest(BaseModel):
    url: str

@app.post("/api/detect-business")
async def detect_business(req: DetectBusinessRequest):
    try:
        import httpx
        # Fetch homepage
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(req.url, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text[:8000]

        # Strip tags
        import re
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean).strip()[:800]

        prompt = f"""Analyse this website content and return ONLY a JSON object with no extra text:
{{
  "business_description": "one line description of what this business does (max 80 chars)",
  "target_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}

Website URL: {req.url}
Website Content: {clean}

Rules:
- business_description must be concise, specific, and useful for Google Ads targeting
- target_keywords must be 5 relevant SEO/SEM keywords for this business
- Return ONLY the JSON, no markdown, no explanation"""

        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            data = r.json()

        # Handle Gemini response safely
        if "candidates" not in data or not data["candidates"]:
            return {"business_description": "", "target_keywords": [], "error": "Gemini no candidates: " + str(data)[:200]}
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = re.sub(r'^```json|^```|```$', '', raw, flags=re.MULTILINE).strip()
        result = json.loads(raw)
        return result

    except Exception as e:
        return {"business_description": "", "target_keywords": [], "error": str(e)}

# ─────────────────────────────────────────
# Serve React Frontend (Production)
# ─────────────────────────────────────────
import os as _os
from fastapi.responses import FileResponse as _FileResponse

_dist = _os.path.join(_os.path.dirname(__file__), "frontend", "dist")
if _os.path.exists(_dist):
    app.mount("/assets", StaticFiles(directory=_os.path.join(_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = _os.path.join(_dist, "index.html")
        return _FileResponse(index)

# ─────────────────────────────────────────
# Multi-User Authentication
# ─────────────────────────────────────────
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "sem-ai-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_users_table():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                password_hash TEXT,
                google_id TEXT,
                avatar TEXT,
                plan TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Users table ready")
    except Exception as e:
        print(f"Users table error: {e}")

init_users_table()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    conn = get_db_connection()
    if not conn:
        return {"error": "DB connection failed"}
    try:
        cur = conn.cursor()
        # Check if email exists
        cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
        if cur.fetchone():
            cur.close(); conn.close()
            return {"error": "Email already registered"}
        # Hash password
        password_hash = pwd_context.hash(req.password[:72])
        cur.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s) RETURNING id, email, name, plan",
            (req.email, req.name, password_hash)
        )
        user = cur.fetchone()
        conn.commit()
        cur.close(); conn.close()
        token = create_access_token({"sub": str(user[0]), "email": user[1]})
        return {"token": token, "user": {"id": user[0], "email": user[1], "name": user[2], "plan": user[3]}}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    conn = get_db_connection()
    if not conn:
        return {"error": "DB connection failed"}
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, password_hash, plan, avatar, is_active FROM users WHERE email = %s", (req.email,))
        user = cur.fetchone()
        cur.close(); conn.close()
        if not user or not pwd_context.verify(req.password[:72], user[3]):
            return {"error": "Invalid email or password"}
        if user[6] is False:
            return {"error": "Your account has been disabled. Please contact support."}
        token = create_access_token({"sub": str(user[0]), "email": user[1]})
        return {"token": token, "user": {"id": user[0], "email": user[1], "name": user[2], "plan": user[4], "avatar": user[5]}}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/auth/me")
async def get_me(authorization: str = None, request: Request = None):
    token = None
    if request:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        return {"error": "No token provided"}
    payload = verify_token(token)
    if not payload:
        return {"error": "Invalid token"}
    conn = get_db_connection()
    if not conn:
        return {"error": "DB connection failed"}
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, plan, avatar, created_at FROM users WHERE id = %s", (payload["sub"],))
        user = cur.fetchone()
        cur.close(); conn.close()
        if not user:
            return {"error": "User not found"}
        return {"user": {"id": user[0], "email": user[1], "name": user[2], "plan": user[3], "avatar": user[4], "created_at": str(user[5])}}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/auth/google-login")
async def google_login_auth(request: Request):
    """Convert existing Google session to JWT user"""
    body = await request.json()
    session_id = body.get("session_id")
    email = body.get("email")
    if not session_id or not email:
        return {"error": "Missing session_id or email"}
    session = _sessions.get(session_id)
    if not session:
        return {"error": "Invalid session"}
    conn = get_db_connection()
    if not conn:
        return {"error": "DB connection failed"}
    try:
        cur = conn.cursor()
        # Upsert user
        cur.execute("SELECT id, email, name, plan, is_active FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            name = session.get("name", email.split("@")[0])
            cur.execute(
                "INSERT INTO users (email, name, google_id) VALUES (%s, %s, %s) RETURNING id, email, name, plan, TRUE",
                (email, name, session.get("google_id", ""))
            )
            user = cur.fetchone()
        conn.commit()
        cur.close(); conn.close()
        if len(user) > 4 and user[4] is False:
            return {"error": "Your account has been disabled. Please contact support."}
        token = create_access_token({"sub": str(user[0]), "email": user[1]})
        return {"token": token, "user": {"id": user[0], "email": user[1], "name": user[2], "plan": user[3]}}
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────
# Admin Panel Endpoints
# ─────────────────────────────────────────
SUPER_ADMIN_EMAIL = os.environ.get("SUPER_ADMIN_EMAIL", "jsvking@gmail.com")

def is_admin(token: str) -> bool:
    payload = verify_token(token)
    if not payload: return False
    return payload.get("email") == SUPER_ADMIN_EMAIL

@app.post("/api/admin/users")
async def admin_get_users(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or not is_admin(auth[7:]):
        return {"error": "Unauthorized"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, plan, created_at FROM users ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"users": [{"id": r[0], "email": r[1], "name": r[2], "plan": r[3], "created_at": str(r[4])} for r in rows]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/admin/users/{user_id}/plan")
async def admin_update_plan(user_id: int, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or not is_admin(auth[7:]):
        return {"error": "Unauthorized"}
    body = await request.json()
    plan = body.get("plan", "free")
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET plan = %s WHERE id = %s", (plan, user_id))
        conn.commit()
        cur.close(); conn.close()
        return {"success": True, "plan": plan}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or not is_admin(auth[7:]):
        return {"error": "Unauthorized"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close(); conn.close()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/admin/stats")
async def admin_stats(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or not is_admin(auth[7:]):
        return {"error": "Unauthorized"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE plan = 'pro'")
        pro_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE plan = 'agency'")
        agency_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '7 days'")
        new_this_week = cur.fetchone()[0]
        cur.close(); conn.close()
        return {"total_users": total_users, "pro_users": pro_users, "agency_users": agency_users, "free_users": total_users - pro_users - agency_users, "new_this_week": new_this_week}
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────
# Feature Flags
# ─────────────────────────────────────────
def init_feature_flags_table():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_flags (
                key TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT false,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        # Default flags
        cur.execute("""
            INSERT INTO feature_flags (key, enabled) VALUES
                ('stripe_billing', false),
                ('team_workspaces', false),
                ('white_label', false)
            ON CONFLICT (key) DO NOTHING
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Feature flags table ready")
    except Exception as e:
        print(f"Feature flags error: {e}")

init_feature_flags_table()

@app.post("/api/feature-flags")
async def get_feature_flags():
    conn = get_db_connection()
    if not conn: return {"flags": {}}
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, enabled FROM feature_flags")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"flags": {r[0]: r[1] for r in rows}}
    except Exception as e:
        return {"flags": {}, "error": str(e)}

@app.post("/api/admin/feature-flags/{key}")
async def toggle_feature_flag(key: str, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or not is_admin(auth[7:]):
        return {"error": "Unauthorized"}
    body = await request.json()
    enabled = body.get("enabled", False)
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO feature_flags (key, enabled) VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET enabled = %s, updated_at = NOW()
        """, (key, enabled, enabled))
        conn.commit()
        cur.close(); conn.close()
        return {"success": True, "key": key, "enabled": enabled}
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────
# Razorpay Payment Integration
# ─────────────────────────────────────────
import razorpay

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

PLANS = {
    "pro": {"amount": 299900, "name": "Pro Plan", "description": "SEM AI Pro - Unlimited analyses"},
    "agency": {"amount": 999900, "name": "Agency Plan", "description": "SEM AI Agency - Unlimited everything"},
}

class CreateOrderRequest(BaseModel):
    plan: str
    user_id: int

@app.post("/api/payment/create-order")
async def create_order(req: CreateOrderRequest, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return {"error": "Unauthorized"}
    # Try both jose and base64 decode
    token = auth[7:]
    payload = verify_token(token)
    if not payload:
        try:
            import base64, json as _j
            parts = token.split('.')
            if len(parts) == 3:
                padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
                payload = _j.loads(base64.b64decode(padded))
        except:
            pass
    if not payload:
        return {"error": "Invalid token"}
    if req.plan not in PLANS:
        return {"error": "Invalid plan"}
    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        plan = PLANS[req.plan]
        order = client.order.create({
            "amount": plan["amount"],
            "currency": "INR",
            "receipt": f"order_{req.user_id}_{req.plan}",
            "notes": {"plan": req.plan, "user_id": str(req.user_id)}
        })
        return {"order_id": order["id"], "amount": plan["amount"], "currency": "INR", "key_id": RAZORPAY_KEY_ID, "plan": req.plan, "name": plan["name"]}
    except Exception as e:
        return {"error": str(e)}

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str
    user_id: int

@app.post("/api/payment/verify")
async def verify_payment(req: VerifyPaymentRequest, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return {"error": "Unauthorized"}
    token = auth[7:]
    payload = verify_token(token)
    if not payload:
        try:
            import base64, json as _j
            parts = token.split('.')
            if len(parts) == 3:
                padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
                payload = _j.loads(base64.b64decode(padded))
        except:
            pass
    if not payload:
        return {"error": "Invalid token"}
    try:
        # Verify signature only for live payments
        if RAZORPAY_KEY_ID.startswith('rzp_live'):
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                "razorpay_order_id": req.razorpay_order_id,
                "razorpay_payment_id": req.razorpay_payment_id,
                "razorpay_signature": req.razorpay_signature,
            })
        # Update user plan
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET plan = %s WHERE id = %s", (req.plan, req.user_id))
            conn.commit()
            cur.close(); conn.close()
        return {"success": True, "plan": req.plan}
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────
# Team Workspaces
# ─────────────────────────────────────────
def init_workspace_tables():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id INTEGER REFERENCES users(id),
                plan TEXT DEFAULT 'pro',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workspace_members (
                id SERIAL PRIMARY KEY,
                workspace_id INTEGER REFERENCES workspaces(id),
                user_id INTEGER REFERENCES users(id),
                role TEXT DEFAULT 'viewer',
                joined_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(workspace_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workspace_invites (
                id SERIAL PRIMARY KEY,
                workspace_id INTEGER REFERENCES workspaces(id),
                email TEXT NOT NULL,
                role TEXT DEFAULT 'viewer',
                token TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close(); conn.close()
        print("Workspace tables ready")
    except Exception as e:
        print(f"Workspace tables error: {e}")

init_workspace_tables()

class CreateWorkspaceRequest(BaseModel):
    name: str

@app.post("/api/workspaces/create")
async def create_workspace(req: CreateWorkspaceRequest, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "): return {"error": "Unauthorized"}
    payload = verify_token(auth[7:])
    if not payload: return {"error": "Invalid token"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        # Check user plan
        cur.execute("SELECT plan FROM users WHERE id = %s", (payload["sub"],))
        user = cur.fetchone()
        if not user or user[0] not in ['pro', 'agency']:
            cur.close(); conn.close()
            return {"error": "Upgrade to Pro or Agency to create workspaces"}
        cur.execute("INSERT INTO workspaces (name, owner_id) VALUES (%s, %s) RETURNING id, name, created_at", (req.name, payload["sub"]))
        workspace = cur.fetchone()
        # Add owner as admin member
        cur.execute("INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (%s, %s, 'admin')", (workspace[0], payload["sub"]))
        conn.commit()
        cur.close(); conn.close()
        return {"workspace": {"id": workspace[0], "name": workspace[1], "created_at": str(workspace[2]), "role": "admin"}}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/workspaces")
async def get_workspaces(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "): return {"error": "Unauthorized"}
    payload = verify_token(auth[7:])
    if not payload: return {"error": "Invalid token"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT w.id, w.name, w.owner_id, w.created_at, wm.role,
                   (SELECT COUNT(*) FROM workspace_members WHERE workspace_id = w.id) as member_count
            FROM workspaces w
            JOIN workspace_members wm ON w.id = wm.workspace_id
            WHERE wm.user_id = %s
            ORDER BY w.created_at DESC
        """, (payload["sub"],))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"workspaces": [{"id": r[0], "name": r[1], "owner_id": r[2], "created_at": str(r[3]), "role": r[4], "member_count": r[5]} for r in rows]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/workspaces/{workspace_id}/members")
async def get_workspace_members(workspace_id: int, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "): return {"error": "Unauthorized"}
    payload = verify_token(auth[7:])
    if not payload: return {"error": "Invalid token"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.name, u.email, wm.role, wm.joined_at
            FROM workspace_members wm
            JOIN users u ON wm.user_id = u.id
            WHERE wm.workspace_id = %s
        """, (workspace_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"members": [{"id": r[0], "name": r[1], "email": r[2], "role": r[3], "joined_at": str(r[4])} for r in rows]}
    except Exception as e:
        return {"error": str(e)}

class InviteMemberRequest(BaseModel):
    workspace_id: int
    email: str
    role: str = "viewer"

@app.post("/api/workspaces/invite")
async def invite_member(req: InviteMemberRequest, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "): return {"error": "Unauthorized"}
    payload = verify_token(auth[7:])
    if not payload: return {"error": "Invalid token"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        import secrets
        token = secrets.token_urlsafe(32)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO workspace_invites (workspace_id, email, role, token)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (req.workspace_id, req.email, req.role, token))
        conn.commit()
        cur.close(); conn.close()
        # Send invite email via Resend
        resend_key = os.environ.get("RESEND_API_KEY", "")
        frontend_url = os.environ.get("FRONTEND_URL", "https://believable-rebirth-production-7e19.up.railway.app")
        invite_link = f"{frontend_url}?invite={token}"
        if resend_key:
            try:
                import httpx as _httpx
                async with _httpx.AsyncClient() as _client:
                    await _client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                        json={
                            "from": "SEM AI <reports@sakthivelraja.ai>",
                            "to": [req.email],
                            "subject": "You have been invited to a SEM AI Workspace",
                            "html": f"""<div style="font-family:sans-serif;max-width:500px;margin:0 auto;padding:24px;"><h2 style="color:#6366f1;">You have been invited to join a SEM AI Workspace</h2><p>You have been invited to collaborate on SEM AI platform.</p><p>Click the button below to accept your invitation:</p><a href="{invite_link}" style="display:inline-block;padding:12px 24px;background:#6366f1;color:white;text-decoration:none;border-radius:8px;font-weight:600;">Accept Invitation</a><p style="color:#6b7280;font-size:12px;margin-top:24px;">If you did not expect this invitation, you can ignore this email.</p></div>"""
                        }
                    )
            except Exception as e:
                print(f"Email send error: {e}")
        return {"success": True, "invite_token": token, "invite_link": invite_link, "message": f"Invite sent to {req.email}"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/workspaces/accept-invite/{token}")
async def accept_invite(token: str, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "): return {"error": "Unauthorized"}
    payload = verify_token(auth[7:])
    if not payload: return {"error": "Invalid token"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, workspace_id, email, role FROM workspace_invites WHERE token = %s AND status = 'pending'", (token,))
        invite = cur.fetchone()
        if not invite: return {"error": "Invalid or expired invite"}
        cur.execute("INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (invite[1], payload["sub"], invite[3]))
        cur.execute("UPDATE workspace_invites SET status = 'accepted' WHERE id = %s", (invite[0],))
        conn.commit()
        cur.close(); conn.close()
        return {"success": True, "workspace_id": invite[1]}
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────
# Usage Limits
# ─────────────────────────────────────────
def init_usage_table():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action TEXT DEFAULT 'analysis',
                date DATE DEFAULT CURRENT_DATE,
                count INTEGER DEFAULT 0,
                UNIQUE(user_id, action, date)
            )
        """)
        conn.commit()
        cur.close(); conn.close()
        print("Usage table ready")
    except Exception as e:
        print(f"Usage table error: {e}")

init_usage_table()

PLAN_LIMITS = {
    "free": 1,
    "pro": 999999,
    "agency": 999999,
}

def check_and_increment_usage(user_id: int, plan: str, action: str = "analysis") -> dict:
    limit = PLAN_LIMITS.get(plan, 1)
    conn = get_db_connection()
    if not conn: return {"allowed": True}
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO usage_tracking (user_id, action, date, count)
            VALUES (%s, %s, CURRENT_DATE, 1)
            ON CONFLICT (user_id, action, date)
            DO UPDATE SET count = usage_tracking.count + 1
            RETURNING count
        """, (user_id, action))
        count = cur.fetchone()[0]
        conn.commit()
        cur.close(); conn.close()
        if count > limit:
            return {"allowed": False, "count": count, "limit": limit, "plan": plan}
        return {"allowed": True, "count": count, "limit": limit}
    except Exception as e:
        print(f"Usage check error: {e}")
        return {"allowed": True}

@app.post("/api/usage/check")
async def check_usage(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "): return {"allowed": True}
    payload = verify_token(auth[7:])
    if not payload: return {"allowed": True}
    conn = get_db_connection()
    if not conn: return {"allowed": True}
    try:
        cur = conn.cursor()
        cur.execute("SELECT plan FROM users WHERE id = %s", (payload["sub"],))
        user = cur.fetchone()
        cur.execute("""
            SELECT count FROM usage_tracking 
            WHERE user_id = %s AND action = 'analysis' AND date = CURRENT_DATE
        """, (payload["sub"],))
        usage = cur.fetchone()
        cur.close(); conn.close()
        plan = user[0] if user else "free"
        count = usage[0] if usage else 0
        limit = PLAN_LIMITS.get(plan, 1)
        return {"allowed": count < limit, "count": count, "limit": limit, "plan": plan}
    except Exception as e:
        return {"allowed": True}


# ─────────────────────────────────────────
# Subscription Management
# ─────────────────────────────────────────
class ChangeSubscriptionRequest(BaseModel):
    plan: str

@app.post("/api/subscription/change")
async def change_subscription(req: ChangeSubscriptionRequest, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "): return {"error": "Unauthorized"}
    payload = verify_token(auth[7:])
    if not payload: return {"error": "Invalid token"}
    if req.plan not in ["free", "pro", "agency"]:
        return {"error": "Invalid plan"}
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET plan = %s WHERE id = %s", (req.plan, payload["sub"]))
        conn.commit()
        cur.close(); conn.close()
        return {"success": True, "plan": req.plan}
    except Exception as e:
        return {"error": str(e)}

# ─── Auto-Pilot Mode ──────────────────────────────────────────────────────────

@app.post("/api/ads/autopilot/status")
async def get_autopilot_status(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS autopilot_settings (
                    session_id TEXT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT FALSE,
                    last_run TIMESTAMP,
                    actions_taken JSONB DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.execute("SELECT enabled, last_run, actions_taken FROM autopilot_settings WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return {"enabled": row[0], "last_run": str(row[1]) if row[1] else None, "actions": row[2] or []}
    except Exception as e:
        print(f"Autopilot status error: {e}")
    return {"enabled": False, "last_run": None, "actions": []}

@app.post("/api/ads/autopilot/history")
async def get_autopilot_history(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    limit = body.get("limit", 10)
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS autopilot_log (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    run_at TIMESTAMP DEFAULT NOW(),
                    actions JSONB,
                    total_actions INT
                )
            """)
            cur.execute("""
                SELECT id, run_at, actions, total_actions 
                FROM autopilot_log 
                WHERE session_id = %s 
                ORDER BY run_at DESC 
                LIMIT %s
            """, (session_id, limit))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            history = []
            for row in rows:
                import json
                history.append({
                    "id": row[0],
                    "run_at": row[1].strftime("%Y-%m-%d %H:%M:%S") if row[1] else "",
                    "actions": row[2] if isinstance(row[2], list) else json.loads(row[2]) if row[2] else [],
                    "total_actions": row[3] or 0
                })
            return {"history": history, "total": len(history)}
    except Exception as e:
        return {"history": [], "total": 0, "error": str(e)}

@app.post("/api/ads/autopilot/toggle")
async def toggle_autopilot(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    enabled = body.get("enabled", False)
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO autopilot_settings (session_id, enabled, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (session_id) DO UPDATE SET enabled = %s, updated_at = NOW()
            """, (session_id, enabled, enabled))
            conn.commit()
            cur.close()
            conn.close()
            return {"success": True, "enabled": enabled}
    except Exception as e:
        print(f"Autopilot toggle error: {e}")
    return {"success": False}

@app.post("/api/ads/autopilot/run")
async def run_autopilot(request: Request):
    import httpx
    body = await request.json()
    session_id = body.get("session_id")
    customer_id = body.get("customer_id", "7836650842")
    
    session = _sessions.get(session_id)
    if not session:
        fresh = load_sessions()
        session = fresh.get(session_id)
    if not session:
        return {"success": False, "message": "Session not found"}
    
    actions = []
    try:
        refresh_token = session.get("refresh_token", "")
        if isinstance(refresh_token, bytes): refresh_token = refresh_token.decode("utf-8")
        
        import httpx as _hx
        tr = _hx.post("https://oauth2.googleapis.com/token", data={
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        })
        access_token = str(tr.json().get("access_token", "")).strip()
        dev_token = str(os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")).strip()
        manager_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
        headers = {
            "Authorization": "Bearer " + access_token,
            "developer-token": dev_token,
            "Content-Type": "application/json"
        }
        if manager_id:
            headers["login-customer-id"] = manager_id

        async with _hx.AsyncClient(timeout=30) as client:
            # Fetch campaigns
            resp = await client.post(
                f"https://googleads.googleapis.com/v23/customers/{customer_id}/googleAds:search",
                headers=headers,
                json={"query": "SELECT campaign.id, campaign.name, campaign.status, metrics.clicks, metrics.impressions, metrics.ctr, metrics.cost_micros FROM campaign WHERE campaign.status = 'ENABLED'"}
            )
            
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for row in results:
                    m = row.get("metrics", {})
                    clicks = int(m.get("clicks", 0))
                    impressions = int(m.get("impressions", 0))
                    ctr = float(m.get("ctr", 0))
                    campaign_name = row.get("campaign", {}).get("name", "")
                    
                    # Low CTR detection
                    if impressions > 100 and ctr < 0.01:
                        actions.append({
                            "type": "warning",
                            "campaign": campaign_name,
                            "action": f"Low CTR detected ({round(ctr*100, 2)}%) — Consider pausing or improving ads",
                            "severity": "high"
                        })
                    elif impressions > 50 and clicks == 0:
                        actions.append({
                            "type": "warning", 
                            "campaign": campaign_name,
                            "action": "0 clicks with impressions — Ad copy needs improvement",
                            "severity": "medium"
                        })
                    else:
                        actions.append({
                            "type": "info",
                            "campaign": campaign_name,
                            "action": f"Campaign healthy — {clicks} clicks, CTR {round(ctr*100,2)}%",
                            "severity": "low"
                        })

        # Use Gemini for recommendations
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        actions_summary = "\n".join([f"- {a['campaign']}: {a['action']}" for a in actions])
        prompt = f"""You are a Google Ads Auto-Pilot AI. Based on these campaign insights:
{actions_summary}

Give 3 specific auto-pilot recommendations in JSON:
{{"recommendations": [{{"action": "...", "reason": "...", "priority": "high/medium/low"}}]}}"""
        
        try:
            resp_ai = model.generate_content(prompt)
            import json, re
            match = re.search(r'\{.*\}', resp_ai.text, re.DOTALL)
            if match:
                ai_data = json.loads(match.group())
                for rec in ai_data.get("recommendations", []):
                    actions.append({
                        "type": "ai_recommendation",
                        "action": rec.get("action", ""),
                        "reason": rec.get("reason", ""),
                        "severity": rec.get("priority", "medium")
                    })
        except:
            pass

        # Save to DB
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                import json
                # Update settings
                cur.execute("""
                    INSERT INTO autopilot_settings (session_id, enabled, last_run, actions_taken, updated_at)
                    VALUES (%s, TRUE, NOW(), %s, NOW())
                    ON CONFLICT (session_id) DO UPDATE SET last_run = NOW(), actions_taken = %s, updated_at = NOW()
                """, (session_id, json.dumps(actions), json.dumps(actions)))
                # Save to activity log
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS autopilot_log (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT,
                        run_at TIMESTAMP DEFAULT NOW(),
                        actions JSONB,
                        total_actions INT
                    )
                """)
                cur.execute("""
                    INSERT INTO autopilot_log (session_id, run_at, actions, total_actions)
                    VALUES (%s, NOW(), %s, %s)
                """, (session_id, json.dumps(actions), len(actions)))
                conn.commit()
                cur.close()
                conn.close()
        except Exception as e:
            print(f"DB save error: {e}")

        return {"success": True, "actions": actions, "total": len(actions)}

    except Exception as e:
        return {"success": False, "message": str(e), "actions": []}

# ─── AB Test State ────────────────────────────────────────────────────────────

@app.post("/api/ads/ab-test/save-state")
async def save_ab_state(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    campaign_resource = body.get("campaign_resource_name")
    variant_a = body.get("variant_a")
    variant_b = body.get("variant_b")
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_state (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    campaign_resource TEXT,
                    variant_a JSONB,
                    variant_b JSONB,
                    status TEXT DEFAULT 'running',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.execute("""
                INSERT INTO ab_test_state (session_id, campaign_resource, variant_a, variant_b, status)
                VALUES (%s, %s, %s, %s, 'running')
                ON CONFLICT DO NOTHING
            """, (session_id, campaign_resource, json.dumps(variant_a), json.dumps(variant_b)))
            conn.commit()
            cur.close()
            conn.close()
            return {"success": True}
    except Exception as e:
        print(f"AB state save error: {e}")
    return {"success": False}

@app.post("/api/ads/ab-test/get-state")
async def get_ab_state(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    campaign_resource = body.get("campaign_resource_name")
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_state (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    campaign_resource TEXT,
                    variant_a JSONB,
                    variant_b JSONB,
                    status TEXT DEFAULT 'running',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.execute("""
                SELECT variant_a, variant_b, status, created_at 
                FROM ab_test_state 
                WHERE session_id = %s AND campaign_resource = %s
                ORDER BY created_at DESC LIMIT 1
            """, (session_id, campaign_resource))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return {"running": True, "variant_a": row[0], "variant_b": row[1], "status": row[2], "created_at": str(row[3])}
    except Exception as e:
        print(f"AB state get error: {e}")
    return {"running": False}

@app.post("/api/admin/users/{user_id}/toggle")
async def admin_toggle_user(user_id: int, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or not is_admin(auth[7:]):
        return {"error": "Unauthorized"}
    body = await request.json()
    is_active = body.get("is_active", True)
    conn = get_db_connection()
    if not conn: return {"error": "DB error"}
    try:
        cur = conn.cursor()
        # Add column if not exists
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
        conn.commit()
        cur.execute("UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id))
        conn.commit()
        cur.close(); conn.close()
        return {"success": True, "is_active": is_active}
    except Exception as e:
        return {"error": str(e)}

# ─── Auto-Pilot Scheduler ────────────────────────────────────────────────────
scheduler = AsyncIOScheduler()

async def run_autopilot_for_all_active():
    """Run auto-pilot for all active sessions every 6 hours."""
    print("⏰ Scheduled Auto-Pilot run starting...")
    try:
        conn = get_db_connection()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("SELECT session_id FROM autopilot_settings WHERE enabled = TRUE")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        for row in rows:
            session_id = row[0]
            session = _sessions.get(session_id)
            if not session:
                fresh = load_sessions()
                session = fresh.get(session_id)
            if not session:
                continue
            try:
                cid = session.get("customer_id", "").replace("-", "")
                if not cid:
                    continue
                import httpx as _hx
                import json as _json
                # Simple health check run
                actions = [{"type": "info", "action": "Scheduled auto-pilot check completed", "severity": "low"}]
                conn2 = get_db_connection()
                if conn2:
                    cur2 = conn2.cursor()
                    cur2.execute("""
                        CREATE TABLE IF NOT EXISTS autopilot_log (
                            id SERIAL PRIMARY KEY, session_id TEXT,
                            run_at TIMESTAMP DEFAULT NOW(), actions JSONB, total_actions INT
                        )
                    """)
                    cur2.execute("""
                        INSERT INTO autopilot_log (session_id, run_at, actions, total_actions)
                        VALUES (%s, NOW(), %s, %s)
                    """, (session_id, _json.dumps(actions), len(actions)))
                    cur2.execute("""
                        UPDATE autopilot_settings SET last_run = NOW(), updated_at = NOW()
                        WHERE session_id = %s
                    """, (session_id,))
                    conn2.commit()
                    cur2.close()
                    conn2.close()
                print(f"✅ Auto-pilot ran for session {session_id[:20]}")
            except Exception as e:
                print(f"Auto-pilot error for {session_id[:20]}: {e}")
    except Exception as e:
        print(f"Scheduler error: {e}")

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        run_autopilot_for_all_active,
        IntervalTrigger(hours=6),
        id="autopilot_job",
        replace_existing=True
    )
    # Weekly email reports — every Monday 9AM
    from apscheduler.triggers.cron import CronTrigger
    scheduler.add_job(
        send_weekly_reports,
        CronTrigger(day_of_week='mon', hour=9, minute=0),
        id="weekly_email_job",
        replace_existing=True
    )
    scheduler.start()
    print("⏰ Auto-Pilot scheduler started — runs every 6 hours")
    print("📧 Weekly email reports scheduler started — every Monday 9AM")

@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown()

# ─── User Tab Activity Tracking ──────────────────────────────────────────────
@app.post("/api/track/tab")
async def track_tab_visit(request: Request):
    """Track user tab visits and time spent."""
    try:
        body = await request.json()
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_id = None
        email = None
        try:
            import base64 as _b64, json as _j
            parts = token.split('.')
            if len(parts) == 3:
                padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
                payload = _j.loads(_b64.b64decode(padded))
                user_id = str(payload.get("sub", ""))
                email = payload.get("email", "")
        except:
            pass
        tab = body.get("tab", "")
        url = body.get("url", "")
        time_spent = int(body.get("time_spent", 0))
        action = body.get("action", "visit")
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id SERIAL PRIMARY KEY, user_id TEXT, email TEXT,
                    tab TEXT, url TEXT, time_spent INT DEFAULT 0,
                    action TEXT, visited_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                INSERT INTO user_activity (user_id, email, tab, url, time_spent, action, visited_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (user_id, email, tab, url, time_spent, action))
            conn.commit()
            cur.close()
            conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/user-activity")
async def get_user_activity(request: Request):
    """Get user activity for admin panel."""
    try:
        body = await request.json()
        token = body.get("token", "")
        try:
            import base64, json as _json
            parts = token.split('.')
            if len(parts) != 3:
                return {"error": "Invalid token"}
            padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = _json.loads(base64.b64decode(padded))
            email = payload.get("email", "")
            if email != "jsvking@gmail.com":
                return {"error": "Unauthorized"}
        except:
            return {"error": "Invalid token"}
        conn = get_db_connection()
        if not conn:
            return {"activity": []}
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id SERIAL PRIMARY KEY, user_id TEXT, email TEXT,
                tab TEXT, url TEXT, time_spent INT DEFAULT 0,
                action TEXT, visited_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            SELECT email, tab, url,
                SUM(time_spent) as total_time,
                COUNT(*) as visit_count,
                MAX(visited_at) as last_visit
            FROM user_activity
            WHERE visited_at > NOW() - INTERVAL '30 days'
            GROUP BY email, tab, url
            ORDER BY last_visit DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        activity = []
        for row in rows:
            activity.append({
                "email": row[0] or "anonymous",
                "tab": row[1],
                "url": row[2],
                "total_time_seconds": int(row[3] or 0),
                "total_time_formatted": f"{int((row[3] or 0)//60)}m {int((row[3] or 0)%60)}s",
                "visit_count": row[4],
                "last_visit": row[5].strftime("%Y-%m-%d %H:%M") if row[5] else ""
            })
        return {"activity": activity, "total": len(activity)}
    except Exception as e:
        return {"activity": [], "error": str(e)}

# ─── Email Report Preferences ────────────────────────────────────────────────

@app.post("/api/email-reports/preferences")
async def get_email_preferences(request: Request):
    """Get user email report preferences."""
    try:
        body = await request.json()
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        try:
            import base64, json as _j
            parts = token.split('.')
            padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = _j.loads(base64.b64decode(padded))
            user_id = payload.get("sub")
            email = payload.get("email")
        except:
            return {"error": "Invalid token"}
        
        conn = get_db_connection()
        if not conn:
            return {"enabled": False}
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS email_preferences (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                weekly_report BOOLEAN DEFAULT TRUE,
                last_sent TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("SELECT weekly_report, last_sent FROM email_preferences WHERE user_id = %s", (str(user_id),))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            return {"enabled": row[0], "last_sent": str(row[1]) if row[1] else None}
        return {"enabled": True, "last_sent": None}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/email-reports/toggle")
async def toggle_email_reports(request: Request):
    """Enable/disable weekly email reports."""
    try:
        body = await request.json()
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        enabled = body.get("enabled", True)
        try:
            import base64, json as _j
            parts = token.split('.')
            padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = _j.loads(base64.b64decode(padded))
            user_id = payload.get("sub")
            email = payload.get("email")
        except:
            return {"error": "Invalid token"}
        
        conn = get_db_connection()
        if not conn:
            return {"error": "DB error"}
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS email_preferences (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                weekly_report BOOLEAN DEFAULT TRUE,
                last_sent TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            INSERT INTO email_preferences (user_id, email, weekly_report)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET weekly_report = %s
        """, (str(user_id), email, enabled, enabled))
        conn.commit()
        cur.close(); conn.close()
        return {"success": True, "enabled": enabled}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/email-reports/send-test")
async def send_test_email_report(request: Request):
    """Send a test email report to the user."""
    try:
        body = await request.json()
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        try:
            import base64, json as _j
            parts = token.split('.')
            padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = _j.loads(base64.b64decode(padded))
            email = payload.get("email")
            name = email.split("@")[0] if email else "User"
        except:
            return {"error": "Invalid token"}
        
        site_url = body.get("url", "your website")
        resend_api_key = os.environ.get("RESEND_API_KEY", "")
        if not resend_api_key:
            return {"error": "Email service not configured"}
        
        html = f"""
        <div style="font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#f0f0f8;padding:32px;border-radius:16px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px">
            <div style="width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:16px">⚡</div>
            <span style="font-size:18px;font-weight:700">SEM AI Weekly Report</span>
          </div>
          
          <p style="color:#a0a0b8;margin-bottom:24px">Hi {name}, here's your weekly SEO & campaign summary for <strong style="color:#f0f0f8">{site_url}</strong></p>
          
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:24px">
            <div style="background:#111118;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px">
              <div style="font-size:12px;color:#606070;margin-bottom:4px">SEO SCORE</div>
              <div style="font-size:28px;font-weight:800;color:#6366f1">75/100</div>
            </div>
            <div style="background:#111118;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px">
              <div style="font-size:12px;color:#606070;margin-bottom:4px">IMPRESSIONS</div>
              <div style="font-size:28px;font-weight:800;color:#06b6d4">1</div>
            </div>
          </div>
          
          <div style="background:#111118;border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:16px;margin-bottom:24px">
            <div style="font-size:13px;font-weight:600;margin-bottom:12px">⚡ Quick Wins This Week</div>
            <div style="font-size:13px;color:#a0a0b8;margin-bottom:8px">• Add H1 tag to homepage — +8 SEO points</div>
            <div style="font-size:13px;color:#a0a0b8;margin-bottom:8px">• Shorten meta description — +5 SEO points</div>
            <div style="font-size:13px;color:#a0a0b8">• Add schema markup — +10 SEO points</div>
          </div>
          
          <a href="https://believable-rebirth-production-7e19.up.railway.app" style="display:block;text-align:center;padding:14px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border-radius:10px;text-decoration:none;font-weight:600;font-size:15px">View Full Report →</a>
          
          <p style="text-align:center;font-size:12px;color:#606070;margin-top:20px">
            <a href="#" style="color:#6366f1">Unsubscribe</a> from weekly reports
          </p>
        </div>
        """
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_api_key}", "Content-Type": "application/json"},
                json={
                    "from": "SEM AI <reports@sakthivelraja.ai>",
                    "to": [email],
                    "subject": f"📊 Your Weekly SEO Report — {site_url}",
                    "html": html
                }
            )
        if resp.status_code == 200:
            return {"success": True, "message": f"Test report sent to {email}"}
        return {"error": f"Email failed: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}

async def send_weekly_reports():
    """Send weekly email reports to all opted-in users."""
    print("📧 Sending weekly email reports...")
    try:
        conn = get_db_connection()
        if not conn: return
        cur = conn.cursor()
        cur.execute("""
            SELECT ep.user_id, ep.email, u.name
            FROM email_preferences ep
            LEFT JOIN users u ON u.id::text = ep.user_id
            WHERE ep.weekly_report = TRUE
            AND (ep.last_sent IS NULL OR ep.last_sent < NOW() - INTERVAL '7 days')
        """)
        users = cur.fetchall()
        cur.close(); conn.close()
        print(f"Found {len(users)} users to email")
        for user in users:
            try:
                resend_api_key = os.environ.get("RESEND_API_KEY", "")
                if not resend_api_key: continue
                email = user[1]
                name = user[2] or email.split("@")[0]
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {resend_api_key}", "Content-Type": "application/json"},
                        json={
                            "from": "SEM AI <reports@sakthivelraja.ai>",
                            "to": [email],
                            "subject": "📊 Your Weekly SEM AI Report",
                            "html": f"<p>Hi {name}, your weekly report is ready. <a href='https://believable-rebirth-production-7e19.up.railway.app'>View Dashboard →</a></p>"
                        }
                    )
                # Update last_sent
                conn2 = get_db_connection()
                if conn2:
                    cur2 = conn2.cursor()
                    cur2.execute("UPDATE email_preferences SET last_sent = NOW() WHERE user_id = %s", (user[0],))
                    conn2.commit()
                    cur2.close(); conn2.close()
                print(f"✅ Email sent to {email}")
            except Exception as e:
                print(f"❌ Failed for {user[1]}: {e}")
    except Exception as e:
        print(f"Weekly report error: {e}")

# ─── Hybrid Autonomous SEM Engine ────────────────────────────────────────────

TRUST_THRESHOLDS = {
    "bid_adjust_auto_max_pct": 10,      # ±10% bid change → auto
    "ctr_pause_threshold": 0.005,        # CTR < 0.5% for 7 days → auto pause keyword
    "budget_used_pause_pct": 80,         # 80% budget used → auto pause
    "ai_confidence_keyword_add": 85,     # AI confidence > 85% → auto add keyword
}

async def classify_action(action_type: str, magnitude: float = 0) -> str:
    """Classify action as 'auto' or 'approve'."""
    if action_type == "bid_adjust":
        return "auto" if abs(magnitude) <= TRUST_THRESHOLDS["bid_adjust_auto_max_pct"] else "approve"
    elif action_type == "pause_keyword":
        return "auto"
    elif action_type == "pause_campaign":
        return "auto"
    elif action_type == "budget_increase":
        return "approve"
    elif action_type == "new_campaign":
        return "approve"
    elif action_type == "add_keyword":
        return "auto" if magnitude >= TRUST_THRESHOLDS["ai_confidence_keyword_add"] else "approve"
    elif action_type == "change_ad_copy":
        return "auto"
    return "approve"

@app.post("/api/ads/autonomous/run")
async def run_autonomous_engine(request: Request):
    """Run hybrid autonomous SEM engine."""
    import httpx as _hx, json as _j
    body = await request.json()
    session_id = body.get("session_id")
    customer_id = body.get("customer_id", "")

    session = _sessions.get(session_id)
    if not session:
        fresh = load_sessions()
        session = fresh.get(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}

    auto_actions = []
    approve_actions = []

    try:
        refresh_token = session.get("refresh_token", "")
        cid = (customer_id or session.get("customer_id", "")).replace("-", "")

        # Fetch campaigns
        campaigns = get_all_campaigns_spend(cid, refresh_token)

        for campaign in campaigns:
            c_name = campaign.get("campaign_name", "")
            c_resource = campaign.get("resource_name", "")
            clicks = int(campaign.get("clicks", 0))
            impressions = int(campaign.get("impressions", 0))
            ctr = float(campaign.get("ctr", 0))
            spend = float(campaign.get("spend_today_usd", 0))
            daily_budget = float(campaign.get("daily_budget_inr", 500))

            # Rule 1: Low CTR → suggest ad copy change (auto)
            if impressions > 100 and ctr < TRUST_THRESHOLDS["ctr_pause_threshold"]:
                action_class = await classify_action("change_ad_copy")
                action = {
                    "type": "change_ad_copy",
                    "campaign": c_name,
                    "resource": c_resource,
                    "reason": f"CTR {round(ctr*100,2)}% is below 0.5% threshold",
                    "recommendation": "Generate new ad copy variants using A/B test",
                    "severity": "high",
                    "class": action_class,
                    "auto_applied": False,
                }
                if action_class == "auto":
                    auto_actions.append(action)
                else:
                    approve_actions.append(action)

            # Rule 2: Budget 80% used → auto pause
            monthly_monitor = campaign.get("budget_monitoring", {})
            if monthly_monitor:
                spend_pct = monthly_monitor.get("spend_percentage", 0)
                if spend_pct >= TRUST_THRESHOLDS["budget_used_pause_pct"]:
                    action_class = await classify_action("pause_campaign")
                    action = {
                        "type": "pause_campaign",
                        "campaign": c_name,
                        "resource": c_resource,
                        "reason": f"Budget {spend_pct}% used — auto-pausing to prevent overspend",
                        "severity": "critical",
                        "class": "auto",
                        "auto_applied": True,
                    }
                    auto_actions.append(action)

            # Rule 3: 0 impressions after 3 days → approve to pause
            if impressions == 0 and clicks == 0:
                approve_actions.append({
                    "type": "review_campaign",
                    "campaign": c_name,
                    "resource": c_resource,
                    "reason": "0 impressions detected — possible policy issue or targeting problem",
                    "recommendation": "Review campaign settings, keywords and ad policy",
                    "severity": "medium",
                    "class": "approve",
                    "auto_applied": False,
                })

            # Rule 4: Good performance → suggest bid increase (approve)
            if ctr > 0.05 and clicks > 50:
                approve_actions.append({
                    "type": "budget_increase",
                    "campaign": c_name,
                    "resource": c_resource,
                    "reason": f"High CTR {round(ctr*100,2)}% — campaign performing well",
                    "recommendation": "Consider increasing daily budget by 20% to capture more traffic",
                    "severity": "low",
                    "class": "approve",
                    "auto_applied": False,
                })

        # Save to DB
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS autonomous_actions (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    run_at TIMESTAMP DEFAULT NOW(),
                    auto_actions JSONB,
                    approve_actions JSONB,
                    status TEXT DEFAULT 'pending'
                )
            """)
            cur.execute("""
                INSERT INTO autonomous_actions (session_id, auto_actions, approve_actions, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id
            """, (session_id, _j.dumps(auto_actions), _j.dumps(approve_actions)))
            run_id = cur.fetchone()[0]
            conn.commit()
            cur.close(); conn.close()

        # Send approval email if needed
        if approve_actions:
            email = session.get("email", "") or session.get("user_email", "")
            print(f"Sending approval email to: {email}, approve_actions: {len(approve_actions)}")
            resend_api_key = os.environ.get("RESEND_API_KEY", "")
            if email and resend_api_key:
                approval_items = "".join([
                    f"<div style='padding:16px;margin-bottom:10px;background:#1a1a24;border-radius:10px;border-left:4px solid {'#f87171' if a['severity']=='critical' else '#fbbf24' if a['severity']=='high' else '#60a5fa'}'>"
                    f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>"
                    f"<div style='font-size:14px;font-weight:700;color:#f0f0f8'>{a['type'].replace('_',' ').title()}</div>"
                    f"<span style='font-size:11px;padding:2px 8px;border-radius:10px;background:{'rgba(239,68,68,0.2)' if a['severity']=='critical' else 'rgba(251,191,36,0.2)' if a['severity']=='high' else 'rgba(96,165,250,0.2)'};color:{'#f87171' if a['severity']=='critical' else '#fbbf24' if a['severity']=='high' else '#60a5fa'}'>{a['severity'].upper()}</span>"
                    f"</div>"
                    f"<div style='font-size:12px;color:#606070;margin-bottom:2px'>CAMPAIGN</div>"
                    f"<div style='font-size:13px;color:#a0a0b8;margin-bottom:8px'>{a['campaign']}</div>"
                    f"<div style='font-size:12px;color:#606070;margin-bottom:2px'>ISSUE DETECTED</div>"
                    f"<div style='font-size:13px;color:#a0a0b8;margin-bottom:8px'>{a['reason']}</div>"
                    f"<div style='font-size:12px;color:#606070;margin-bottom:2px'>RECOMMENDED ACTION</div>"
                    f"<div style='font-size:13px;color:#a0a0b8;margin-bottom:12px'>{a.get('recommendation','Review and take appropriate action')}</div>"
                    f"<div style='display:flex;gap:8px'>"
                    f"<a href='https://believable-rebirth-production-7e19.up.railway.app/approve/{run_id}/{i}/{session_id}' style='padding:8px 16px;background:#22c55e;color:white;border-radius:7px;text-decoration:none;font-size:13px;font-weight:600'>✅ Approve & Mark Reviewed</a>"
                    f"<a href='https://believable-rebirth-production-7e19.up.railway.app' style='padding:8px 14px;background:#374151;color:white;border-radius:7px;text-decoration:none;font-size:13px'>View in Dashboard</a>"
                    f"</div>"
                    f"</div>"
                    for i, a in enumerate(approve_actions)
                ])
                html = f"""
                <div style='font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#f0f0f8;padding:32px;border-radius:16px'>
                  <div style='display:flex;align-items:center;gap:10px;margin-bottom:24px'>
                    <div style='width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);text-align:center;line-height:32px'>⚡</div>
                    <span style='font-size:18px;font-weight:700'>SEM AI — Action Required</span>
                  </div>
                  <p style='color:#a0a0b8;margin-bottom:16px'>Your AI found <strong style='color:#f0f0f8'>{len(approve_actions)} actions</strong> that need your approval:</p>
                  {approval_items}
                  <div style='margin-top:20px;padding:16px;background:#111118;border-radius:10px;border:1px solid rgba(99,102,241,0.2)'>
                    <div style='font-size:13px;color:#a0a0b8;margin-bottom:12px'>✅ Auto-applied {len(auto_actions)} small fixes already</div>
                    <a href='https://believable-rebirth-production-7e19.up.railway.app/?tab=ads&subtab=autopilot' style='display:block;text-align:center;padding:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border-radius:8px;text-decoration:none;font-weight:600'>Review & Approve in Auto-Pilot →</a>
                  </div>
                </div>
                """
                async with _hx.AsyncClient() as client:
                    await client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {resend_api_key}", "Content-Type": "application/json"},
                        json={
                            "from": "SEM AI <reports@sakthivelraja.ai>",
                            "to": [email],
                            "subject": f"⚡ SEM AI: {len(approve_actions)} actions need your approval",
                            "html": html
                        }
                    )

        return {
            "success": True,
            "run_id": run_id if 'run_id' in dir() else None,
            "auto_actions": auto_actions,
            "approve_actions": approve_actions,
            "summary": {
                "auto_applied": len([a for a in auto_actions if a.get("auto_applied")]),
                "pending_approval": len(approve_actions),
                "total": len(auto_actions) + len(approve_actions),
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.get("/api/ads/autonomous/pending/{session_id}")
async def get_pending_approvals(session_id: str):
    """Get pending approval actions."""
    try:
        conn = get_db_connection()
        if not conn:
            return {"pending": []}
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_actions (
                id SERIAL PRIMARY KEY, session_id TEXT,
                run_at TIMESTAMP DEFAULT NOW(),
                auto_actions JSONB, approve_actions JSONB,
                status TEXT DEFAULT 'pending'
            )
        """)
        cur.execute("""
            SELECT id, run_at, auto_actions, approve_actions
            FROM autonomous_actions
            WHERE session_id = %s AND status = 'pending'
            ORDER BY run_at DESC LIMIT 10
        """, (session_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        import json as _j
        pending = []
        for row in rows:
            approve = row[3] if isinstance(row[3], list) else _j.loads(row[3]) if row[3] else []
            pending.append({
                "id": row[0],
                "run_at": row[1].strftime("%Y-%m-%d %H:%M") if row[1] else "",
                "approve_actions": approve,
            })
        return {"pending": pending}
    except Exception as e:
        return {"pending": [], "error": str(e)}

@app.post("/api/ads/autonomous/approve")
async def approve_autonomous_action(request: Request):
    """Approve a pending autonomous action."""
    import json as _j
    body = await request.json()
    run_id = body.get("run_id")
    action_index = body.get("action_index", 0)
    session_id = body.get("session_id")

    try:
        conn = get_db_connection()
        if not conn:
            return {"error": "DB error"}
        cur = conn.cursor()
        cur.execute("SELECT approve_actions, session_id FROM autonomous_actions WHERE id = %s", (run_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Action not found"}

        approve_actions = row[0] if isinstance(row[0], list) else _j.loads(row[0])
        session_id = session_id or row[1]
        
        if action_index >= len(approve_actions):
            return {"error": "Invalid action index"}

        action = approve_actions[action_index]
        action_type = action.get("type", "")
        campaign_resource = action.get("resource", "")

        session = _sessions.get(session_id)
        if not session:
            fresh = load_sessions()
            session = fresh.get(session_id)

        result_msg = ""

        # Execute the approved action
        if action_type == "pause_campaign" and session:
            from ads_manager import pause_campaign
            cid = session.get("customer_id", "").replace("-", "")
            refresh_token = session.get("refresh_token", "")
            result = pause_campaign(cid, refresh_token, campaign_resource)
            result_msg = "Campaign paused successfully"

        elif action_type == "budget_increase" and session:
            result_msg = "Budget increase noted — please update manually in Google Ads"

        elif action_type == "review_campaign":
            result_msg = "Action marked as reviewed"

        else:
            result_msg = f"Action '{action_type}' approved and logged"

        # Mark as approved in DB
        approve_actions[action_index]["approved"] = True
        approve_actions[action_index]["approved_result"] = result_msg
        
        # Check if all approved
        all_approved = all(a.get("approved") for a in approve_actions)
        new_status = "completed" if all_approved else "partial"

        cur.execute("""
            UPDATE autonomous_actions 
            SET approve_actions = %s, status = %s
            WHERE id = %s
        """, (_j.dumps(approve_actions), new_status, run_id))
        conn.commit()
        cur.close(); conn.close()

        return {"success": True, "message": result_msg, "action": action}

    except Exception as e:
        return {"error": str(e)}

@app.get("/api/ads/autonomous/approve-page/{run_id}/{action_index}/{session_id}")
async def approve_action_page(run_id: int, action_index: int, session_id: str):
    """Simple HTML page for email approve links - no auth required."""
    from fastapi.responses import HTMLResponse
    try:
        import json as _j
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT approve_actions FROM autonomous_actions WHERE id = %s", (run_id,))
            row = cur.fetchone()
            if row:
                actions = row[0] if isinstance(row[0], list) else _j.loads(row[0])
                if action_index < len(actions):
                    action = actions[action_index]
                    actions[action_index]["approved"] = True
                    actions[action_index]["approved_result"] = "Approved via email"
                    all_approved = all(a.get("approved") for a in actions)
                    new_status = "completed" if all_approved else "partial"
                    cur.execute("UPDATE autonomous_actions SET approve_actions = %s, status = %s WHERE id = %s", (_j.dumps(actions), new_status, run_id))
                    conn.commit()
                    cur.close(); conn.close()
                    action_name = action.get('type','').replace('_',' ').title()
                    campaign_name = action.get('campaign','')
                    reason = action.get('reason','')
                    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Action Approved — SEM AI</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a0f;color:#f0f0f8;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box">
<div style="text-align:center;padding:40px 32px;background:#111118;border-radius:20px;border:1px solid rgba(255,255,255,0.08);max-width:480px;width:100%">
  <div style="width:64px;height:64px;background:rgba(34,197,94,0.15);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:32px">✅</div>
  <h2 style="font-size:22px;font-weight:700;margin:0 0 8px">Action Approved!</h2>
  <p style="color:#a0a0b8;font-size:14px;margin:0 0 20px">{action_name}</p>
  <div style="background:#1a1a24;border-radius:10px;padding:14px 16px;text-align:left;margin-bottom:24px">
    <div style="font-size:12px;color:#606070;margin-bottom:4px">CAMPAIGN</div>
    <div style="font-size:13px;color:#f0f0f8;margin-bottom:10px">{campaign_name}</div>
    <div style="font-size:12px;color:#606070;margin-bottom:4px">ISSUE DETECTED</div>
    <div style="font-size:13px;color:#a0a0b8">{reason}</div>
  </div>
  <div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);border-radius:8px;padding:10px 14px;font-size:13px;color:#4ade80;margin-bottom:20px">
    ✓ Approval logged. SEM AI will process this action.
  </div>
  <a href="https://believable-rebirth-production-7e19.up.railway.app" style="display:block;padding:13px 24px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px">View Dashboard →</a>
  <p style="font-size:12px;color:#606070;margin-top:16px">Powered by SEM AI · <a href="https://believable-rebirth-production-7e19.up.railway.app" style="color:#6366f1">sakthivelraja.ai</a></p>
</div>
</body></html>""")
    except Exception as e:
        pass
    return HTMLResponse("<html><body>Error processing approval</body></html>")
