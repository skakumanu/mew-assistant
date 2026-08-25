"""
The three persona screens.

Server-rendered shells, one per persona, plus a canvas that shows all three
side by side the way the design reference does. Every string the screens use
is resolved here from the reader's locale and handed to the client as data;
the client never assembles a sentence by concatenation.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import DEFAULT_CAREGIVER_TERM
from ..utils.auth import SESSION_COOKIE
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


@router.get("/setup", response_class=HTMLResponse)
async def setup_wizard_screen(request: Request, db: DbSession = Depends(get_db)):
    """
    First-run wizard: add a child, optionally a provider.

    Same "static shell, client script does the rest" pattern as the other
    screens - the page renders unconditionally and mew.js's requireSignIn()
    redirects to sign-in if the session cookie is missing or expired.
    """
    translator = translator_for(request.headers.get("accept-language"), None, db)
    return templates.TemplateResponse("mew/setup_wizard.html", _context(request, translator))


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
# WorkOS AuthKit is the front door - its hosted UI is where a parent
# actually enters a password, picks Google/Microsoft/Apple, or gets a
# passwordless email code. This screen only ever renders when that flow
# itself failed (an ?error=1 bounce-back); otherwise it redirects straight
# to app/routers/oauth_workos.py before anything is shown.
# ---------------------------------------------------------------------------


@router.get("/sign-in", response_class=HTMLResponse)
async def sign_in_screen(
    request: Request,
    next: str = "/app/parent",
    error: Optional[str] = None,
    db: DbSession = Depends(get_db),
):
    """Send the browser straight to WorkOS, unless it just bounced back with an error."""
    if error:
        translator = translator_for(request.headers.get("accept-language"), None, db)
        return templates.TemplateResponse(
            "mew/sign_in.html",
            _context(request, translator, next_path=_safe_next(next), error=error),
        )
    return RedirectResponse(
        url=f"/auth/workos/login?next={_safe_next(next)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


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
