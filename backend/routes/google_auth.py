# Google OAuth 2.0 (Authorization Code + OIDC) for Mera Mentor.
# Uses the user's own Google Cloud OAuth 2.0 Web Application credentials.
# Reads all secrets from environment variables — nothing is hardcoded.
from __future__ import annotations

import hashlib
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
from lib.settings import request_origin

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


LANDING_PATH = "/courses/data-analytics"
CALLBACK_PATH = "/api/auth/google/callback"


def _check_google_config():
    names = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    missing = [name for name in names if not os.environ.get(name, "").strip()]
    if missing:
        raise HTTPException(503, f"Google sign-in is not configured. Missing: {', '.join(missing)}")


def _redirect_uri(request: Request) -> str:
    """GOOGLE_REDIRECT_URI if set, else built from the incoming request (https behind Render's proxy)."""
    configured = os.environ.get("GOOGLE_REDIRECT_URI", "").strip()
    if configured:
        return configured
    origin = request_origin(request)
    if not origin:
        raise HTTPException(400, "Could not determine this site's address for Google sign-in")
    return f"{origin}{CALLBACK_PATH}"


def _serializer() -> URLSafeTimedSerializer:
    # SESSION_SECRET is optional; otherwise derive a stable signing key from the Google client secret.
    secret = os.environ.get("SESSION_SECRET", "").strip() or hashlib.sha256(
        b"mera-mentor-oauth-state:" + _env("GOOGLE_CLIENT_SECRET").encode()).hexdigest()
    return URLSafeTimedSerializer(secret, salt="google-oauth-state-v1")


def _auth_failed(reason: str) -> RedirectResponse:
    """Send the student back to the landing page with a short error, never a blank JSON screen."""
    resp = RedirectResponse(f"{LANDING_PATH}?{urlencode({'auth_error': reason})}", status_code=302)
    resp.delete_cookie("google_oauth_state", path="/api/auth/google")
    return resp


def _generate_referral_code() -> str:
    import random
    return "MMM" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))


@router.get("/login")
async def google_login(request: Request,
                       ref: str | None = Query(default=None, max_length=100),
                       visitor_id: UUID | None = None,
                       browser_type: Literal["instagram", "facebook", "browser"] = "browser",
                       intent: Literal["signup", "purchase"] = "signup"):
    """Redirect the user to Google's consent screen."""
    _check_google_config()
    client_id = _env("GOOGLE_CLIENT_ID")
    redirect_uri = _redirect_uri(request)
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
    try:
        _check_google_config()
    except HTTPException:
        return _auth_failed("not_configured")

    if error:
        return _auth_failed("cancelled" if error == "access_denied" else "failed")
    if not code or not state:
        return _auth_failed("failed")

    # 1) State validation (CSRF)
    expected_state = request.cookies.get("google_oauth_state")
    if not expected_state or not secrets.compare_digest(state, expected_state):
        return _auth_failed("expired")
    try:
        state_data = _serializer().loads(state, max_age=600)
    except (BadSignature, SignatureExpired):
        return _auth_failed("expired")

    client_id = _env("GOOGLE_CLIENT_ID")
    client_secret = _env("GOOGLE_CLIENT_SECRET")
    try:
        redirect_uri = _redirect_uri(request)
    except HTTPException:
        return _auth_failed("failed")

    # 2) Token exchange
    try:
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
    except httpx.HTTPError:
        return _auth_failed("failed")
    if token_resp.status_code != 200:
        return _auth_failed("failed")

    tokens = token_resp.json()
    raw_id_token = tokens.get("id_token")
    if not raw_id_token:
        return _auth_failed("failed")

    # 3) ID token verification
    try:
        claims = id_token.verify_oauth2_token(
            raw_id_token, google_requests.Request(), client_id
        )
    except ValueError:
        return _auth_failed("failed")

    if claims.get("aud") != client_id:
        return _auth_failed("failed")
    if not secrets.compare_digest(str(claims.get("nonce", "")), str(state_data.get("nonce", ""))):
        return _auth_failed("failed")
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        return _auth_failed("failed")
    if not claims.get("email") or not claims.get("sub"):
        return _auth_failed("failed")
    if not claims.get("email_verified", False):
        return _auth_failed("unverified_email")

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

    # 6) Redirect back to the frontend with cookie (same domain, so a relative path)
    dashboard_url = "/dashboard"
    if state_data.get("intent") == "purchase":
        query = {"checkout": "1", "source_browser": state_data.get("browser_type", "browser")}
        if state_data.get("visitor_id"):
            query["visitor"] = state_data["visitor_id"]
        if state_data.get("ref"):
            query["ref"] = state_data["ref"]
        dashboard_url = f"{LANDING_PATH}?{urlencode(query)}#pricing"
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
