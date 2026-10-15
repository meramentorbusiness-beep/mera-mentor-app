# Google OAuth 2.0 (Authorization Code + OIDC) for Mera Mentor.
# Uses the user's own Google Cloud OAuth 2.0 Web Application credentials.
# Reads all secrets from environment variables — nothing is hardcoded.
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from typing import Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lib.database import get_db
from models.models import User, UserSession
from routes.landing import record_event
from lib.settings import frontend_url

router = APIRouter(prefix="/api/auth/google", tags=["google-auth"])

SCOPES = "openid email profile"
AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# Lazy env-var reads so import time never fails when developing without OAuth set.
def _env(name: str, required: bool = True) -> str:
    val = os.environ.get(name, "").strip()
    if required and not val:
        raise HTTPException(
            status_code=503,
            detail=f"{name} is not set on the server. See README for OAuth setup.",
        )
    return val


def _check_google_config():
    names = ("FRONTEND_URL", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "SESSION_SECRET")
    missing = [name for name in names if not os.environ.get(name, "").strip()]
    if missing:
        raise HTTPException(503, f"Google sign-in is not configured. Missing: {', '.join(missing)}")
    if not frontend_url():
        raise HTTPException(503, "FRONTEND_URL must be a full HTTP(S) origin, without a path or comma-separated URLs")


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(_env("SESSION_SECRET"), salt="google-oauth-state-v1")


def _generate_referral_code() -> str:
    import random
    return "MMM" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))


@router.get("/login")
async def google_login(ref: str | None = Query(default=None, max_length=100),
                       visitor_id: UUID | None = None,
                       browser_type: Literal["instagram", "facebook", "browser"] = "browser",
                       intent: Literal["signup", "purchase"] = "signup"):
    """Redirect the user to Google's consent screen."""
    _check_google_config()
    client_id = _env("GOOGLE_CLIENT_ID")
    redirect_uri = _env("GOOGLE_REDIRECT_URI")
    ref = ref.strip() if ref else None

    nonce = secrets.token_urlsafe(32)
    state = _serializer().dumps({"nonce": nonce, "ref": ref,
        "visitor_id": str(visitor_id) if visitor_id else None,
        "browser_type": browser_type, "intent": intent})

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "nonce": nonce,
        "prompt": "select_account",
        "access_type": "online",
    }
    url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

    resp = RedirectResponse(url, status_code=302)
    # Bind the state to this browser so an attacker can't forge a callback.
    resp.set_cookie(
        "google_oauth_state",
        state,
        max_age=600,
        httponly=True,
        secure=True,
        samesite="none",
        path="/api/auth/google",
    )
    return resp


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google's redirect: exchange code, verify id_token, issue session cookie."""
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    _check_google_config()
    frontend_base = frontend_url()
    login_url = f"{frontend_base}/courses/data-analytics"

    if error:
        return RedirectResponse(f"{login_url}?{urlencode({'auth_error': error})}", status_code=302)
    if not code or not state:
        raise HTTPException(400, "Missing Google authorization code or state")

    # 1) State validation (CSRF)
    expected_state = request.cookies.get("google_oauth_state")
    if not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(400, "Invalid OAuth state")
    try:
        state_data = _serializer().loads(state, max_age=600)
    except (BadSignature, SignatureExpired):
        raise HTTPException(400, "Expired or invalid OAuth state")

    client_id = _env("GOOGLE_CLIENT_ID")
    client_secret = _env("GOOGLE_CLIENT_SECRET")
    redirect_uri = _env("GOOGLE_REDIRECT_URI")

    # 2) Token exchange
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if token_resp.status_code != 200:
        raise HTTPException(400, "Google token exchange failed")

    tokens = token_resp.json()
    raw_id_token = tokens.get("id_token")
    if not raw_id_token:
        raise HTTPException(400, "Google did not return an ID token")

    # 3) ID token verification
    try:
        claims = id_token.verify_oauth2_token(
            raw_id_token, google_requests.Request(), client_id
        )
    except ValueError:
        raise HTTPException(400, "Invalid Google ID token")

    if claims.get("aud") != client_id:
        raise HTTPException(400, "Invalid Google token audience")
    if not secrets.compare_digest(str(claims.get("nonce", "")), str(state_data.get("nonce", ""))):
        raise HTTPException(400, "Invalid Google token nonce")
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(400, "Invalid Google token issuer")
    if not claims.get("email") or not claims.get("sub"):
        raise HTTPException(400, "Google token lacks required identity claims")
    if not claims.get("email_verified", False):
        raise HTTPException(403, "Google email is not verified")

    google_id = claims["sub"]
    email = claims["email"].lower().strip()
    name = claims.get("name") or email.split("@", 1)[0]
    picture = claims.get("picture")

    # 4) Look up or create the user
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user is None:
        # Fallback: link by verified email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    admin_emails = [
        e.strip() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()
    ]

    is_new_user = user is None
    if is_new_user:
        # New user — build referral chain from state
        referral_chain: list[str] = []
        referred_by_id: str | None = None
        referral_code = state_data.get("ref")

        if referral_code:
            ref_result = await db.execute(
                select(User).where(User.referral_code == referral_code)
            )
            referrer = ref_result.scalar_one_or_none()
            if referrer:
                referred_by_id = str(referrer.id)
                referral_chain = [str(referrer.id)] + (referrer.referral_chain or [])[:4]

        user = User(
            email=email,
            name=name,
            avatar=picture,
            google_id=google_id,
            referral_code=_generate_referral_code(),
            referred_by_id=referred_by_id,
            referral_chain=referral_chain,
            email_verified=True,
            role="admin" if email in admin_emails else "user",
        )
        db.add(user)
        await db.flush()  # gets user.id before session insert
    else:
        # Returning user — refresh profile fields, do NOT re-apply referral
        if not user.google_id:
            user.google_id = google_id
        user.name = name or user.name
        if picture:
            user.avatar = picture

    # 5) Issue session
    session_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db.add(UserSession(
        session_token=session_token,
        user_id=str(user.id),
        expires_at=expires_at,
    ))
    if is_new_user and state_data.get("visitor_id"):
        await record_event(db, event_id=f"signup:{user.id}", visitor_id=state_data["visitor_id"],
            event="signup_completed", browser_type=state_data.get("browser_type", "browser"),
            referral_code=state_data.get("ref"))
    await db.commit()

    # 6) Redirect back to the frontend with cookie
    dashboard_url = f"{frontend_base}/dashboard"
    if state_data.get("intent") == "purchase":
        query = {"checkout": "1", "source_browser": state_data.get("browser_type", "browser")}
        if state_data.get("visitor_id"):
            query["visitor"] = state_data["visitor_id"]
        if state_data.get("ref"):
            query["ref"] = state_data["ref"]
        dashboard_url = f"{frontend_base}/courses/data-analytics?{urlencode(query)}#pricing"
    resp = RedirectResponse(dashboard_url, status_code=302)
    resp.delete_cookie("google_oauth_state", path="/api/auth/google")
    resp.set_cookie(
        "session_token",
        session_token,
        max_age=30 * 24 * 60 * 60,
        expires=int(expires_at.timestamp()),
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )
    return resp
