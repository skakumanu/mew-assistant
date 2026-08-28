"""
Sign-in, via WorkOS AuthKit.

WorkOS sits at the front door only: its hosted UI is where a parent
actually enters a password, picks Google/Microsoft/Apple, or gets a
passwordless magic-code email - this app never sees a credential. Once
WorkOS confirms who they are, this callback exchanges that for the exact
same session this app has always used (create_access_token + the
mew_session cookie), so get_current_user and everything built on it needs
no changes at all.

Kid accounts are untouched by this file: it only ever creates/looks up
UserRole.PARENT accounts. Kid accounts stay parent-managed, accessed via
an already-signed-in device rather than an independent login.
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import User, UserRole
from ..services.workos_client import get_workos_client
from ..utils.auth import ACCESS_TOKEN_EXPIRE_MINUTES, SESSION_COOKIE, create_access_token
from ..utils.config import settings
from ..utils.log_sanitizer import sanitize_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/workos", tags=["Sign in"])


def _redirect_uri() -> str:
    base_url = settings.BASE_URL or "http://localhost:8888"
    return f"{base_url}/auth/workos/callback"


@router.get("/login")
async def login(next: str = "/app/parent"):
    """Send the browser to WorkOS's hosted sign-in UI."""
    from .mew_ui import _safe_next

    client = get_workos_client()
    authorization_url = client.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=_redirect_uri(),
        state=_safe_next(next),
    )
    return RedirectResponse(url=authorization_url, status_code=303)


@router.get("/callback")
async def callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: DbSession = Depends(get_db),
):
    """Exchange the code for a WorkOS identity, then start our own session."""
    from .mew_ui import _safe_next

    if error or not code:
        safe_error = str(error or "no code").replace("\n", "").replace("\r", "")[:100]
        logger.warning(f"WorkOS sign-in did not complete: {safe_error}")
        return RedirectResponse(url="/app/sign-in?error=1", status_code=303)

    try:
        client = get_workos_client()
        resp = await client.user_management.authenticate_with_code(code=code)
    except Exception as exc:
        logger.error(f"WorkOS code exchange failed: {exc}", exc_info=True)
        return RedirectResponse(url="/app/sign-in?error=1", status_code=303)

    workos_user = resp.user
    if not workos_user.email_verified:
        logger.warning("WorkOS sign-in rejected: email not verified")
        raise HTTPException(status_code=400, detail="Email not verified")

    email = workos_user.email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            email=email,
            full_name=workos_user.name or email.split("@")[0],
            role=UserRole.PARENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user via WorkOS: {sanitize_email(email)}")
    else:
        logger.info(f"User signed in via WorkOS: {sanitize_email(email)}")

    token_data = {"sub": user.email, "user_id": user.id, "role": user.role.value}
    jwt_token = create_access_token(token_data)

    has_children = (
        db.query(User)
        .filter(User.parent_id == user.id, User.is_kid_account.is_(True))
        .first()
        is not None
    )
    # `state` round-trips whatever /app/sign-in?next=... asked for (already
    # validated once on the way out; re-validated here since it passed
    # through an attacker-observable URL). A parent with no child on file
    # yet can't do anything useful on the dashboard, so that one case is
    # overridden regardless of what was originally requested.
    destination = _safe_next(state)
    if destination == "/app/parent" and not has_children:
        destination = "/app/setup"

    response = RedirectResponse(url=destination, status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        jwt_token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response
