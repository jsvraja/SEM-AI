from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import json

from app.database import get_db
from app.models.user import User
from app.routers.reports import get_current_user

router = APIRouter(prefix="/api/search-console", tags=["search-console"])

GOOGLE_CLIENT_ID = os.environ.get("SEARCH_CONSOLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("SEARCH_CONSOLE_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("SEARCH_CONSOLE_REDIRECT_URI", "https://sem-ai-production.up.railway.app/api/search-console/callback")
FRONTEND_URL = "https://believable-rebirth-production-7e19.up.railway.app"

SCOPES = "https://www.googleapis.com/auth/webmasters.readonly"


@router.get("/auth")
async def search_console_auth(session_id: str = ""):
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={session_id}"
    )
    return {"auth_url": auth_url}


@router.get("/callback")
async def search_console_callback(code: str, state: str = "", db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )
        token_data = token_res.json()

    if "error" in token_data:
        return RedirectResponse(url=f"{FRONTEND_URL}?gsc_error={token_data['error']}")

    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")

    return RedirectResponse(
        url=f"{FRONTEND_URL}?gsc_token={access_token}&gsc_refresh={refresh_token}&session_id={state}"
    )


class SearchConsoleDataRequest(BaseModel):
    session_id: Optional[str] = ""
    url: str
    days: int = 28
    gsc_token: Optional[str] = ""


@router.post("/data")
async def get_search_console_data(req: SearchConsoleDataRequest):
    token = req.gsc_token or ""
    
    if not token:
        raise HTTPException(status_code=401, detail="No Search Console token")

    site_url = req.url
    if not site_url.startswith("sc-domain:"):
        if not site_url.startswith("http"):
            site_url = "https://" + site_url

    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=req.days)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        # Get keywords
        # Try with https:// URL first, then sc-domain:
        urls_to_try = [site_url, f"sc-domain:{site_url.replace('https://','').replace('http://','').rstrip('/')}"]
        kw_data = {"rows": []}
        page_data = {"rows": []}
        
        for try_url in urls_to_try:
            kw_res = await client.post(
                f"https://searchconsole.googleapis.com/webmasters/v3/sites/{try_url}/searchAnalytics/query",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "startDate": start_date,
                    "endDate": end_date,
                    "dimensions": ["query"],
                    "rowLimit": 20
                }
            )
            if kw_res.status_code == 200 and kw_res.content:
                try:
                    kw_data = kw_res.json()
                    # Get pages with same URL
                    page_res = await client.post(
                        f"https://searchconsole.googleapis.com/webmasters/v3/sites/{try_url}/searchAnalytics/query",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "startDate": start_date,
                            "endDate": end_date,
                            "dimensions": ["page"],
                            "rowLimit": 10
                        }
                    )
                    if page_res.status_code == 200 and page_res.content:
                        page_data = page_res.json()
                    break
                except:
                    continue

    keywords = [
        {
            "keyword": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 1)
        }
        for row in kw_data.get("rows", [])
    ]

    pages = [
        {
            "page": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 1)
        }
        for row in page_data.get("rows", [])
    ]

    total_clicks = sum(p["clicks"] for p in pages) if pages else sum(k["clicks"] for k in keywords)
    total_impressions = sum(p["impressions"] for p in pages) if pages else sum(k["impressions"] for k in keywords)
    avg_ctr = round(sum(k["ctr"] for k in keywords) / len(keywords), 2) if keywords else 0
    avg_position = round(sum(k["position"] for k in keywords) / len(keywords), 1) if keywords else 0

    return {
        "keywords": keywords,
        "pages": pages,
        "summary": {
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": avg_ctr,
            "avg_position": avg_position,
            "date_range": f"{start_date} to {end_date}"
        }
    }


@router.post("/refresh-token")
async def refresh_token(body: dict):
    refresh_tok = body.get("refresh_token", "")
    if not refresh_tok:
        raise HTTPException(status_code=400, detail="No refresh token")
    
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "refresh_token": refresh_tok,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "grant_type": "refresh_token",
            }
        )
        data = res.json()
    
    if "access_token" in data:
        return {"access_token": data["access_token"]}
    raise HTTPException(status_code=400, detail="Token refresh failed")
