"""
Google OAuth 2.0 handler for Google Ads authentication.
Handles the full OAuth flow: redirect → callback → token storage
"""

import os
import json
import httpx
from urllib.parse import urlencode


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def get_oauth_url(state: str = "sem-ai") -> str:
    """Generate the Google OAuth redirect URL."""
    params = {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"),
            "grant_type": "authorization_code",
        })
        return response.json()


async def get_user_info(access_token: str) -> dict:
    """Get Google user info from access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Refresh an expired access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "grant_type": "refresh_token",
        })
        return response.json()
