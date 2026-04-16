with open('/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py', 'r') as f:
    content = f.read()

endpoints = """
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
    prompt = f"Professional social media content for {domain}. Services: {services or 'technology'}. Keywords: {', '.join(keywords) or 'AI'}. Topic: {custom_topic or 'Brand awareness'}. Platforms: {', '.join(platforms)}.\\nRespond ONLY valid JSON: {{\\\"posts\\\":[{{\\\"platform\\\":\\\"linkedin\\\",\\\"type\\\":\\\"service\\\",\\\"content\\\":\\\"post text\\\",\\\"hashtags\\\":[\\\"tag1\\\"],\\\"best_time\\\":\\\"Tuesday 9AM\\\"}}]}}"
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
    prompt = f"SEO analyst: analyse {url} vs {', '.join(competitors)} (score:{seo_score}, keywords:{', '.join(keywords)}).\\nRespond ONLY valid JSON: {{\\\"my_site\\\":{{\\\"domain\\\":\\\"{domain}\\\",\\\"score\\\":{seo_score},\\\"strengths\\\":[\\\"s1\\\"],\\\"weaknesses\\\":[\\\"w1\\\"]}},\\\"competitors\\\":[{{\\\"domain\\\":\\\"x.com\\\",\\\"estimated_score\\\":70,\\\"estimated_traffic\\\":\\\"10k/month\\\",\\\"top_keywords\\\":[\\\"kw1\\\"],\\\"strengths\\\":[\\\"s1\\\"],\\\"weaknesses\\\":[\\\"w1\\\"],\\\"ad_strategy\\\":\\\"desc\\\",\\\"social_presence\\\":\\\"desc\\\"}}],\\\"opportunities\\\":[\\\"o1\\\"],\\\"threats\\\":[\\\"t1\\\"],\\\"action_plan\\\":[\\\"a1\\\"]}}"
    try:
        import re as _re, json as _json
        raw = await call_gemini(prompt)
        clean = _re.sub(r"```json|```", "", raw).strip()
        return _json.loads(clean)
    except Exception as e:
        return {"error": str(e)}

"""

content = content.replace(
    "# ─── AI SEM Agent Routes",
    endpoints + "\n# ─── AI SEM Agent Routes"
)

with open('/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py', 'w') as f:
    f.write(content)

with open('/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py') as f:
    c = f.read()
print("social:", "/api/social/generate" in c)
print("analyze:", "/api/competitor/analyze" in c)
