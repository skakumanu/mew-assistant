"""
Notifications that say something.

Two rules from the design shape every line of this module:

  * **Nothing is announced in a single channel.** A notification is stored
    as a locale key plus parameters, so the push, the email and the screen
    all render the same sentence. A chime is never the only signal, and a
    push that a person misses is still readable in the app afterwards.
  * **An outcome must survive the session moving off today.** A child who
    was not looking when the answer arrived finds it, phrased the same way,
    whenever they next look.

Outbound channels are best effort. The stored row is the delivery that
matters; email or push failing is logged and never raised, because a
notification that could not be pushed is not a reason to undo a change the
rules already allowed.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session as DbSession

from ..database.models import Notification, NotificationKind, User
from ..utils.locale import DEFAULT_LOCALE, Translator
from ..utils.locale_context import translator_for

logger = logging.getLogger(__name__)

IN_APP = "in_app"


class NotificationDelivery:
    """Creates the durable record, then fans out best effort."""

    def __init__(self, db: DbSession):
        self.db = db

    # ------------------------------------------------------------------
    # writing
    # ------------------------------------------------------------------

    def notify(
        self,
        recipient: User,
        kind: NotificationKind,
        text_key: str,
        params: Optional[Dict[str, Any]] = None,
        approval_request_id: Optional[int] = None,
        scheduled_session_id: Optional[int] = None,
        push: bool = True,
    ) -> Notification:
        """
        Record a notification and try to deliver it outward.

        The row is written first and unconditionally: if every outbound
        channel fails, the person still finds the sentence in the app.
        """
        notification = Notification(
            recipient_id=recipient.id,
            approval_request_id=approval_request_id,
            scheduled_session_id=scheduled_session_id,
            kind=kind.value,
            text_key=text_key,
            params=params or None,
            delivered_channels=[IN_APP],
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        if push:
            delivered = self._fan_out(recipient, self.render(notification, recipient))
            if delivered:
                notification.delivered_channels = [IN_APP] + delivered
                self.db.commit()

        return notification

    def _fan_out(self, recipient: User, sentence: str) -> List[str]:
        """
        Push the same sentence to whatever channels are configured.

        Every channel carries the text. None of them is allowed to be a
        sound or a badge on its own.
        """
        delivered: List[str] = []

        if recipient.email:
            if self._try_email(recipient.email, sentence):
                delivered.append("email")
        if recipient.phone:
            if self._try_sms(recipient.phone, sentence):
                delivered.append("sms")

        return delivered

    def _try_email(self, address: str, sentence: str) -> bool:
        try:
            from ..integrations.email_integration import get_email_integration

            integration = get_email_integration()
            if not getattr(integration, "enabled", True):
                return False
            coroutine = integration.send_email(
                to_email=address, subject="Mew Assistant", body=sentence
            )
            _run(coroutine)
            return True
        except Exception as exc:
            logger.info("Email notification not delivered: %s", exc)
            return False

    def _try_sms(self, number: str, sentence: str) -> bool:
        try:
            from ..integrations.sms_integration import SMSIntegration

            _run(SMSIntegration().send_sms(to_number=number, message=sentence))
            return True
        except Exception as exc:
            logger.info("SMS notification not delivered: %s", exc)
            return False

    # ------------------------------------------------------------------
    # reading
    # ------------------------------------------------------------------

    def for_user(
        self, user: User, limit: int = 20, unread_only: bool = False
    ) -> List[Notification]:
        query = self.db.query(Notification).filter(Notification.recipient_id == user.id)
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        return (
            query.order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )

    def render(self, notification: Notification, recipient: User) -> str:
        """
        The sentence, in the recipient's own language.

        Rendered at read time, not at write time, so a person who changes
        language sees their history in the new one.
        """
        translator = self._translator_for(recipient)
        params = dict(notification.params or {})
        return translator.t(notification.text_key, **params)

    def _translator_for(self, recipient: User) -> Translator:
        try:
            return translator_for(None, recipient, self.db)
        except Exception:
            return Translator(DEFAULT_LOCALE)

    def mark_read(self, notification: Notification) -> Notification:
        from datetime import datetime

        if notification.read_at is None:
            notification.read_at = datetime.utcnow()
            self.db.commit()
        return notification


def _run(coroutine) -> None:
    """
    Fire an async integration from sync code.

    Inside a running loop the send is scheduled rather than awaited: a
    notification must never add latency to the request that caused it.
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coroutine)
        return
    loop.create_task(coroutine)
