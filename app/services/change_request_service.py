"""
The one write path for schedule changes.

A kid, a service provider or the parent proposes a change. The deterministic
rule engine evaluates it. If every active rule is satisfied the change is
applied immediately, written back to the calendar and recorded in the quiet
log. If it is not, the request is parked for the parent with stable reason
codes and up to three compliant alternatives already attached.

No client decides whether something is allowed. ``submit()`` is the only
entry point, and ``kid_friendly``, ``provider`` and the voice pipeline all
call it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DbSession

from ..database.models import (
    ApprovalAuditLog,
    ApprovalRequest,
    ApprovalStatus,
    ChangeKind,
    ChangeLogEntry,
    LogTone,
    ProviderPerson,
    RequestedBy,
    RequestType,
    RuleSet,
    ScheduledSession,
    User,
)
from . import rule_engine as engine
from .notification_service import NotificationService
from .ruleset_service import RuleSetService

logger = logging.getLogger(__name__)

# How far around the requested time we look for buffer conflicts and caps.
WEEK_WINDOW_DAYS_BEFORE = 7
WEEK_WINDOW_DAYS_AFTER = 14

_REQUEST_TYPE_BY_KIND = {
    ChangeKind.MOVE: RequestType.TIME_CHANGE,
    ChangeKind.SWAP_PROVIDER: RequestType.SCHEDULE_CHANGE,
    ChangeKind.CANCEL: RequestType.SKIP_ACTIVITY,
}


@dataclass
class ChangeOutcome:
    """What happened to one request. Mirrors the ``POST /requests`` response."""

    auto_applied: bool
    session: ScheduledSession
    request: Optional[ApprovalRequest] = None
    reason_codes: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)


class ChangeRequestService:
    """Evaluate, then apply or park. One code path, three callers."""

    def __init__(self, db: DbSession):
        self.db = db
        self.rules = RuleSetService(db)
        self.notifications = NotificationService(db)

    # ------------------------------------------------------------------
    # the loop
    # ------------------------------------------------------------------

    async def submit(
        self,
        actor: User,
        session_id: int,
        kind: ChangeKind,
        new_start: Optional[datetime] = None,
        new_provider_person_id: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> ChangeOutcome:
        """Evaluate a proposed change and either apply it or park it."""
        session = self._load_session(session_id)
        requested_by = self._authorize(actor, session)
        child, parent = self._family(session)
        now = now or datetime.utcnow()

        if kind is ChangeKind.MOVE and new_start is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A move needs a new start time",
            )
        if kind is ChangeKind.SWAP_PROVIDER and new_provider_person_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A provider swap needs the person to swap to",
            )
        if new_provider_person_id is not None:
            self._validate_provider_person(new_provider_person_id, session)

        ruleset = self.rules.get_or_create(parent.id, child.id)
        engine_rules = self.rules.to_engine_rules(ruleset)
        engine_session = self.rules.to_engine_session(session)
        week = self._week_sessions(session, new_start or session.start_utc)

        request = engine.ChangeRequest(
            kind=engine.RequestKind(kind.value),
            session_id=str(session.id),
            requested_by=requested_by.value,
            new_start=new_start,
            new_provider_person_id=(
                str(new_provider_person_id) if new_provider_person_id is not None else None
            ),
        )

        evaluator = engine.RuleEngine(engine_rules, now=now)
        evaluation = evaluator.evaluate(request, engine_session, week)

        if evaluation.passed:
            return await self._apply_now(
                session=session,
                child=child,
                parent=parent,
                actor=actor,
                requested_by=requested_by,
                kind=kind,
                new_start=new_start,
                new_provider_person_id=new_provider_person_id,
                ruleset=ruleset,
            )

        alternatives = evaluator.alternatives(request, engine_session, week)
        return self._park_for_parent(
            session=session,
            child=child,
            parent=parent,
            actor=actor,
            requested_by=requested_by,
            kind=kind,
            new_start=new_start,
            new_provider_person_id=new_provider_person_id,
            reason_codes=[r.value for r in evaluation.reasons],
            alternatives=alternatives,
        )

    # ------------------------------------------------------------------
    # parent decisions on a parked request
    # ------------------------------------------------------------------

    async def apply_approved(self, request: ApprovalRequest, parent: User) -> ScheduledSession:
        """Parent approved the request exactly as it was asked."""
        session = self._load_session(request.scheduled_session_id)
        kind = ChangeKind(request.change_kind or ChangeKind.MOVE.value)

        self._mutate(
            session,
            kind=kind,
            new_start=request.new_start_utc,
            new_provider_person_id=request.new_provider_person_id,
        )
        request.auto_applied = False
        request.applied_to_calendar = True
        self.db.commit()

        await self._write_back_to_calendar(session, kind)
        self._log_change(
            session=session,
            parent=parent,
            kind=kind,
            tone=LogTone.MANUAL,
            meta_key="parent.meta_approved",
            meta_params={"who": self._who(request)},
            approval_request_id=request.id,
        )
        self._notify_requester(request, session)
        return session

    async def choose_alternative(
        self, request: ApprovalRequest, parent: User, index: int
    ) -> ScheduledSession:
        """
        Parent picked one of the three compliant alternatives.

        This is the primary path in the design: one tap, and the requester is
        told the new time rather than being told "no".
        """
        options = request.alternatives or []
        if index < 0 or index >= len(options):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No such alternative on this request",
            )

        chosen = options[index]
        session = self._load_session(request.scheduled_session_id)
        new_start = datetime.fromisoformat(chosen["start"])

        # Picking an alternative always resolves to a move at a compliant
        # time, even when the request that failed was a swap or a cancel.
        self._mutate(session, kind=ChangeKind.MOVE, new_start=new_start)

        request.status = ApprovalStatus.APPROVED
        request.parent_approved = True
        request.approved_at = datetime.utcnow()
        request.processed_at = datetime.utcnow()
        request.chosen_alternative_index = index
        request.auto_applied = False
        request.applied_to_calendar = True
        self.db.commit()

        self._audit(
            request.id,
            "chose_alternative",
            parent.id,
            notes=f"alternative {index}: {chosen['start']}",
        )

        await self._write_back_to_calendar(session, ChangeKind.MOVE)
        self._log_change(
            session=session,
            parent=parent,
            kind=ChangeKind.MOVE,
            tone=LogTone.MANUAL,
            meta_key="parent.meta_picked",
            meta_params={},
            approval_request_id=request.id,
        )
        self._notify_requester(request, session)
        return session

    def record_denied(self, request: ApprovalRequest, parent: User) -> ChangeLogEntry:
        """Log a denial in the parent's quiet log. The schedule is untouched."""
        session = (
            self.db.query(ScheduledSession)
            .filter(ScheduledSession.id == request.scheduled_session_id)
            .first()
        )
        entry = ChangeLogEntry(
            parent_id=parent.id,
            child_id=request.kid_id,
            approval_request_id=request.id,
            text_key="parent.log_stays",
            params={
                "title": session.title if session else (request.requested_activity or ""),
                "when": session.start_utc.isoformat() if session else "",
            },
            meta_key="parent.meta_declined",
            meta_params={"who": self._who(request)},
            tone=LogTone.MANUAL.value,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ------------------------------------------------------------------
    # reads
    # ------------------------------------------------------------------

    def sessions_for_child(
        self,
        child_id: int,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        include_cancelled: bool = False,
    ) -> List[ScheduledSession]:
        query = self.db.query(ScheduledSession).filter(ScheduledSession.child_id == child_id)
        if not include_cancelled:
            query = query.filter(ScheduledSession.is_cancelled.is_(False))
        if start is not None:
            query = query.filter(ScheduledSession.start_utc >= start)
        if end is not None:
            query = query.filter(ScheduledSession.start_utc < end)
        return query.order_by(ScheduledSession.start_utc.asc()).all()

    def log_for_parent(self, parent_id: int, limit: int = 8) -> List[ChangeLogEntry]:
        return (
            self.db.query(ChangeLogEntry)
            .filter(ChangeLogEntry.parent_id == parent_id)
            .order_by(ChangeLogEntry.created_at.desc(), ChangeLogEntry.id.desc())
            .limit(limit)
            .all()
        )

    def pending_for_session(self, session_id: int) -> Optional[ApprovalRequest]:
        """The open request blocking further asks on one session, if any."""
        return (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.scheduled_session_id == session_id,
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .order_by(ApprovalRequest.created_at.desc())
            .first()
        )

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _load_session(self, session_id: Optional[int]) -> ScheduledSession:
        session = (
            self.db.query(ScheduledSession).filter(ScheduledSession.id == session_id).first()
            if session_id is not None
            else None
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    def _family(self, session: ScheduledSession):
        child = self.db.query(User).filter(User.id == session.child_id).first()
        if child is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Child account not found"
            )
        parent = (
            self.db.query(User).filter(User.id == child.parent_id).first()
            if child.parent_id
            else None
        )
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No parent account linked to this child",
            )
        return child, parent

    def _authorize(self, actor: User, session: ScheduledSession) -> RequestedBy:
        """Work out which persona is asking, and refuse anyone else."""
        if actor.is_kid_account:
            if actor.id != session.child_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your schedule",
                )
            return RequestedBy.KID

        child = self.db.query(User).filter(User.id == session.child_id).first()
        if child is not None and child.parent_id == actor.id:
            return RequestedBy.PARENT

        person = (
            self.db.query(ProviderPerson)
            .filter(
                ProviderPerson.user_id == actor.id,
                ProviderPerson.is_active.is_(True),
            )
            .first()
        )
        if person is not None and person.org_id == session.provider_org_id:
            return RequestedBy.PROVIDER

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to change this session",
        )

    def _validate_provider_person(self, person_id: int, session: ScheduledSession) -> None:
        person = self.db.query(ProviderPerson).filter(ProviderPerson.id == person_id).first()
        if person is None or not person.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown therapist",
            )
        if session.provider_org_id and person.org_id != session.provider_org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That therapist works for a different organisation",
            )

    def _week_sessions(self, session: ScheduledSession, around: datetime) -> List[engine.Session]:
        """Everything the engine needs for buffer checks and weekly caps."""
        window_start = around - timedelta(days=WEEK_WINDOW_DAYS_BEFORE)
        window_end = around + timedelta(days=WEEK_WINDOW_DAYS_AFTER)
        rows = self.sessions_for_child(session.child_id, window_start, window_end)
        return [self.rules.to_engine_session(row) for row in rows]

    async def _apply_now(
        self,
        *,
        session: ScheduledSession,
        child: User,
        parent: User,
        actor: User,
        requested_by: RequestedBy,
        kind: ChangeKind,
        new_start: Optional[datetime],
        new_provider_person_id: Optional[int],
        ruleset: RuleSet,
    ) -> ChangeOutcome:
        """Rules satisfied: change the schedule, log it, tell the requester."""
        self._mutate(session, kind, new_start, new_provider_person_id)

        request = self._record_request(
            session=session,
            child=child,
            parent=parent,
            actor=actor,
            requested_by=requested_by,
            kind=kind,
            new_start=new_start,
            new_provider_person_id=new_provider_person_id,
            reason_codes=[],
            alternatives=[],
            auto_applied=True,
        )

        await self._write_back_to_calendar(session, kind)
        self._log_change(
            session=session,
            parent=parent,
            kind=kind,
            tone=LogTone.AUTO,
            meta_key="parent.meta_auto",
            meta_params={"who": self._display_name(actor)},
            approval_request_id=request.id,
        )

        # Telling the parent about an auto-applied change is a preference,
        # not part of the loop: the point is that it did not need them.
        if ruleset.notify_on_auto_approve:
            try:
                self.notifications.send_approval_result(
                    kid_id=parent.id,
                    approved=True,
                    parent_note="Applied automatically: it fit your rules.",
                )
            except Exception as exc:  # notification failures never block a change
                logger.warning("Auto-approve notification failed: %s", exc)

        return ChangeOutcome(auto_applied=True, session=session, request=request)

    def _park_for_parent(
        self,
        *,
        session: ScheduledSession,
        child: User,
        parent: User,
        actor: User,
        requested_by: RequestedBy,
        kind: ChangeKind,
        new_start: Optional[datetime],
        new_provider_person_id: Optional[int],
        reason_codes: List[str],
        alternatives: List[engine.Alternative],
    ) -> ChangeOutcome:
        """Rules not satisfied: one card for the parent, fix already attached."""
        serialised = [
            {"start": alt.start.isoformat(), "rank": alt.reason_rank} for alt in alternatives
        ]
        request = self._record_request(
            session=session,
            child=child,
            parent=parent,
            actor=actor,
            requested_by=requested_by,
            kind=kind,
            new_start=new_start,
            new_provider_person_id=new_provider_person_id,
            reason_codes=reason_codes,
            alternatives=serialised,
            auto_applied=False,
        )

        try:
            self.notifications.notify_parent_approval_needed(
                parent=parent,
                kid_name=self._display_name(child),
                request=request,
            )
        except Exception as exc:
            logger.warning("Approval notification failed: %s", exc)

        return ChangeOutcome(
            auto_applied=False,
            session=session,
            request=request,
            reason_codes=reason_codes,
            alternatives=serialised,
        )

    def _mutate(
        self,
        session: ScheduledSession,
        kind: ChangeKind,
        new_start: Optional[datetime] = None,
        new_provider_person_id: Optional[int] = None,
    ) -> ScheduledSession:
        """The only place a session's time, therapist or status changes."""
        if kind is ChangeKind.CANCEL:
            session.is_cancelled = True
        else:
            if new_start is not None:
                session.start_utc = new_start
            if new_provider_person_id is not None:
                session.provider_person_id = new_provider_person_id
        session.last_changed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session

    def _record_request(
        self,
        *,
        session: ScheduledSession,
        child: User,
        parent: User,
        actor: User,
        requested_by: RequestedBy,
        kind: ChangeKind,
        new_start: Optional[datetime],
        new_provider_person_id: Optional[int],
        reason_codes: List[str],
        alternatives: List[Dict[str, Any]],
        auto_applied: bool,
    ) -> ApprovalRequest:
        """
        Every request is recorded, including the ones that never reached the
        parent. Auto-applied changes still need an audit trail.
        """
        request = ApprovalRequest(
            kid_id=child.id,
            parent_id=parent.id,
            request_type=_REQUEST_TYPE_BY_KIND[kind],
            status=ApprovalStatus.APPROVED if auto_applied else ApprovalStatus.PENDING,
            original_activity_id=session.id,
            requested_activity=session.title,
            requested_time=new_start.isoformat() if new_start else None,
            requested_by=requested_by.value,
            provider_org_id=session.provider_org_id,
            change_kind=kind.value,
            scheduled_session_id=session.id,
            new_start_utc=new_start,
            new_provider_person_id=new_provider_person_id,
            reason_codes=reason_codes or None,
            alternatives=alternatives or None,
            auto_applied=auto_applied,
            parent_approved=True if auto_applied else None,
            approved_at=datetime.utcnow() if auto_applied else None,
            processed_at=datetime.utcnow() if auto_applied else None,
            applied_to_calendar=auto_applied,
            created_at=datetime.utcnow(),
            expires_at=None if auto_applied else datetime.utcnow() + timedelta(hours=72),
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)

        self._audit(
            request.id,
            "auto_applied" if auto_applied else "created",
            actor.id,
            new_status=request.status.value,
            notes=(
                f"{requested_by.value} requested {kind.value}"
                + (f"; blocked by {', '.join(reason_codes)}" if reason_codes else "")
            ),
        )
        return request

    def _log_change(
        self,
        *,
        session: ScheduledSession,
        parent: User,
        kind: ChangeKind,
        tone: LogTone,
        meta_key: str,
        meta_params: Dict[str, Any],
        approval_request_id: Optional[int] = None,
    ) -> ChangeLogEntry:
        """
        Add a row to the parent's quiet log.

        Keys and parameters only: the sentence is rendered in whatever
        language the reader is using, whenever they open the log.
        """
        if kind is ChangeKind.CANCEL:
            text_key = "parent.log_cancelled"
            params = {"title": session.title, "day": session.start_utc.isoformat()}
        else:
            text_key = "parent.log_moved"
            params = {"title": session.title, "when": session.start_utc.isoformat()}

        entry = ChangeLogEntry(
            parent_id=parent.id,
            child_id=session.child_id,
            approval_request_id=approval_request_id,
            text_key=text_key,
            params=params,
            meta_key=meta_key,
            meta_params=meta_params or None,
            tone=tone.value,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    async def _write_back_to_calendar(self, session: ScheduledSession, kind: ChangeKind) -> None:
        """
        Push the change back out as a calendar update.

        Best effort by design: the schedule in Mew is already authoritative,
        so a calendar that is unreachable, read-only or simply not connected
        must never undo a change the rules allowed.
        """
        from .calendar_sync_service import CalendarSyncService

        try:
            pushed = await CalendarSyncService(self.db).push(session, kind)
        except Exception as exc:  # a calendar never breaks the loop
            logger.warning("Calendar write-back failed for session %s: %s", session.id, exc)
            return

        if not pushed:
            logger.info(
                "Session %s changed in Mew but not written back (no writable calendar)",
                session.id,
            )

    def _notify_requester(self, request: ApprovalRequest, session: ScheduledSession) -> None:
        """Push the outcome to whoever asked, in a sentence they can read."""
        try:
            self.notifications.send_approval_result(
                kid_id=request.kid_id,
                approved=True,
                parent_note=session.start_utc.isoformat(),
            )
        except Exception as exc:
            logger.warning("Requester notification failed: %s", exc)

    def _audit(
        self,
        approval_request_id: int,
        action: str,
        performed_by: int,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        self.db.add(
            ApprovalAuditLog(
                approval_request_id=approval_request_id,
                action=action,
                performed_by=performed_by,
                timestamp=datetime.utcnow(),
                old_status=old_status,
                new_status=new_status,
                notes=notes,
            )
        )
        self.db.commit()

    def _who(self, request: ApprovalRequest) -> str:
        if request.requested_by == RequestedBy.PROVIDER.value:
            org = request.provider_org_id
            if org:
                from ..database.models import ProviderOrg

                row = self.db.query(ProviderOrg).filter(ProviderOrg.id == org).first()
                if row:
                    return row.name
        user = self.db.query(User).filter(User.id == request.kid_id).first()
        return self._display_name(user) if user else ""

    @staticmethod
    def _display_name(user: Optional[User]) -> str:
        if user is None:
            return ""
        return user.display_name or user.full_name or user.username or user.email or ""
