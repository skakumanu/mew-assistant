"""
Smart approval engine for kid requests with minimal parent burden.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List


class ApprovalDecision(str, Enum):
    """Approval decision types."""

    AUTO_APPROVED = "auto_approved"
    REQUIRES_APPROVAL = "requires_approval"
    BATCHED = "batched"
    DENIED = "denied"


class SmartApprovalEngine:
    """
    Intelligent approval system that minimizes parent burden.
    Auto-approves safe requests within predefined rules.
    """

    def __init__(self):
        """Initialize smart approval engine."""
        self.auto_approval_rules = {}
        self.batch_window_hours = 4
        self.pending_approvals = {}

    def evaluate_request(
        self, child_id: str, parent_id: str, request_type: str, request_data: Dict
    ) -> Dict:
        """
        Evaluate a child's request and determine approval status.

        Args:
            child_id: Child user ID
            parent_id: Parent user ID
            request_type: Type of request (schedule_change, activity, etc.)
            request_data: Request details

        Returns:
            Dictionary with decision and reasoning
        """
        # Check auto-approval rules
        if self._can_auto_approve(child_id, request_type, request_data):
            return {
                "decision": ApprovalDecision.AUTO_APPROVED,
                "reason": "Within pre-approved parameters",
                "approved_at": datetime.utcnow().isoformat(),
                "approved_by": "system",
            }

        # Check if should batch
        if self._should_batch(parent_id):
            return {
                "decision": ApprovalDecision.BATCHED,
                "reason": "Batched for parent review",
                "batch_review_at": self._get_next_batch_time().isoformat(),
            }

        # Requires immediate approval
        return {
            "decision": ApprovalDecision.REQUIRES_APPROVAL,
            "reason": "Requires parent approval",
            "requested_at": datetime.utcnow().isoformat(),
        }

    def _can_auto_approve(self, child_id: str, request_type: str, request_data: Dict) -> bool:
        """Check if request can be auto-approved."""
        rules_key = f"{child_id}_{request_type}"

        if rules_key not in self.auto_approval_rules:
            return False

        rules = self.auto_approval_rules[rules_key]

        # Check time constraints
        if "allowed_hours" in rules:
            current_hour = datetime.utcnow().hour
            if current_hour not in rules["allowed_hours"]:
                return False

        # Check duration constraints
        if "max_duration_minutes" in rules and "duration" in request_data:
            if request_data["duration"] > rules["max_duration_minutes"]:
                return False

        return True

    def _should_batch(self, parent_id: str) -> bool:
        """Determine if request should be batched."""
        # Check if there are already pending requests
        if parent_id in self.pending_approvals:
            batch_count = len(self.pending_approvals[parent_id])
            return batch_count < 5  # Batch up to 5 requests
        return True

    def _get_next_batch_time(self) -> datetime:
        """Get next batch review time."""
        now = datetime.utcnow()
        next_batch = now + timedelta(hours=self.batch_window_hours)
        return next_batch

    def set_auto_approval_rule(self, child_id: str, request_type: str, rules: Dict):
        """
        Set auto-approval rules for a child and request type.

        Example:
            engine.set_auto_approval_rule(
                "child_123",
                "schedule_change",
                {
                    "allowed_hours": [15, 16, 17, 18],
                    "max_duration_minutes": 60,
                    "allowed_days": ["weekday"]
                }
            )
        """
        rules_key = f"{child_id}_{request_type}"
        self.auto_approval_rules[rules_key] = rules

    def get_pending_batch(self, parent_id: str) -> List[Dict]:
        """Get pending requests for parent review."""
        return self.pending_approvals.get(parent_id, [])

    # Backwards-compatible helper expected by older tests
    def should_auto_approve(self, request: Dict) -> bool:
        """Return True if the given request would be auto-approved.

        Accepts a request dict with keys like `type`, `child_id`, and
        other metadata. This wraps the existing evaluate_request
        and returns a boolean.
        """
        try:
            req_type = request.get("type") or request.get("request_type")
            child_id = request.get("child_id") or request.get("child")
            # minimal shape
            decision = self.evaluate_request(
                child_id or "", request.get("parent_id", ""), req_type or "", request
            )
            return decision.get("decision") == ApprovalDecision.AUTO_APPROVED
        except Exception:
            return False
