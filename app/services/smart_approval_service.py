"""
Smart Approval Service
Reduces parent overwhelm by intelligently auto-approving safe requests
and batching others for efficient review.
"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.database.models import ApprovalRequest, ApprovalRule, User
from app.schemas.approval import ApprovalStatus, RequestPriority


class SmartApprovalService:
    """
    Intelligent approval system that learns from parent decisions
    and auto-approves safe, routine requests.
    """

    def __init__(self, db: Session):
        self.db = db

    async def evaluate_request(self, request: ApprovalRequest, parent: User) -> Dict:
        """
        Evaluate if request can be auto-approved based on rules and patterns.

        Returns:
            dict with 'auto_approved', 'reason', and 'confidence' keys
        """
        # Check explicit auto-approval rules
        auto_approve_rule = self._check_auto_approval_rules(request, parent)
        if auto_approve_rule:
            return {
                "auto_approved": True,
                "reason": f"Matches rule: {auto_approve_rule.name}",
                "confidence": 1.0,
            }

        # Check learned patterns from history
        pattern_match = await self._check_learned_patterns(request, parent)
        if pattern_match and pattern_match["confidence"] > 0.85:
            return {
                "auto_approved": True,
                "reason": "Similar requests always approved in past",
                "confidence": pattern_match["confidence"],
            }

        # Check if low-risk routine request
        if self._is_low_risk_routine(request):
            return {
                "auto_approved": True,
                "reason": "Low-risk routine activity",
                "confidence": 0.9,
            }

        return {
            "auto_approved": False,
            "reason": "Requires parent review",
            "confidence": 0.0,
        }

    def _check_auto_approval_rules(
        self, request: ApprovalRequest, parent: User
    ) -> Optional[ApprovalRule]:
        """Check if request matches any auto-approval rules."""
        rules = (
            self.db.query(ApprovalRule)
            .filter(ApprovalRule.user_id == parent.id, ApprovalRule.is_active == True)
            .all()
        )

        for rule in rules:
            if self._matches_rule(request, rule):
                return rule

        return None

    def _matches_rule(self, request: ApprovalRequest, rule: ApprovalRule) -> bool:
        """Check if request matches a specific rule."""
        # Time-based rules
        if rule.rule_type == "time_range":
            req_time = request.proposed_start_time.time()
            if rule.time_start <= req_time <= rule.time_end:
                return True

        # Activity-based rules
        elif rule.rule_type == "activity_type":
            if request.activity_type in rule.allowed_activities:
                return True

        # Duration-based rules
        elif rule.rule_type == "duration":
            duration = (
                request.proposed_end_time - request.proposed_start_time
            ).total_seconds() / 60
            if duration <= rule.max_duration_minutes:
                return True

        # Location-based rules
        elif rule.rule_type == "location":
            if request.location in rule.allowed_locations:
                return True

        return False

    async def _check_learned_patterns(
        self, request: ApprovalRequest, parent: User
    ) -> Optional[Dict]:
        """
        Analyze historical approvals to find patterns.
        Uses ML-like approach to calculate confidence.
        """
        # Get similar past requests
        similar_requests = (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.parent_id == parent.id,
                ApprovalRequest.activity_type == request.activity_type,
                ApprovalRequest.status.in_(
                    [ApprovalStatus.APPROVED, ApprovalStatus.DENIED]
                ),
            )
            .order_by(ApprovalRequest.created_at.desc())
            .limit(20)
            .all()
        )

        if len(similar_requests) < 5:
            return None

        # Calculate approval rate
        approved_count = sum(
            1 for r in similar_requests if r.status == ApprovalStatus.APPROVED
        )
        approval_rate = approved_count / len(similar_requests)

        # Additional similarity scoring
        similarity_scores = []
        for past_req in similar_requests:
            score = self._calculate_similarity(request, past_req)
            similarity_scores.append((score, past_req.status))

        # Weight recent approvals more heavily
        weighted_score = sum(
            score * (1.0 if status == ApprovalStatus.APPROVED else 0.0)
            for score, status in similarity_scores
        ) / len(similarity_scores)

        confidence = (approval_rate * 0.6) + (weighted_score * 0.4)

        return {
            "confidence": confidence,
            "sample_size": len(similar_requests),
            "approval_rate": approval_rate,
        }

    def _calculate_similarity(
        self, req1: ApprovalRequest, req2: ApprovalRequest
    ) -> float:
        """Calculate similarity score between two requests (0-1)."""
        score = 0.0
        weight_sum = 0.0

        # Activity type match (weight: 0.3)
        if req1.activity_type == req2.activity_type:
            score += 0.3
        weight_sum += 0.3

        # Time of day similarity (weight: 0.2)
        time_diff = abs(req1.proposed_start_time.hour - req2.proposed_start_time.hour)
        time_similarity = max(0, 1 - (time_diff / 12))
        score += time_similarity * 0.2
        weight_sum += 0.2

        # Duration similarity (weight: 0.2)
        dur1 = (req1.proposed_end_time - req1.proposed_start_time).total_seconds()
        dur2 = (req2.proposed_end_time - req2.proposed_start_time).total_seconds()
        dur_diff = abs(dur1 - dur2) / max(dur1, dur2)
        dur_similarity = max(0, 1 - dur_diff)
        score += dur_similarity * 0.2
        weight_sum += 0.2

        # Day of week match (weight: 0.15)
        if req1.proposed_start_time.weekday() == req2.proposed_start_time.weekday():
            score += 0.15
        weight_sum += 0.15

        # Location match (weight: 0.15)
        if req1.location == req2.location:
            score += 0.15
        weight_sum += 0.15

        return score / weight_sum if weight_sum > 0 else 0.0

    def _is_low_risk_routine(self, request: ApprovalRequest) -> bool:
        """Determine if request is low-risk and routine."""
        low_risk_activities = [
            "homework",
            "reading",
            "practice",
            "break",
            "snack",
            "free_play",
            "rest",
        ]

        # Check activity type
        if request.activity_type not in low_risk_activities:
            return False

        # Check duration (max 60 minutes for auto-approval)
        duration = (
            request.proposed_end_time - request.proposed_start_time
        ).total_seconds() / 60
        if duration > 60:
            return False

        # Check time (during daytime hours)
        hour = request.proposed_start_time.hour
        if hour < 6 or hour > 21:
            return False

        return True

    async def batch_pending_requests(
        self, parent: User, min_batch_size: int = 3
    ) -> List[Dict]:
        """
        Group pending requests into smart batches for efficient review.

        Returns:
            List of batches with metadata for optimal presentation
        """
        pending = (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.parent_id == parent.id,
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .order_by(ApprovalRequest.created_at)
            .all()
        )

        if len(pending) < min_batch_size:
            return [
                {
                    "batch_id": "single",
                    "requests": pending,
                    "priority": "normal",
                    "description": f"{len(pending)} pending request(s)",
                }
            ]

        batches = []

        # Batch 1: Urgent/Time-sensitive
        urgent = [
            r
            for r in pending
            if r.priority == RequestPriority.URGENT or self._is_time_sensitive(r)
        ]
        if urgent:
            batches.append(
                {
                    "batch_id": "urgent",
                    "requests": urgent,
                    "priority": "high",
                    "description": f"⚡ {len(urgent)} urgent request(s) - needs quick decision",
                }
            )

        # Batch 2: Same activity type
        remaining = [r for r in pending if r not in urgent]
        activity_groups = {}
        for req in remaining:
            activity_groups.setdefault(req.activity_type, []).append(req)

        for activity, reqs in activity_groups.items():
            if len(reqs) >= 2:
                batches.append(
                    {
                        "batch_id": f"activity_{activity}",
                        "requests": reqs,
                        "priority": "normal",
                        "description": f"📚 {len(reqs)} {activity} requests - similar activities",
                    }
                )
                remaining = [r for r in remaining if r not in reqs]

        # Batch 3: Same day
        if remaining:
            day_groups = {}
            for req in remaining:
                day_key = req.proposed_start_time.date()
                day_groups.setdefault(day_key, []).append(req)

            for day, reqs in day_groups.items():
                batches.append(
                    {
                        "batch_id": f"day_{day}",
                        "requests": reqs,
                        "priority": "low",
                        "description": f"📅 {len(reqs)} request(s) for {day.strftime('%A, %b %d')}",
                    }
                )

        return batches

    def _is_time_sensitive(self, request: ApprovalRequest) -> bool:
        """Check if request is time-sensitive."""
        now = datetime.utcnow()
        time_until = request.proposed_start_time - now

        # Urgent if starts within 2 hours
        return time_until.total_seconds() < 7200

    async def create_auto_approval_rule(
        self, parent: User, rule_data: Dict
    ) -> ApprovalRule:
        """Allow parents to create custom auto-approval rules."""
        rule = ApprovalRule(
            user_id=parent.id,
            name=rule_data["name"],
            rule_type=rule_data["rule_type"],
            is_active=True,
            **rule_data.get("params", {}),
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    async def suggest_rules_from_history(self, parent: User) -> List[Dict]:
        """
        Analyze approval history and suggest auto-approval rules
        to reduce parent workload.
        """
        suggestions = []

        # Get approval history
        approved = (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.parent_id == parent.id,
                ApprovalRequest.status == ApprovalStatus.APPROVED,
            )
            .all()
        )

        if len(approved) < 10:
            return suggestions

        # Analyze patterns

        # 1. Activities always approved
        activity_counts = {}
        for req in approved:
            activity_counts[req.activity_type] = (
                activity_counts.get(req.activity_type, 0) + 1
            )

        for activity, count in activity_counts.items():
            if count >= 5:
                suggestions.append(
                    {
                        "rule_type": "activity_type",
                        "name": f"Auto-approve {activity}",
                        "description": f"You've approved {count} {activity} requests - always approve?",
                        "params": {"allowed_activities": [activity]},
                        "confidence": min(count / 10, 1.0),
                    }
                )

        # 2. Time windows
        morning_count = sum(1 for r in approved if 6 <= r.proposed_start_time.hour < 12)
        if morning_count >= 10:
            suggestions.append(
                {
                    "rule_type": "time_range",
                    "name": "Auto-approve morning activities",
                    "description": f"Auto-approve low-risk activities during morning hours",
                    "params": {"time_start": "06:00", "time_end": "12:00"},
                    "confidence": min(morning_count / 20, 1.0),
                }
            )

        # 3. Short duration activities
        short_activities = [
            r
            for r in approved
            if (r.proposed_end_time - r.proposed_start_time).total_seconds() <= 1800
        ]
        if len(short_activities) >= 10:
            suggestions.append(
                {
                    "rule_type": "duration",
                    "name": "Auto-approve activities under 30 minutes",
                    "description": f"You've approved {len(short_activities)} short activities",
                    "params": {"max_duration_minutes": 30},
                    "confidence": min(len(short_activities) / 20, 1.0),
                }
            )

        return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)
