"""
Google Calendar connect: a small, isolated OAuth flow.

Deliberately separate from oauth_simple.py's sign-in flow (proven working
end-to-end with real credentials this session, and left untouched here to
keep its blast radius small) and from oauth_service.py's generic-login
linking flow (whose "google" client only ever requests identity scopes,
never calendar access - see calendar_sync_service.py's docstring history
for why that made Google Calendar sync silently non-functional). This
flow exists for exactly one purpose: let an already-signed-in parent grant
Mew read access to a Google Calendar for one of their providers.

Requires a Google Cloud Console redirect URI for this exact callback path
to be authorized on the OAuth client, same as the one already added for
oauth_simple.py's sign-in callback.
"""

import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DbSession

from ..database.connection import get_db
from ..database.models import OAuthProvider, ProviderOrg, User
from ..routers.calendar_sync import _upsert_connection
from ..utils.auth import (
    create_calendar_connect_state,
    decode_calendar_connect_state,
    get_current_user,
    verify_parent_account,
)
from ..utils.config import settings
from ..utils.log_sanitizer import sanitize_email, sanitize_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar-sync/google", tags=["Calendar Sync"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def _redirect_uri() -> str:
    base_url = settings.BASE_URL or "http://localhost:8888"
    return f"{base_url}/calendar-sync/google/callback"


@router.get("/connect")
async def connect(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Send the signed-in parent to Google's consent screen for one org's calendar."""
    verify_parent_account(current_user)

    org = db.query(ProviderOrg).filter(ProviderOrg.id == org_id).first()
    if org is None:
        raise HTTPException(status_code=404, detail="Provider organisation not found")

    state = create_calendar_connect_state(user_id=current_user.id, org_id=org_id)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": f"openid email {CALENDAR_SCOPE}",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: DbSession = Depends(get_db),
):
    """
    Exchange the code, re-verify who this is really for (the signed state,
    not anything the browser sends), and store the token.
    """
    if error:
        safe_error = str(error).replace("\n", "").replace("\r", "")[:100]
        raise HTTPException(status_code=400, detail=f"Google Calendar connection failed: {safe_error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    payload = decode_calendar_connect_state(state)
    user_id = payload["user_id"]
    org_id = payload["org_id"]

    parent = db.query(User).filter(User.id == user_id).first()
    if parent is None or parent.is_kid_account:
        raise HTTPException(status_code=403, detail="Not a parent account")

    org = db.query(ProviderOrg).filter(ProviderOrg.id == org_id).first()
    if org is None:
        raise HTTPException(status_code=404, detail="Provider organisation not found")

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": _redirect_uri(),
            },
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token from Google")
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token in Google's response")

        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get account info from Google")
        user_info = userinfo_response.json()

    logger.info(
        "Google Calendar connected: %s for %s",
        sanitize_email(user_info.get("email")),
        sanitize_user_id(user_id),
    )

    _store_google_token(db, user_id=user_id, provider_user_id=user_info.get("id") or str(user_id), token_json=token_json)
    _upsert_connection(db, org_id=org.id, parent_id=user_id, connected_by_user_id=user_id)
    db.commit()

    return RedirectResponse(url="/app/parent?tab=providers", status_code=303)


def _store_google_token(db: DbSession, user_id: int, provider_user_id: str, token_json: dict) -> None:
    """Find-or-update, matching oauth_service.py's existing pattern - never a blind insert."""
    link = (
        db.query(OAuthProvider)
        .filter(OAuthProvider.user_id == user_id, OAuthProvider.provider == "google")
        .first()
    )
    expires_in = token_json.get("expires_in")
    expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None

    if link is None:
        db.add(
            OAuthProvider(
                user_id=user_id,
                provider="google",
                provider_user_id=provider_user_id,
                access_token=token_json.get("access_token"),
                refresh_token=token_json.get("refresh_token"),
                token_expires_at=expires_at,
            )
        )
        return

    link.access_token = token_json.get("access_token")
    if token_json.get("refresh_token"):
        link.refresh_token = token_json.get("refresh_token")
    link.token_expires_at = expires_at
    link.updated_at = datetime.utcnow()
