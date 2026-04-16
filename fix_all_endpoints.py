import re

path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path, 'r') as f:
    content = f.read()

# Find insertion point - before agent/status endpoint
marker = '@app.get("/api/agent/status")'
if marker not in content:
    print("ERROR: Cannot find insertion point")
    exit(1)

new_endpoints = '''
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


'''

content = content.replace(marker, new_endpoints + marker)

with open(path, 'w') as f:
    f.write(content)

with open(path) as f:
    c = f.read()
print("social/generate:", "/api/social/generate" in c)
print("competitor/analyze:", "/api/competitor/analyze" in c)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("Syntax ERROR:", e)
