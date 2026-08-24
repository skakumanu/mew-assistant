"""
Per-request locale resolution for the web layer.

The UI locale comes from the device (``Accept-Language``) unless the person
made an explicit choice, which is stored in ``UserLocale`` and always wins.
Nothing here inspects the content of a message: text sniffing belongs to the
voice pipeline (``app/voice/language_detector.py``) and must not decide what
language a screen renders in.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, Request
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import User, UserLocale
from .locale import Translator, resolve_locale

logger = logging.getLogger(__name__)


def translator_for(
    accept_language: Optional[str],
    user: Optional[User] = None,
    db: Optional[DbSession] = None,
) -> Translator:
    """Build the Translator one reader should see."""
    override = None
    source = "device"

    if user is not None and db is not None:
        stored = db.query(UserLocale).filter(UserLocale.user_id == user.id).first()
        if stored is not None and stored.source == "explicit":
            override = stored.locale
            source = "explicit"

    code = resolve_locale(accept_language, override)
    return Translator(code, source=source)


def set_user_locale(db: DbSession, user: User, locale: str, source: str = "explicit") -> UserLocale:
    """Record an explicit choice, or refresh what the device reported."""
    translator = Translator(resolve_locale(None, locale))
    stored = db.query(UserLocale).filter(UserLocale.user_id == user.id).first()
    if stored is None:
        stored = UserLocale(user_id=user.id)
        db.add(stored)
    stored.locale = translator.code
    stored.dir = translator.dir
    stored.clock = translator.clock
    stored.source = source
    db.commit()
    db.refresh(stored)
    return stored


async def get_translator(request: Request, db: DbSession = Depends(get_db)) -> Translator:
    """
    FastAPI dependency: the reader's Translator.

    Works for anonymous requests too, so the same dependency serves the
    signed-in parent and the kid's tablet before it has a token.
    """
    user = getattr(request.state, "user", None)
    return translator_for(request.headers.get("accept-language"), user, db)
