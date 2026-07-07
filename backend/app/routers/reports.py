import asyncio
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from jose import jwt, JWTError

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.scraper import scrape_website
from app.services.prompts import build_seo_prompt, build_ad_prompt
from app.services.gemini import call_gemini, parse_ai_json
from app.database import get_db
from app.models.user import User
from app.models.report import Report
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api", tags=["reports"])
security = HTTPBearer()

PLAN_LIMITS = {
    "free": 3,
    "pro": 50,
    "agency": 999999
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class FullReportRequest(BaseModel):
    url: str
    business_description: Optional[str] = ""
    target_keywords: Optional[list[str]] = []


@router.post("/full-report")
async def full_report(
    req: FullReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Plan limit check
    limit = PLAN_LIMITS.get(current_user.plan, 3)
    if current_user.reports_used >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Report limit reached for {current_user.plan} plan. Please upgrade."
        )

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
        raise HTTPException(status_code=500, detail=f"SEO JSON parse error: {str(e)}")

    try:
        ad_copy = parse_ai_json(ad_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ad JSON parse error: {str(e)}")

    # Save report to DB
    report = Report(
        user_id=current_user.id,
        url=url,
        seo_report=seo_report,
        ad_copy=ad_copy,
        scraped_data={
            "title": scraped["title"],
            "meta_description": scraped["meta_description"],
            "h1_tags": scraped["h1_tags"],
            "images_count": scraped["images_count"],
            "images_without_alt_count": scraped["images_without_alt_count"],
            "internal_links_count": scraped["internal_links_count"],
            "has_schema_markup": scraped["has_schema_markup"],
            "html_size_kb": scraped["html_size_kb"],
        }
    )
    db.add(report)

    # Increment usage
    current_user.reports_used += 1
    db.commit()

    return {
        "report_id": str(report.id),
        "url": url,
        "scraped_data": report.scraped_data,
        "seo_report": seo_report,
        "ad_copy": ad_copy,
        "usage": {
            "used": current_user.reports_used,
            "limit": limit,
            "plan": current_user.plan
        }
    }


@router.get("/reports")
def get_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).filter(
        Report.user_id == current_user.id
    ).order_by(Report.created_at.desc()).all()

    return {
        "reports": [
            {
                "id": str(r.id),
                "url": r.url,
                "seo_score": r.seo_report.get("overall_seo_score") if r.seo_report else None,
                "created_at": r.created_at.isoformat()
            }
            for r in reports
        ]
    }
