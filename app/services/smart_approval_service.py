"""
Smart approval: the second opinion, never the decision.

The deterministic rule engine decides. It runs FIRST and it runs alone: a
request that satisfies the caregiver's declared rules is applied without ever
consulting this module, and a request that breaks one is parked no matter how
confident a pattern-matcher feels about it. A caregiver who wrote "nothing
past 6pm" meant it, and no confidence score gets to overrule that.

What is left is genuinely useful, and it is all this module does:

  * **Advice.** When a request is already parked, say what history says about
    it - "you have approved 8 of 9 requests like this" - so the caregiver can
    decide in a glance instead of from scratch.
  * **Batching.** Group what is waiting so a caregiver reads one screen
    rather than a trickle of notifications.

Both are read-time only. Nothing here writes to a schedule.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session as DbSession

from app.database.models import (
    ApprovalRequest,
    ApprovalRule,
    ApprovalStatus,
    ScheduledSession,
    User,
)

logger = logging.getLogger(__name__)

# Below this many comparable decisions, history is noise rather than a signal.
MIN_HISTORY = 3
# A request starting sooner than this is worth surfacing first.
TIME_SENSITIVE_HOURS = 2


@dataclass(frozen=True)
class Advisory:
    """
    What history says about a parked request.

    Deliberately not a recommendation: it reports counts and lets the
    caregiver draw the conclusion.
    """

    approved: int
    denied: int
    matched_rule: Optional[str] = None

    @property
    def total(self) -> int:
        return self.approved + self.denied

    @property
    def approval_rate(self) -> float:
        return self.approved / self.total if self.total else 0.0

    def as_dict(self) -> Dict:
        return {
            "approved": self.approved,
            "denied": self.denied,
            "total": self.total,
            "approval_rate": round(self.approval_rate, 2),
            "matched_rule": self.matched_rule,
        }


@dataclass(frozen=True)
class RequestFacts:
    """
    One request, described in terms the real schema actually has.

    Built once so the checks below never reach for a column that does not
    exist - which is how the previous version of this file came to reference
    ten attributes that were never on the models.
    """

    activity_type: str
    start: Optional[datetime]
    duration_minutes: int
    location: Optional[str]
    change_kind: Optional[str]


class SmartApprovalService:
    """Advice and batching. It never decides, and never writes a schedule."""

    def __init__(self, db: DbSession):
        self.db = db

    # ------------------------------------------------------------------
    # advice
    # ------------------------------------------------------------------

    def advise(self, request: ApprovalRequest) -> Optional[Advisory]:
        """
        What history says about a request the engine already parked.

        Returns None when there is not enough comparable history to say
        anything honest, rather than inventing a confident-looking number.
        """
        facts = self.facts_for(request)

        comparable = [
            other
            for other in self._decided_history(request.parent_id)
            if self.facts_for(other).activity_type == facts.activity_type and other.id != request.id
        ]
        if len(comparable) < MIN_HISTORY:
            return None

        approved = sum(1 for r in comparable if r.status == ApprovalStatus.APPROVED)
        rule = self.matching_rule(request, facts)

        return Advisory(
            approved=approved,
            denied=len(comparable) - approved,
            matched_rule=rule.rule_name if rule else None,
        )

    def _decided_history(self, parent_id: int, limit: int = 50) -> List[ApprovalRequest]:
        return (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.parent_id == parent_id,
                ApprovalRequest.status.in_([ApprovalStatus.APPROVED, ApprovalStatus.DENIED]),
                # Auto-applied requests were never a decision, so counting
                # them would tell a caregiver they agreed with things they
                # never actually saw.
                ApprovalRequest.auto_applied.isnot(True),
            )
            .order_by(ApprovalRequest.created_at.desc())
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # facts
    # ------------------------------------------------------------------

    def facts_for(self, request: ApprovalRequest) -> RequestFacts:
        """Describe a request using columns that exist."""
        session = None
        if request.scheduled_session_id:
            session = (
                self.db.query(ScheduledSession)
                .filter(ScheduledSession.id == request.scheduled_session_id)
                .first()
            )

        return RequestFacts(
            activity_type=(
                session.activity_type if session else (request.requested_activity or "other")
            ),
            start=request.new_start_utc or (session.start_utc if session else None),
            duration_minutes=session.duration_minutes if session else 60,
            location=session.location if session else None,
            change_kind=request.change_kind,
        )

    # ------------------------------------------------------------------
    # the caregiver's own free-form rules
    # ------------------------------------------------------------------

    def matching_rule(
        self, request: ApprovalRequest, facts: Optional[RequestFacts] = None
    ) -> Optional[ApprovalRule]:
        """
        The first active ApprovalRule this request matches, if any.

        These are the older free-form rules, kept because families may have
        written them. The structured fields live inside ``conditions`` JSON,
        not as columns.
        """
        facts = facts or self.facts_for(request)

        rules = (
            self.db.query(ApprovalRule)
            .filter(
                ApprovalRule.created_by == request.parent_id,
                ApprovalRule.is_active.is_(True),
            )
            .order_by(ApprovalRule.priority.asc())
            .all()
        )
        for rule in rules:
            if self._matches(rule, facts):
                return rule
        return None

    def _matches(self, rule: ApprovalRule, facts: RequestFacts) -> bool:
        try:
            conditions = json.loads(rule.conditions or "{}")
        except (TypeError, ValueError):
            logger.warning("ApprovalRule %s has unparseable conditions", rule.id)
            return False
        if not isinstance(conditions, dict):
            return False

        allowed = conditions.get("allowed_activities")
        if allowed and facts.activity_type not in allowed:
            return False

        locations = conditions.get("allowed_locations")
        if locations and facts.location not in locations:
            return False

        max_duration = conditions.get("max_duration_minutes")
        if isinstance(max_duration, int) and facts.duration_minutes > max_duration:
            return False

        if facts.start is not None:
            start = _time_of(conditions.get("time_start"))
            end = _time_of(conditions.get("time_end"))
            if start is not None and facts.start.hour < start:
                return False
            if end is not None and facts.start.hour >= end:
                return False

        # A rule with no usable conditions matches nothing, rather than
        # everything - the safer direction to be wrong in.
        return any(
            key in conditions
            for key in (
                "allowed_activities",
                "allowed_locations",
                "max_duration_minutes",
                "time_start",
                "time_end",
            )
        )

    # ------------------------------------------------------------------
    # batching
    # ------------------------------------------------------------------

    def batch_pending(self, parent: User, min_batch_size: int = 3) -> List[Dict]:
        """
        Group what is waiting, so a caregiver reads one screen.

        Time-sensitive requests come first: something starting in an hour
        cannot wait for a batch.
        """
        pending = (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.parent_id == parent.id,
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .order_by(ApprovalRequest.created_at.asc())
            .all()
        )

        if len(pending) < min_batch_size:
            return [
                {
                    "batch_id": "single",
                    "request_ids": [r.id for r in pending],
                    "priority": "normal",
                    "count": len(pending),
                }
            ]

        soon, later = [], []
        for request in pending:
            (soon if self.is_time_sensitive(request) else later).append(request)

        batches = []
        if soon:
            batches.append(
                {
                    "batch_id": "time_sensitive",
                    "request_ids": [r.id for r in soon],
                    "priority": "urgent",
                    "count": len(soon),
                }
            )
        if later:
            batches.append(
                {
                    "batch_id": "everything_else",
                    "request_ids": [r.id for r in later],
                    "priority": "normal",
                    "count": len(later),
                }
            )
        return batches

    def is_time_sensitive(self, request: ApprovalRequest) -> bool:
        """True when the session starts soon enough that waiting is a decision."""
        start = self.facts_for(request).start
        if start is None:
            return False
        return start - datetime.utcnow() < timedelta(hours=TIME_SENSITIVE_HOURS)

    # ------------------------------------------------------------------
    # caregiver-authored rules
    # ------------------------------------------------------------------

    def create_auto_approval_rule(self, parent: User, rule_data: Dict) -> ApprovalRule:
        """Store a free-form rule. Conditions are JSON, matching the column."""
        rule = ApprovalRule(
            family_id=rule_data.get("family_id"),
            rule_name=rule_data.get("name") or rule_data.get("rule_name") or "Rule",
            rule_type=rule_data.get("rule_type", "activity_type"),
            conditions=json.dumps(rule_data.get("conditions", rule_data.get("params", {}))),
            is_active=True,
            priority=rule_data.get("priority", 100),
            created_by=parent.id,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def suggest_rules_from_history(self, parent: User) -> List[Dict]:
        """
        Activities this caregiver has always said yes to.

        A suggestion, never an applied rule: turning "you always approve
        this" into "so I did it for you" is exactly the move the design
        exists to avoid.
        """
        history = self._decided_history(parent.id, limit=200)
        if len(history) < 10:
            return []

        tally: Dict[str, Dict[str, int]] = {}
        for request in history:
            activity = self.facts_for(request).activity_type
            bucket = tally.setdefault(activity, {"approved": 0, "denied": 0})
            key = "approved" if request.status == ApprovalStatus.APPROVED else "denied"
            bucket[key] += 1

        return [
            {
                "activity_type": activity,
                "approved": counts["approved"],
                "denied": counts["denied"],
                "suggestion": "always_allow",
            }
            for activity, counts in sorted(tally.items())
            if counts["denied"] == 0 and counts["approved"] >= 5
        ]


def _time_of(value) -> Optional[int]:
    """An hour from 17, "17" or "17:00"."""
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        head = value.split(":")[0].strip()
        try:
            return int(head)
        except ValueError:
            return None
    return None
