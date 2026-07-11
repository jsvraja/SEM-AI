from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt
import os
import httpx

from app.database import get_db
from app.models.user import User
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["google-auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://believable-rebirth-production-7e19.up.railway.app")


@router.get("/auth/google")
async def google_login():
    redirect_uri = f"https://sem-ai-production.up.railway.app/auth/google/callback"
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    redirect_uri = f"https://sem-ai-production.up.railway.app/auth/google/callback"

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        )
        token_data = token_res.json()

        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error"])

        # Get user info
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_info = user_res.json()

    email = user_info.get("email")
    name = user_info.get("name", "")

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google")

    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password="google_oauth",
            full_name=name,
            plan="free"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create JWT token
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": str(user.id), "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    user_data = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "plan": user.plan,
        "reports_used": user.reports_used
    }

    # Redirect to frontend with token
    import json, urllib.parse
    user_json = urllib.parse.quote(json.dumps(user_data))
    return RedirectResponse(
        url=f"{FRONTEND_URL}?token={token}&user={user_json}"
    )
