"""
The three persona screens.

Server-rendered shells, one per persona, plus a canvas that shows all three
side by side the way the design reference does. Every string the screens use
is resolved here from the reader's locale and handed to the client as data;
the client never assembles a sentence by concatenation.
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import DEFAULT_CAREGIVER_TERM
from ..utils.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SESSION_COOKIE,
    authenticate_user,
    create_access_token,
)
from ..utils.locale import Translator
from ..utils.locale_context import translator_for

router = APIRouter(prefix="/app", tags=["Mew UI"])

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def _context(request: Request, translator: Translator, **extra) -> dict:
    context = {
        "request": request,
        "locale": translator.code,
        "dir": translator.dir,
        "clock": translator.clock,
        "t": translator.strings,
        "strings_json": json.dumps(translator.strings, ensure_ascii=False),
    }
    context.update(extra)
    return context


# "Parent" and "guardian" name one persona, so one screen answers on both
# paths and the label it shows comes from the family's own choice of word.
@router.get("/parent", response_class=HTMLResponse)
@router.get("/guardian", response_class=HTMLResponse)
async def parent_screen(
    request: Request,
    name: Optional[str] = None,
    term: Optional[str] = None,
    db: DbSession = Depends(get_db),
):
    """Inbox, week and rules. The only screen a caregiver has to keep up to date."""
    translator = translator_for(request.headers.get("accept-language"), None, db)

    # The path itself is a reasonable default: somebody who opened /app/guardian
    # should not be greeted by the word "parent" before their rules load.
    if term is None:
        term = "guardian" if request.url.path.endswith("/guardian") else DEFAULT_CAREGIVER_TERM

    return templates.TemplateResponse(
        "mew/parent.html",
        _context(
            request,
            translator,
            caregiver_term=term,
            caregiver_label=translator.caregiver(term),
            display_name=name or translator.caregiver(term),
        ),
    )


@router.get("/kid", response_class=HTMLResponse)
async def kid_screen(request: Request, db: DbSession = Depends(get_db)):
    """Today's cards, two buttons, no rules and no emoji."""
    translator = translator_for(request.headers.get("accept-language"), None, db)
    return templates.TemplateResponse("mew/kid.html", _context(request, translator))


@router.get("/provider", response_class=HTMLResponse)
async def provider_screen(
    request: Request,
    org: Optional[str] = None,
    calendar: str = "Google Calendar",
    db: DbSession = Depends(get_db),
):
    """The provider's own sessions, and one form to propose a change."""
    translator = translator_for(request.headers.get("accept-language"), None, db)
    return templates.TemplateResponse(
        "mew/provider.html",
        _context(
            request,
            translator,
            org_name=org or translator.strings["persona"]["provider"],
            calendar_name=calendar,
        ),
    )


# ---------------------------------------------------------------------------
# Signing in
#
# The screens used to want a bearer token pasted into a box. They now take an
# email and a password like anything else, and keep the session in an
# HttpOnly cookie that page script cannot read.
# ---------------------------------------------------------------------------


@router.get("/sign-in", response_class=HTMLResponse)
async def sign_in_screen(
    request: Request,
    next: str = "/app/parent",
    error: Optional[str] = None,
    db: DbSession = Depends(get_db),
):
    """The sign-in form."""
    translator = translator_for(request.headers.get("accept-language"), None, db)
    return templates.TemplateResponse(
        "mew/sign_in.html",
        _context(request, translator, next_path=_safe_next(next), error=error),
    )


@router.post("/sign-in")
async def sign_in(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/app/parent"),
    db: DbSession = Depends(get_db),
):
    """
    Authenticate and set the session cookie.

    A failure says only that the pair did not match: which half was wrong is
    not the signer-in's business to learn, and telling them enumerates
    accounts for everybody else.
    """
    destination = _safe_next(next)
    user = authenticate_user(db, email, password)
    if user is None or not user.is_active:
        return RedirectResponse(
            url=f"/app/sign-in?next={destination}&error=1",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    token = create_access_token({"sub": user.email, "user_id": user.id})
    response = RedirectResponse(url=destination, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/sign-out")
async def sign_out():
    """Drop the session cookie."""
    response = RedirectResponse(url="/app/sign-in", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


def _safe_next(destination: Optional[str]) -> str:
    """
    Only ever redirect within this app.

    A ``next`` parameter is attacker-controlled, so anything that is not a
    plain local path is discarded rather than sanitised.
    """
    if not destination or not destination.startswith("/") or destination.startswith("//"):
        return "/app/parent"
    return destination
