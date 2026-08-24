"""
RuleSet persistence and translation into rule-engine inputs.

The rule engine (``app/services/rule_engine.py``) is pure: it knows nothing
about SQLAlchemy. This module is the only place that converts stored rows
into the engine's dataclasses and back, and the only place that knows how
the six toggles in the parent's Rules tab map onto columns.
"""

from __future__ import annotations

import json
import logging
from datetime import time
from typing import Dict, List, Optional

from sqlalchemy.orm import Session as DbSession

from ..database.models import (
    ApprovalRule,
    ProtectedBlock,
    RuleSet,
    ScheduledSession,
    WeeklyCap,
)
from . import rule_engine as engine

logger = logging.getLogger(__name__)

# The defaults the design ships with, shown as six "on" toggles.
DEFAULT_MIN_NOTICE_HOURS = 24
DEFAULT_EARLIEST_START = time(8, 0)
DEFAULT_LATEST_END = time(18, 0)
DEFAULT_BUFFER_MINUTES = 45
DEFAULT_MIDDAY_BLOCK = (time(12, 0), time(13, 0), "block.midday")


class RuleSetService:
    """Loads, creates and updates a parent's declared rules for one child."""

    def __init__(self, db: DbSession):
        self.db = db

    # -- lookup -----------------------------------------------------------

    def get(self, parent_id: int, child_id: Optional[int] = None) -> Optional[RuleSet]:
        query = self.db.query(RuleSet).filter(RuleSet.parent_id == parent_id)
        if child_id is not None:
            specific = query.filter(RuleSet.child_id == child_id).first()
            if specific:
                return specific
        # A family-wide ruleset (child_id NULL) applies to every child.
        return query.filter(RuleSet.child_id.is_(None)).first() or query.first()

    def get_or_create(self, parent_id: int, child_id: Optional[int] = None) -> RuleSet:
        existing = self.get(parent_id, child_id)
        if existing:
            return existing

        ruleset = RuleSet(
            parent_id=parent_id,
            child_id=child_id,
            min_notice_hours=DEFAULT_MIN_NOTICE_HOURS,
            earliest_start=DEFAULT_EARLIEST_START,
            latest_end=DEFAULT_LATEST_END,
            require_same_provider_person=True,
            buffer_minutes=DEFAULT_BUFFER_MINUTES,
            cancellation_needs_approval=True,
        )
        self.db.add(ruleset)
        self.db.flush()

        start, end, label = DEFAULT_MIDDAY_BLOCK
        self.db.add(
            ProtectedBlock(ruleset_id=ruleset.id, start_time=start, end_time=end, label_key=label)
        )
        self.db.commit()
        self.db.refresh(ruleset)

        # Anything the family already declared through the older, free-form
        # ApprovalRule rows is folded in so nobody re-enters their rules.
        self.backfill_from_approval_rules(ruleset)
        return ruleset

    # -- engine translation ------------------------------------------------

    def to_engine_rules(self, ruleset: RuleSet) -> engine.RuleSet:
        """Convert a stored RuleSet into the pure engine's dataclass."""
        blocks = [
            engine.ProtectedBlock(
                start=b.start_time,
                end=b.end_time,
                label_key=b.label_key,
                weekdays=tuple(b.weekdays) if b.weekdays else None,
            )
            for b in ruleset.protected_blocks
        ]

        caps: Dict[str, int] = {c.activity_type: c.max_sessions for c in ruleset.weekly_caps}

        return engine.RuleSet(
            min_notice_hours=ruleset.min_notice_hours,
            latest_end=ruleset.latest_end,
            earliest_start=ruleset.earliest_start,
            protected_blocks=blocks,
            require_same_provider_person=bool(ruleset.require_same_provider_person),
            buffer_minutes=ruleset.buffer_minutes,
            max_sessions_per_week=caps or None,
            cancellation_needs_approval=bool(ruleset.cancellation_needs_approval),
            allowed_weekdays=tuple(ruleset.allowed_weekdays) if ruleset.allowed_weekdays else None,
            timezone=ruleset.timezone,
        )

    @staticmethod
    def to_engine_session(row: ScheduledSession) -> engine.Session:
        """Convert a stored session into the engine's view of it."""
        return engine.Session(
            id=str(row.id),
            start=row.start_utc,
            duration_minutes=row.duration_minutes,
            activity_type=row.activity_type,
            provider_org_id=str(row.provider_org_id or ""),
            provider_person_id=str(row.provider_person_id or ""),
        )

    # -- updates -----------------------------------------------------------

    def update(self, ruleset: RuleSet, payload: dict) -> RuleSet:
        """
        Apply the parent's toggles. A field set to ``None`` turns that rule
        off, which is exactly what an "off" switch means to the engine.
        """
        simple_fields = (
            "timezone",
            "min_notice_hours",
            "earliest_start",
            "latest_end",
            "buffer_minutes",
            "allowed_weekdays",
        )
        for name in simple_fields:
            if name in payload:
                setattr(ruleset, name, payload[name])

        for name in (
            "require_same_provider_person",
            "cancellation_needs_approval",
            "notify_on_auto_approve",
        ):
            if name in payload and payload[name] is not None:
                setattr(ruleset, name, bool(payload[name]))

        if "protected_blocks" in payload and payload["protected_blocks"] is not None:
            for block in list(ruleset.protected_blocks):
                self.db.delete(block)
            ruleset.protected_blocks = []
            self.db.flush()
            for block in payload["protected_blocks"]:
                self.db.add(
                    ProtectedBlock(
                        ruleset_id=ruleset.id,
                        start_time=block["start"],
                        end_time=block["end"],
                        weekdays=block.get("weekdays"),
                        label_key=block.get("label_key", "block.custom"),
                    )
                )

        if "weekly_caps" in payload and payload["weekly_caps"] is not None:
            for cap in list(ruleset.weekly_caps):
                self.db.delete(cap)
            ruleset.weekly_caps = []
            self.db.flush()
            for cap in payload["weekly_caps"]:
                self.db.add(
                    WeeklyCap(
                        ruleset_id=ruleset.id,
                        activity_type=cap["activity_type"],
                        max_sessions=cap["max_sessions"],
                    )
                )

        self.db.commit()
        self.db.refresh(ruleset)
        return ruleset

    # -- migration ---------------------------------------------------------

    def backfill_from_approval_rules(self, ruleset: RuleSet) -> RuleSet:
        """
        Fold the older free-form ``ApprovalRule`` rows into a RuleSet.

        ``ApprovalRule.conditions`` is JSON text with a shape that depends on
        ``rule_type`` (time_range / activity_type / duration / location).
        Only the parts the engine understands are carried over; anything
        else is left alone for SmartApprovalService.
        """
        rules: List[ApprovalRule] = (
            self.db.query(ApprovalRule).filter(ApprovalRule.is_active.is_(True)).all()
        )
        if not rules:
            return ruleset

        changed = False
        for rule in rules:
            try:
                conditions = json.loads(rule.conditions or "{}")
            except (ValueError, TypeError):
                logger.warning("Skipping ApprovalRule %s: conditions is not JSON", rule.id)
                continue
            if not isinstance(conditions, dict):
                continue

            if rule.rule_type == "time_range":
                earliest = _parse_time(conditions.get("earliest_start") or conditions.get("start"))
                latest = _parse_time(conditions.get("latest_end") or conditions.get("end"))
                if earliest:
                    ruleset.earliest_start = earliest
                    changed = True
                if latest:
                    ruleset.latest_end = latest
                    changed = True

            elif rule.rule_type == "duration":
                buffer_minutes = conditions.get("buffer_minutes")
                if isinstance(buffer_minutes, int):
                    ruleset.buffer_minutes = buffer_minutes
                    changed = True

            elif rule.rule_type == "activity_type":
                cap = conditions.get("max_per_week")
                activity = conditions.get("activity_type")
                if isinstance(cap, int) and activity:
                    self.db.add(
                        WeeklyCap(
                            ruleset_id=ruleset.id,
                            activity_type=str(activity),
                            max_sessions=cap,
                        )
                    )
                    changed = True

        if changed:
            self.db.commit()
            self.db.refresh(ruleset)
        return ruleset


def _parse_time(value) -> Optional[time]:
    """Accept "17:30", "17:30:00" or a time object."""
    if isinstance(value, time):
        return value
    if not isinstance(value, str):
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            from datetime import datetime as _dt

            return _dt.strptime(value, fmt).time()
        except ValueError:
            continue
    return None
