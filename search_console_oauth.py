path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(path) as f:
    content = f.read()

sc_code = '''
# ─── SEARCH CONSOLE OAUTH ────────────────────────────────────────────────────

SC_CLIENT_ID = os.environ.get("SEARCH_CONSOLE_CLIENT_ID", "")
SC_CLIENT_SECRET = os.environ.get("SEARCH_CONSOLE_CLIENT_SECRET", "")
SC_REDIRECT_URI = os.environ.get("SEARCH_CONSOLE_REDIRECT_URI", "https://sem-ai-production.up.railway.app/api/search-console/callback")
SC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# In-memory token store (per session)
sc_tokens = {}

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
                sc_tokens[state] = tokens
                return HTMLResponse("""
                <html><body style="font-family:sans-serif;text-align:center;padding:50px;background:#0f172a;color:white">
                <h2>✅ Search Console Connected!</h2>
                <p>You can close this window and return to SEM AI.</p>
                <script>
                  window.opener && window.opener.postMessage({type:'SC_AUTH_SUCCESS'}, '*');
                  setTimeout(() => window.close(), 2000);
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
    return {"connected": session_id in sc_tokens}

@app.post("/api/search-console/data")
async def get_search_console_data(request: Request):
    """Fetch Search Console data for a URL."""
    try:
        body = await request.json()
        url = body.get("url", "")
        session_id = body.get("session_id", "default")
        days = body.get("days", 28)
        
        if session_id not in sc_tokens:
            return {"error": "Search Console not connected", "connected": False}
        
        tokens = sc_tokens[session_id]
        access_token = tokens.get("access_token", "")
        
        # Get site URL from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        site_url = f"{parsed.scheme}://{parsed.netloc}/"
        
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            # Get search analytics for this page
            resp = await client.post(
                f"https://searchconsole.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "startDate": start_date,
                    "endDate": end_date,
                    "dimensions": ["query"],
                    "dimensionFilterGroups": [{
                        "filters": [{
                            "dimension": "page",
                            "operator": "equals",
                            "expression": url
                        }]
                    }],
                    "rowLimit": 20,
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
                        sc_tokens[session_id].update(new_tokens)
                        return {"error": "Token refreshed, please retry"}
                return {"error": "Authentication expired, please reconnect"}
            
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
                ]
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "connected": False}

'''

# Add before agent routes
if '/api/search-console/auth' not in content:
    # Add HTMLResponse import
    if 'HTMLResponse' not in content:
        content = content.replace(
            'from fastapi import FastAPI',
            'from fastapi import FastAPI\nfrom fastapi.responses import HTMLResponse'
        )
    
    content = content.replace(
        '@app.get("/api/agent/status")',
        sc_code + '@app.get("/api/agent/status")'
    )
    print("Search Console OAuth added!")
else:
    print("Already exists!")

with open(path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)
