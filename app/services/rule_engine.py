"""
Deterministic rule engine for Mew Assistant scheduling requests.

Ported from the design handoff reference implementation (``rules_engine.py``
in the "three-persona scheduling" bundle). It is intentionally pure: no DB,
no I/O, no AI, no framework imports. That keeps it unit-testable on its own
and makes it safe to call from any router or worker.

Design contract:
  * A request either satisfies every active rule (-> auto apply, log it)
    or it does not (-> parent approval, with up to 3 compliant alternatives).
  * A rule failure is identified by a stable REASON CODE, never by an
    English sentence. The UI resolves codes through its locale files
    (``app/locales/<locale>.json`` -> ``reasons.*``).

The engine runs FIRST, before any learned-pattern or confidence scoring in
``SmartApprovalService``: a request that satisfies the parent's declared
rules must never wait on a confidence score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence


class ReasonCode(str, Enum):
    """Stable identifiers for rule failures. Never user-facing text."""

    MIN_NOTICE = "min_notice"
    LATEST_END = "latest_end"
    PROTECTED_BLOCK = "protected_block"
    SAME_PROVIDER = "same_provider"
    BUFFER = "buffer"
    MAX_PER_WEEK = "max_per_week"
    CANCEL_NEEDS_APPROVAL = "cancel_needs_approval"
    OUTSIDE_ALLOWED_DAYS = "outside_allowed_days"


class RequestKind(str, Enum):
    """The three things a kid or a provider can ask for."""

    MOVE = "move"
    CANCEL = "cancel"
    SWAP_PROVIDER = "swap_provider"


@dataclass(frozen=True)
class Session:
    """An existing scheduled session, as the engine sees it."""

    id: str
    start: datetime
    duration_minutes: int
    activity_type: str  # "aba", "speech", "ot", "school", ...
    provider_org_id: str
    provider_person_id: str  # the individual therapist

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.duration_minutes)


@dataclass(frozen=True)
class ProtectedBlock:
    """A daily window that may never be overlapped (meals, meds, nap, prayer)."""

    start: time
    end: time
    label_key: str  # locale key, e.g. "block.midday"
    weekdays: Optional[Sequence[int]] = None  # None = every day (Mon=0)

    def applies_on(self, day: date) -> bool:
        return self.weekdays is None or day.weekday() in self.weekdays


@dataclass
class RuleSet:
    """
    The parent's defaults. Every field is optional: an unset field is an
    inactive rule, which is how the UI toggles work.
    """

    min_notice_hours: Optional[int] = 24
    latest_end: Optional[time] = time(18, 0)
    earliest_start: Optional[time] = time(8, 0)
    protected_blocks: List[ProtectedBlock] = field(default_factory=list)
    require_same_provider_person: bool = True
    buffer_minutes: Optional[int] = 45
    max_sessions_per_week: Optional[Dict[str, int]] = None  # activity_type -> cap
    cancellation_needs_approval: bool = True
    allowed_weekdays: Optional[Sequence[int]] = None  # None = any day
    timezone: str = "America/Chicago"


@dataclass(frozen=True)
class ChangeRequest:
    """What somebody is asking for. The only write path into the schedule."""

    kind: RequestKind
    session_id: str
    requested_by: str  # "kid" | "provider" | "parent"
    new_start: Optional[datetime] = None
    new_provider_person_id: Optional[str] = None


@dataclass(frozen=True)
class Evaluation:
    passed: bool
    reasons: List[ReasonCode]

    @property
    def auto_approve(self) -> bool:
        return self.passed


@dataclass(frozen=True)
class Alternative:
    start: datetime
    reason_rank: int  # 0 = closest to what was asked for


class RuleEngine:
    """Pure evaluation of a change request against a parent's RuleSet."""

    SLOT_MINUTES = 30

    def __init__(self, rules: RuleSet, now: Optional[datetime] = None):
        self.rules = rules
        self.now = now or datetime.utcnow()

    # ---------- evaluation -------------------------------------------------

    def evaluate(
        self,
        request: ChangeRequest,
        session: Session,
        week: Iterable[Session],
    ) -> Evaluation:
        """Return pass/fail plus the reason codes for every rule that failed."""
        r = self.rules
        reasons: List[ReasonCode] = []

        if request.kind is RequestKind.CANCEL:
            if r.cancellation_needs_approval:
                reasons.append(ReasonCode.CANCEL_NEEDS_APPROVAL)
            return Evaluation(not reasons, reasons)

        start = request.new_start or session.start
        end = start + timedelta(minutes=session.duration_minutes)
        provider_person = request.new_provider_person_id or session.provider_person_id

        if r.min_notice_hours is not None:
            if start - self.now < timedelta(hours=r.min_notice_hours):
                reasons.append(ReasonCode.MIN_NOTICE)

        if r.allowed_weekdays is not None and start.weekday() not in r.allowed_weekdays:
            reasons.append(ReasonCode.OUTSIDE_ALLOWED_DAYS)

        # One code covers the whole allowed-hours window: the locale string for
        # LATEST_END reads "outside the allowed hours" for exactly this reason.
        if r.latest_end is not None and end.time() > r.latest_end:
            reasons.append(ReasonCode.LATEST_END)
        elif r.earliest_start is not None and start.time() < r.earliest_start:
            reasons.append(ReasonCode.LATEST_END)

        for block in r.protected_blocks:
            if not block.applies_on(start.date()):
                continue
            b_start = datetime.combine(start.date(), block.start)
            b_end = datetime.combine(start.date(), block.end)
            if start < b_end and b_start < end:
                reasons.append(ReasonCode.PROTECTED_BLOCK)
                break

        if r.require_same_provider_person and provider_person != session.provider_person_id:
            reasons.append(ReasonCode.SAME_PROVIDER)

        if r.buffer_minutes is not None:
            pad = timedelta(minutes=r.buffer_minutes)
            for other in week:
                if other.id == session.id:
                    continue
                if start < other.end + pad and other.start < end + pad:
                    reasons.append(ReasonCode.BUFFER)
                    break

        if r.max_sessions_per_week:
            cap = r.max_sessions_per_week.get(session.activity_type)
            if cap is not None:
                same_week = [
                    s
                    for s in week
                    if s.activity_type == session.activity_type
                    and s.id != session.id
                    and self._same_week(s.start, start)
                ]
                if len(same_week) + 1 > cap:
                    reasons.append(ReasonCode.MAX_PER_WEEK)

        return Evaluation(not reasons, reasons)

    # ---------- alternatives ---------------------------------------------

    def alternatives(
        self,
        request: ChangeRequest,
        session: Session,
        week: Iterable[Session],
        limit: int = 3,
        horizon_days: int = 7,
        one_per_day: bool = True,
    ) -> List[Alternative]:
        """
        Compliant slots nearest to what was asked for. The design shows
        exactly three, each on a different day, closest first.
        """
        if request.kind is RequestKind.CANCEL:
            return []

        week = list(week)
        target = request.new_start or session.start
        earliest = self.rules.earliest_start or time(0, 0)
        latest = self.rules.latest_end or time(23, 59)

        candidates: List[datetime] = []
        day = self.now.date()
        for offset in range(horizon_days):
            d = day + timedelta(days=offset)
            cursor = datetime.combine(d, earliest)
            day_end = datetime.combine(d, latest)
            while cursor + timedelta(minutes=session.duration_minutes) <= day_end:
                candidates.append(cursor)
                cursor += timedelta(minutes=self.SLOT_MINUTES)

        candidates.sort(key=lambda c: abs((c - target).total_seconds()))

        out: List[Alternative] = []
        used_days = set()
        for cand in candidates:
            if len(out) >= limit:
                break
            if one_per_day and cand.date() in used_days:
                continue
            probe = ChangeRequest(
                kind=RequestKind.MOVE,
                session_id=session.id,
                requested_by=request.requested_by,
                new_start=cand,
                new_provider_person_id=session.provider_person_id,
            )
            if self.evaluate(probe, session, week).passed:
                out.append(Alternative(start=cand, reason_rank=len(out)))
                used_days.add(cand.date())
        return out

    # ---------- helpers ---------------------------------------------------

    @staticmethod
    def _same_week(a: datetime, b: datetime) -> bool:
        return a.isocalendar()[:2] == b.isocalendar()[:2]
