"""Schemas for the smart-approval surface (batching, rules, suggestions)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApprovalBatch(BaseModel):
    """
    A group of pending requests to read in one sitting.

    Batching is about attention, not authority: it changes the order a
    caregiver sees things, never whether something was allowed.
    """

    batch_id: str
    request_ids: List[int] = Field(default_factory=list)
    priority: str = Field("normal", description="urgent | normal")
    count: int = 0


class ApprovalRuleCreate(BaseModel):
    """
    A caregiver's own free-form rule.

    These are the older, looser rules kept alongside the structured RuleSet.
    ``conditions`` is stored as JSON, and understands `allowed_activities`,
    `allowed_locations`, `max_duration_minutes`, `time_start` and `time_end`.
    """

    name: str = Field(..., max_length=255)
    rule_type: str = Field("activity_type", max_length=50)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    family_id: Optional[int] = None
    priority: int = 100


class ApprovalRuleResponse(BaseModel):
    id: int
    rule_name: str
    rule_type: str
    conditions: str
    is_active: bool
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True


class RuleSuggestion(BaseModel):
    """
    An activity the caregiver has always said yes to.

    A suggestion and nothing more: turning "you always approve this" into
    "so I did it for you" is the move the design exists to avoid.
    """

    activity_type: str
    approved: int
    denied: int
    suggestion: str = "always_allow"
