from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
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
from oauth_handler import get_oauth_url, exchange_code_for_tokens, get_user_info
from ads_manager import (
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
{{"overall_seo_score":72,"summary":"2-3 sentence assessment","strengths":[{{"point":"strength","impact":"high"}}],"weaknesses":[{{"point":"weakness","impact":"high","fix":"specific fix"}}],"technical_issues":[{{"issue":"name","severity":"critical","description":"detail","recommendation":"action"}}],"content_analysis":{{"quality_score":70,"readability":"Good","keyword_density":"Low","content_gaps":["gap1","gap2"]}},"keyword_suggestions":[{{"keyword":"kw","intent":"transactional","difficulty":"medium","priority":"primary"}}],"sem_recommendations":{{"suggested_monthly_budget_usd":{{"min":500,"max":2000}},"bidding_strategy":"Maximize Clicks","target_countries":["US","UK"],"audience_segments":[{{"segment":"name","age_range":"25-44","interests":["i1","i2"]}}],"estimated_monthly_clicks":{{"min":500,"max":2000}},"estimated_cpc_usd":{{"min":1.0,"max":3.0}}}},"competitor_insights":{{"likely_competitors":["c.com"],"positioning_suggestion":"differentiation"}},"priority_actions":[{{"action":"action","effort":"low","impact":"high"}}]}}"""

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
    seo_raw, ad_raw = await asyncio.gather(
        call_gemini(build_seo_prompt(scraped)),
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
        "mock_campaign": {"status": "PREVIEW", "message": "Connect Google Ads to publish"},
    }

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
    session = _sessions.get(req.session_id)
    if not session or not session.get("refresh_token"):
        raise HTTPException(status_code=401, detail="Not authenticated. Go to /auth/google to reconnect.")
    if req.daily_budget_usd < 1.0:
        raise HTTPException(status_code=400, detail=f"Daily budget ${req.daily_budget_usd:.2f} is below Google Ads minimum of $1.00/day.")

    # Always use client account, never manager account
    manager_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    client_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "").replace("-", "")
    resolved = resolve_customer_id(session, req.customer_id)
    customer_id = client_id if (not resolved or resolved == manager_id) else resolved
    print(f"[PUBLISH] Using customer_id: {customer_id} (manager={manager_id}, client={client_id})")

    result = create_campaign_from_report(
        customer_id=customer_id,
        refresh_token=session["refresh_token"],
        campaign_name=req.campaign_name,
        daily_budget_usd=req.daily_budget_usd,
        target_countries=req.target_countries,
        keywords=req.keywords,
        ad_headlines=req.headlines,
        ad_descriptions=req.descriptions,
        final_url=req.final_url,
    )
    if result.get("success"):
        _sessions[req.session_id]["customer_id"] = customer_id
        save_sessions(_sessions)
        register_campaign(
            campaign_resource_name=result["campaign_resource"],
            monthly_budget_usd=req.monthly_budget_usd,
            customer_id=customer_id,
            refresh_token=session["refresh_token"],
        )
    return result

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

    visit = log_visit(referrer, page, user_agent, ip, converted, conversion_value)
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

# ─── AI SEM Agent Routes ──────────────────────────────────────────────────────

from sem_agent import (
    chat_with_agent, get_agent_status, run_monitoring_cycle,
    generate_weekly_report, set_agent_active, clear_agent_chat,
    analyze_campaigns_with_gemini
)

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

    response = chat_with_agent(message, campaigns, session_id)
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
    from sem_agent import _agent_state
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
