"""
A kid's own personal Google Calendar: a push-only mirror.

Deliberately separate from calendar_oauth.py, which connects a PROVIDER's
calendar, read-only, so their sessions can be pulled in. This connects a
KID's own calendar so approved schedule changes can be written into it
(CalendarSyncService.push_to_kid_calendar) - the opposite direction, and a
different recipient. Kids never sign in independently in this app; the
parent authorises this on their behalf, exactly as they already do for a
provider's calendar.

Requires a Google Cloud Console redirect URI for this exact callback path
to be authorized on the same OAuth client calendar_oauth.py uses.
"""

import logging
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DbSession

from ..database.connection import get_db
from ..database.models import KidCalendarConnection, OAuthProvider, User
from ..routers.calendar_oauth import (
    CALENDAR_SCOPE,
    GOOGLE_AUTH_URL,
    GOOGLE_CALENDAR_LIST_URL,
    GOOGLE_TOKEN_URL,
    _store_google_token,
)
from ..utils.auth import (
    create_calendar_connect_state,
    decode_calendar_connect_state,
    get_current_user,
    verify_parent_account,
)
from ..utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar-sync/google/kid", tags=["Calendar Sync"])


def _redirect_uri() -> str:
    base_url = settings.BASE_URL or "http://localhost:8888"
    return f"{base_url}/calendar-sync/google/kid/callback"


def _owned_kid(db: DbSession, parent_id: int, child_id: int) -> User:
    child = (
        db.query(User)
        .filter(User.id == child_id, User.parent_id == parent_id, User.is_kid_account.is_(True))
        .first()
    )
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


def _upsert_kid_connection(
    db: DbSession, child_id: int, parent_id: int, connected_by_user_id: Optional[int] = None
) -> KidCalendarConnection:
    connection = (
        db.query(KidCalendarConnection).filter(KidCalendarConnection.child_id == child_id).first()
    )
    if connection is None:
        connection = KidCalendarConnection(child_id=child_id, parent_id=parent_id)
        db.add(connection)
    if connected_by_user_id is not None:
        connection.connected_by_user_id = connected_by_user_id
    return connection


@router.get("/list")
async def list_kids(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Every kid this parent could attach a personal-calendar push target to."""
    verify_parent_account(current_user)

    kids = (
        db.query(User)
        .filter(User.parent_id == current_user.id, User.is_kid_account.is_(True))
        .all()
    )
    connections = {
        row.child_id: row
        for row in db.query(KidCalendarConnection)
        .filter(KidCalendarConnection.child_id.in_([kid.id for kid in kids]))
        .all()
    }
    return [
        {
            "id": kid.id,
            "name": kid.display_name or kid.username,
            "calendar_connected": bool(
                connections.get(kid.id) and connections[kid.id].calendar_account_id
            ),
            "calendar_display_name": (
                connections[kid.id].calendar_display_name if kid.id in connections else None
            ),
        }
        for kid in kids
    ]


@router.get("/connect")
async def connect(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Send the signed-in parent to Google's consent screen for their kid's own calendar."""
    verify_parent_account(current_user)
    _owned_kid(db, current_user.id, child_id)

    state = create_calendar_connect_state(user_id=current_user.id, child_id=child_id)
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
    child_id = payload.get("child_id")
    if child_id is None:
        raise HTTPException(status_code=400, detail="Invalid connection link")

    parent = db.query(User).filter(User.id == user_id).first()
    if parent is None or parent.is_kid_account:
        raise HTTPException(status_code=403, detail="Not a parent account")

    child = _owned_kid(db, parent.id, child_id)

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

    _store_google_token(db, user_id=user_id, provider_user_id=str(user_id), token_json=token_json)
    _upsert_kid_connection(db, child_id=child.id, parent_id=parent.id, connected_by_user_id=user_id)
    db.commit()

    # calendar_account_id stays unset until the parent picks a calendar
    # below, same two-step shape as the provider-calendar picker.
    return RedirectResponse(
        url=f"/app/parent?tab=providers&choose_kid_calendar={child.id}", status_code=303
    )


@router.get("/calendars")
async def list_calendars(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Every calendar the just-connected Google account can WRITE to - unlike
    the provider picker (calendar_oauth.py), which only needs read access,
    this is a push target, so a read-only shared calendar would silently
    fail every write later. Filtered to writer/owner access for that
    reason.
    """
    verify_parent_account(current_user)
    child = _owned_kid(db, current_user.id, child_id)

    connection = (
        db.query(KidCalendarConnection)
        .filter(
            KidCalendarConnection.child_id == child.id,
            KidCalendarConnection.connected_by_user_id.isnot(None),
        )
        .first()
    )
    if connection is None:
        raise HTTPException(status_code=404, detail="No Google connection for this kid yet")

    link = (
        db.query(OAuthProvider)
        .filter(
            OAuthProvider.user_id == connection.connected_by_user_id,
            OAuthProvider.provider == "google",
        )
        .first()
    )
    if link is None or not link.access_token:
        raise HTTPException(status_code=404, detail="No Google token for this kid yet")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_CALENDAR_LIST_URL,
            headers={"Authorization": f"Bearer {link.access_token}"},
            params={"minAccessRole": "writer"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not read the calendar list")

    items = response.json().get("items", [])
    calendars = [
        {
            "id": item["id"],
            "summary": item.get("summary") or item["id"],
            "primary": bool(item.get("primary")),
        }
        for item in items
        if item.get("id")
    ]
    calendars.sort(key=lambda c: not c["primary"])
    return {"calendars": calendars}
