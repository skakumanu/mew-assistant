"""
Turns stored codes into sentences, in the reader's language.

Nothing in the database holds a rendered sentence: requests hold reason
codes, log rows hold a locale key plus parameters. This module is where
those become the exact strings the design specifies, for whichever person
is looking.
"""

from __future__ import annotations

import zlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.models import (
    DEFAULT_CAREGIVER_TERM,
    ApprovalRequest,
    ChangeKind,
    ChangeLogEntry,
    ProviderOrg,
    ProviderPerson,
    RequestedBy,
    ScheduledSession,
    User,
)
from ..schemas.change_request import (
    AlternativeOut,
    LogEntryOut,
    PendingRequestOut,
    SessionOut,
)
from ..utils.locale import Translator

# The four tinted pairs the kid's activity tiles cycle through, in the order
# the design lists them: green, amber, indigo, rust.
TILE_COUNT = 4
ACTIVITY_TILES = {"aba": 0, "speech": 1, "ot": 2, "school": 3}


class Presenter:
    """One reader, one language, one set of rendered strings."""

    def __init__(self, translator: Translator, db, caregiver_term: str = DEFAULT_CAREGIVER_TERM):
        self.t = translator
        self.db = db
        # Whether this family reads "parent" or "guardian". Same persona,
        # same permissions - only the word on screen differs.
        self.caregiver_term = caregiver_term

    # -- sessions ---------------------------------------------------------

    def session(self, row: ScheduledSession) -> SessionOut:
        org = row.org
        person = row.person
        return SessionOut(
            id=row.id,
            title=row.title,
            activity_type=row.activity_type,
            start_utc=row.start_utc,
            duration_minutes=row.duration_minutes,
            location=row.location,
            provider_org_id=row.provider_org_id,
            provider_org_name=org.name if org else None,
            provider_person_id=row.provider_person_id,
            provider_person_name=person.display_name if person else None,
            is_cancelled=bool(row.is_cancelled),
            changed=row.last_changed_at is not None,
        )

    # -- alternatives -----------------------------------------------------

    def alternatives(self, stored: Optional[List[Dict[str, Any]]]) -> List[AlternativeOut]:
        out: List[AlternativeOut] = []
        for index, option in enumerate(stored or []):
            start = _parse(option.get("start"))
            if start is None:
                continue
            out.append(
                AlternativeOut(
                    index=index,
                    start=start,
                    label=self.t.option_label(start),
                    note=self.t.t("parent.closest" if index == 0 else "parent.also_fits"),
                )
            )
        return out

    # -- parent inbox -----------------------------------------------------

    def pending_request(self, request: ApprovalRequest) -> PendingRequestOut:
        session = (
            self.db.query(ScheduledSession)
            .filter(ScheduledSession.id == request.scheduled_session_id)
            .first()
        )
        title = session.title if session else (request.requested_activity or "")
        kind = request.change_kind or ChangeKind.MOVE.value
        reason_codes = list(request.reason_codes or [])

        if kind == ChangeKind.CANCEL.value:
            headline = self.t.t("parent.headline_skip", title=title)
        else:
            when = self.t.when(request.new_start_utc) if request.new_start_utc else ""
            headline = self.t.t("parent.headline_move", title=title, when=when)

        detail = self._detail(request, session, kind)

        return PendingRequestOut(
            id=request.id,
            source_label=self.source_label(request),
            requested_by=request.requested_by or RequestedBy.KID.value,
            headline=headline,
            detail=detail,
            reason_codes=reason_codes,
            reasons_text=(
                f"{self.t.t('parent.not_fit')} {self.t.reasons(reason_codes)}"
                if reason_codes
                else ""
            ),
            alternatives=self.alternatives(request.alternatives),
            kind=kind,
            session_id=request.scheduled_session_id,
            created_at=request.created_at,
        )

    def _detail(
        self,
        request: ApprovalRequest,
        session: Optional[ScheduledSession],
        kind: str,
    ) -> str:
        if session is None:
            return ""
        when = self.t.when(session.start_utc)
        person = session.person.display_name if session.person else ""

        if kind == ChangeKind.CANCEL.value:
            return self.t.t("parent.detail_skip", when=when, person=person)

        if kind == ChangeKind.SWAP_PROVIDER.value and request.new_provider_person_id:
            swapped_to = (
                self.db.query(ProviderPerson)
                .filter(ProviderPerson.id == request.new_provider_person_id)
                .first()
            )
            return self.t.t(
                "parent.detail_swap",
                when=when,
                person=swapped_to.display_name if swapped_to else "",
                original=person,
            )

        return self.t.t("parent.detail_now", when=when, person=person)

    def source_label(self, request: ApprovalRequest) -> str:
        """The small uppercase label above a card: who is asking."""
        requested_by = request.requested_by or RequestedBy.KID.value
        if requested_by == RequestedBy.PROVIDER.value and request.provider_org_id:
            org = (
                self.db.query(ProviderOrg).filter(ProviderOrg.id == request.provider_org_id).first()
            )
            if org:
                return org.name
        if requested_by == RequestedBy.KID.value:
            kid = self.db.query(User).filter(User.id == request.kid_id).first()
            if kid:
                return kid.display_name or kid.username or self.t.t("persona.kid")
        if requested_by == RequestedBy.PARENT.value:
            return self.t.caregiver(self.caregiver_term)
        return self.t.t(f"persona.{requested_by}")

    def approve_label(self, request: ApprovalRequest) -> str:
        kind = request.change_kind or ChangeKind.MOVE.value
        if kind == ChangeKind.CANCEL.value:
            return self.t.t("parent.skip_it")
        return self.t.t("parent.allow_anyway")

    # -- quiet log --------------------------------------------------------

    def log_entry(self, entry: ChangeLogEntry) -> LogEntryOut:
        return LogEntryOut(
            id=entry.id,
            text=self.t.t(entry.text_key, **self._humanise(entry.params)),
            meta=(
                self.t.t(entry.meta_key, **self._humanise(entry.meta_params))
                if entry.meta_key
                else ""
            ),
            tone=entry.tone,
            created_at=entry.created_at,
        )

    def _humanise(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Log rows store ISO timestamps so they can be re-rendered later.
        Turn them into the reader's own "Thu 5pm" / "Thu" phrasing.
        """
        out: Dict[str, Any] = {}
        for name, value in (params or {}).items():
            moment = _parse(value) if name in ("when", "day", "time") else None
            if moment is None:
                out[name] = value
            elif name == "day":
                out[name] = self.t.day_name(moment)
            elif name == "time":
                out[name] = self.t.time(moment)
            else:
                out[name] = self.t.when(moment)
        return out

    # -- kid --------------------------------------------------------------

    def kid_card_symbols(self, session: ScheduledSession) -> List[Dict[str, str]]:
        """
        Symbols mode: the same two actions every time, plus the activity.

        Glyphs only - real AAC symbol sets (PCS, ARASAAC, Bliss) need
        licensed artwork, and the design leaves a slot for them rather than
        shipping look-alikes.
        """
        return [
            {"glyph": "◴", "label_key": "kid.ask_later"},
            {"glyph": "✕", "label_key": "kid.ask_skip"},
            {"glyph": "→", "label_key": "kid.with"},
        ]

    @staticmethod
    def tile_index(session: ScheduledSession) -> int:
        """
        Stable tint per activity type, so a card never changes colour.

        The four activities the design names get the four tinted pairs it
        specifies, in its order. Anything else hashes into the same four.
        """
        activity = (session.activity_type or "other").lower()
        if activity in ACTIVITY_TILES:
            return ACTIVITY_TILES[activity]
        return zlib.crc32(activity.encode("utf-8")) % TILE_COUNT


def _parse(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None
