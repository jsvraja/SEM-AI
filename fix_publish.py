path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

# Find and wrap entire publish_campaign function
start = content.find('async def publish_campaign(req: PublishCampaignRequest):')
end = content.find('\n@app.', start + 10)

old_func = content[start:end]
print("Function found, length:", len(old_func))

new_func = '''async def publish_campaign(req: PublishCampaignRequest):
    try:
        session = _sessions.get(req.session_id)
        if not session or not session.get("refresh_token"):
            raise HTTPException(status_code=401, detail="Not authenticated. Go to /auth/google to reconnect.")
        if req.daily_budget_usd < 1.0:
            raise HTTPException(status_code=400, detail=f"Daily budget too low")

        customer_id = req.customer_id or session.get("customer_id", os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", ""))
        refresh_token = session["refresh_token"]

        result = create_google_ads_campaign(
            customer_id=customer_id,
            refresh_token=refresh_token,
            campaign_name=req.campaign_name,
            daily_budget_usd=req.daily_budget_usd,
            target_countries=req.target_countries,
            keywords=req.keywords,
            headlines=req.headlines,
            descriptions=req.descriptions,
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
'''

content = content[:start] + new_func + content[end:]

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)
