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

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import DEFAULT_CAREGIVER_TERM
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
