"""Google OAuth authentication and session management."""

import os
import time
import secrets
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer
import httpx

from forum_db import upsert_user, get_user_by_id, is_banned

auth_router = APIRouter(tags=["auth"])

# Config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FORUM_SECRET_KEY = os.getenv("FORUM_SECRET_KEY", "change-me-to-a-random-secret")
FORUM_BASE_URL = os.getenv("FORUM_BASE_URL", "http://localhost:8000")
FORUM_ADMIN_EMAILS = [
    e.strip() for e in os.getenv("FORUM_ADMIN_EMAILS", "").split(",") if e.strip()
]

SESSION_MAX_AGE = 7 * 24 * 3600  # 7 days
serializer = URLSafeTimedSerializer(FORUM_SECRET_KEY)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# ── Rate limiting for login ──
_login_attempts: dict = {}  # ip -> [timestamps]


def _check_login_rate(ip: str):
    """Allow max 10 login attempts per IP per minute."""
    now = time.time()
    window = [t for t in _login_attempts.get(ip, []) if now - t < 60]
    if len(window) >= 10:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please wait a moment.")
    window.append(now)
    _login_attempts[ip] = window


def get_current_user(request: Request) -> dict | None:
    """Returns user dict or None if not logged in / banned."""
    token = request.cookies.get("forum_session")
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        user = get_user_by_id(data["user_id"])
        if not user:
            return None
        if is_banned(user["id"]):
            return None
        return user
    except Exception:
        return None


def require_auth(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(request: Request) -> dict:
    user = require_auth(request)
    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


@auth_router.get("/auth/login")
def auth_login(request: Request, redirect_to: str = "/forum"):
    """Redirect to Google OAuth consent screen."""
    _check_login_rate(request.client.host)
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    # Only allow relative redirects to prevent open redirect attacks
    if not redirect_to.startswith("/"):
        redirect_to = "/forum"

    state = serializer.dumps({"nonce": secrets.token_hex(16), "redirect_to": redirect_to})
    redirect_uri = f"{FORUM_BASE_URL}/auth/callback"

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    url = f"{GOOGLE_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    response = RedirectResponse(url=url)
    response.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax")
    return response


@auth_router.get("/auth/callback")
def auth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    """Handle Google OAuth callback."""
    if error:
        return RedirectResponse(url="/forum")

    # Verify state
    saved_state = request.cookies.get("oauth_state", "")
    if not state or state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Extract redirect_to from state
    try:
        state_data = serializer.loads(state, max_age=600)
        redirect_after = state_data.get("redirect_to", "/forum")
    except Exception:
        redirect_after = "/forum"
    if not redirect_after.startswith("/"):
        redirect_after = "/forum"

    redirect_uri = f"{FORUM_BASE_URL}/auth/callback"

    # Exchange code for tokens
    with httpx.Client(timeout=10) as client:
        token_resp = client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")
        tokens = token_resp.json()

        # Fetch user info
        userinfo_resp = client.get(GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")
        userinfo = userinfo_resp.json()

    # Override identity for admin accounts
    email = userinfo.get("email", "")
    display_name = userinfo.get("name", "Anonymous")
    avatar_url = userinfo.get("picture", "")
    if email.lower() in [e.lower() for e in FORUM_ADMIN_EMAILS]:
        display_name = "Lunatic"
        avatar_url = "/static/lunatic-avatar.png"

    # Upsert user in DB
    user = upsert_user(
        google_id=userinfo["sub"],
        email=email,
        display_name=display_name,
        avatar_url=avatar_url,
        admin_emails=FORUM_ADMIN_EMAILS,
    )

    # Set session cookie
    session_token = serializer.dumps({"user_id": user["id"]})
    response = RedirectResponse(url=redirect_after)
    response.set_cookie(
        "forum_session", session_token,
        max_age=SESSION_MAX_AGE, httponly=True, samesite="lax", path="/",
    )
    response.delete_cookie("oauth_state")
    return response


@auth_router.get("/auth/logout")
def auth_logout(redirect_to: str = "/"):
    if not redirect_to.startswith("/"):
        redirect_to = "/"
    response = RedirectResponse(url=redirect_to)
    response.delete_cookie("forum_session", path="/")
    return response


@auth_router.get("/api/auth/me")
def auth_me(request: Request):
    user = get_current_user(request)
    if not user:
        return None
    return {
        "id": user["id"],
        "display_name": user["display_name"],
        "avatar_url": user["avatar_url"],
        "email": user["email"],
        "is_admin": bool(user["is_admin"]),
    }
