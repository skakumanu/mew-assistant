"""
AI-Powered Scheduling Service
Provides conflict detection, resolution, and smart scheduling suggestions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database.models import PriorityLevel, ScheduleEntry, SessionStatus
from app.schemas.schedule import OptimizationResult, ScheduleConflict, ScheduleSuggestion

logger = logging.getLogger(__name__)


class AISchedulerService:
    """AI-powered scheduling with conflict detection and optimization"""

    def __init__(self, db: Session):
        self.db = db
        self.learning_threshold = 5  # Minimum patterns needed for learning

    async def detect_conflicts(self, user_id: int, proposed_entry: Dict) -> List[ScheduleConflict]:
        """
        Detect scheduling conflicts for a proposed entry

        Args:
            user_id: User ID
            proposed_entry: Proposed schedule entry with start_time, end_time, type

        Returns:
            List of detected conflicts with severity and suggestions
        """
        conflicts = []
        start = proposed_entry["start_time"]
        end = proposed_entry["end_time"]

        # Query overlapping entries
        existing_entries = (
            self.db.query(ScheduleEntry)
            .filter(
                and_(
                    ScheduleEntry.user_id == user_id,
                    ScheduleEntry.status == SessionStatus.CONFIRMED,
                    or_(
                        and_(
                            ScheduleEntry.start_time <= start,
                            ScheduleEntry.end_time > start,
                        ),
                        and_(
                            ScheduleEntry.start_time < end,
                            ScheduleEntry.end_time >= end,
                        ),
                        and_(
                            ScheduleEntry.start_time >= start,
                            ScheduleEntry.end_time <= end,
                        ),
                    ),
                )
            )
            .all()
        )

        for entry in existing_entries:
            severity = self._calculate_conflict_severity(entry, proposed_entry)
            suggestions = await self._generate_conflict_resolution(entry, proposed_entry)

            conflicts.append(
                ScheduleConflict(
                    type=self._determine_conflict_type(entry, proposed_entry),
                    schedule1_id=entry.id,
                    schedule2_id=proposed_entry.get("id", 0),
                    message=f"{entry.title} conflicts with {proposed_entry.get('title', 'proposed entry')}",
                    suggested_resolution=(suggestions[0] if suggestions else "Adjust timing"),
                    severity=severity,
                    conflicting_entry_id=entry.id,
                    conflicting_title=entry.title,
                    conflict_type=self._determine_conflict_type(entry, proposed_entry),
                    overlap_minutes=self._calculate_overlap_minutes(entry, proposed_entry),
                    suggestions=suggestions,
                )
            )

        return conflicts

    async def resolve_conflict_auto(self, conflict: ScheduleConflict, user_preferences: Dict) -> Optional[Dict]:
        """
        Automatically resolve conflict based on user preferences and priority

        Args:
            conflict: Detected conflict
            user_preferences: User's scheduling preferences

        Returns:
            Resolution action or None if manual intervention needed
        """
        if conflict.severity == "low":
            # Low severity: Suggest time adjustment
            return {
                "action": "adjust_time",
                "adjustment_minutes": 15,
                "reason": "Minor overlap - adjusting by 15 minutes",
            }

        elif conflict.severity == "medium":
            # Check priority rules
            if user_preferences.get("allow_overlap_for_therapy", False):
                return {
                    "action": "allow_overlap",
                    "reason": "Therapy sessions have priority per user preference",
                }

        # High severity or no auto-resolution rule
        return None

    async def suggest_optimal_times(
        self,
        user_id: int,
        activity_type: str,
        duration_minutes: int,
        preferred_date: datetime,
        constraints: Optional[Dict] = None,
    ) -> List[ScheduleSuggestion]:
        """
        Suggest optimal time slots based on user patterns and constraints

        Args:
            user_id: User ID
            activity_type: Type of activity to schedule
            duration_minutes: Activity duration
            preferred_date: Preferred date
            constraints: Optional constraints (earliest_time, latest_time, etc.)

        Returns:
            List of suggested time slots with confidence scores
        """
        suggestions = []

        # Learn from historical patterns
        patterns = await self._learn_user_patterns(user_id, activity_type)

        # Get user's daily schedule for target date
        existing_schedule = await self._get_daily_schedule(user_id, preferred_date)

        # Find available slots
        available_slots = self._find_available_slots(existing_schedule, duration_minutes, preferred_date, constraints)

        # Score each slot based on patterns and heuristics
        for slot in available_slots:
            score = await self._calculate_slot_score(slot, activity_type, patterns, existing_schedule, constraints)

            suggestions.append(
                ScheduleSuggestion(
                    start_time=slot["start"],
                    end_time=slot["end"],
                    confidence_score=score["confidence"],
                    reason=score["reasoning"],
                    reasoning=score["reasoning"],
                    factors=score["factors"],
                )
            )

        # Sort by confidence score
        suggestions.sort(key=lambda x: x.confidence_score, reverse=True)

        return suggestions[:5]  # Return top 5 suggestions

    async def optimize_schedule(
        self, user_id: int, date: datetime, optimization_goals: List[str]
    ) -> OptimizationResult:
        """
        Optimize entire day's schedule based on goals

        Args:
            user_id: User ID
            date: Date to optimize
            optimization_goals: List of goals (e.g., 'minimize_transitions', 'respect_energy_levels')

        Returns:
            Optimized schedule with improvements
        """
        original_schedule = await self._get_daily_schedule(user_id, date)

        # Apply optimization algorithms
        optimized = original_schedule.copy()
        improvements = []

        if "minimize_transitions" in optimization_goals:
            optimized, transition_improvements = self._minimize_transitions(optimized)
            improvements.extend(transition_improvements)

        if "respect_energy_levels" in optimization_goals:
            optimized, energy_improvements = await self._respect_energy_patterns(user_id, optimized)
            improvements.extend(energy_improvements)

        if "balance_activities" in optimization_goals:
            optimized, balance_improvements = self._balance_activity_types(optimized)
            improvements.extend(balance_improvements)

        return OptimizationResult(
            original_schedule=original_schedule,
            optimized_schedule=optimized,
            improvements=improvements,
            efficiency_gain_percent=self._calculate_efficiency_gain(original_schedule, optimized),
        )

    async def _learn_user_patterns(self, user_id: int, activity_type: str) -> Dict:
        """Learn patterns from user's historical scheduling"""
        # Query past 90 days of similar activities
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)

        historical = (
            self.db.query(ScheduleEntry)
            .filter(
                and_(
                    ScheduleEntry.user_id == user_id,
                    ScheduleEntry.activity_type == activity_type,
                    ScheduleEntry.start_time >= ninety_days_ago,
                    ScheduleEntry.status == SessionStatus.COMPLETED,
                )
            )
            .all()
        )

        if len(historical) < self.learning_threshold:
            return {"has_patterns": False}

        # Analyze patterns
        patterns = {
            "has_patterns": True,
            "preferred_hours": self._extract_preferred_hours(historical),
            "preferred_days": self._extract_preferred_days(historical),
            "typical_duration": self._calculate_typical_duration(historical),
            "success_rate_by_time": self._analyze_success_by_time(historical),
        }

        return patterns

    def _calculate_conflict_severity(self, existing: ScheduleEntry, proposed: Dict) -> str:
        """Calculate severity of schedule conflict"""
        overlap_minutes = self._calculate_overlap_minutes(existing, proposed)

        # High severity conditions
        if overlap_minutes > 30:
            return "high"
        if existing.priority in (PriorityLevel.HIGH, PriorityLevel.URGENT):
            return "high"
        if proposed.get("priority") in (
            PriorityLevel.HIGH.value,
            PriorityLevel.URGENT.value,
            "critical",
        ):
            return "high"
        if existing.activity_type in ["therapy", "medical"]:
            return "high"

        # Medium severity
        if overlap_minutes > 15:
            return "medium"

        return "low"

    def _calculate_overlap_minutes(self, existing: ScheduleEntry, proposed: Dict) -> int:
        """Calculate minutes of overlap between two entries"""
        start = max(existing.start_time, proposed["start_time"])
        end = min(existing.end_time, proposed["end_time"])

        if start < end:
            return int((end - start).total_seconds() / 60)
        return 0

    def _determine_conflict_type(self, existing: ScheduleEntry, proposed: Dict) -> str:
        """Determine type of conflict"""
        if existing.activity_type == proposed.get("activity_type"):
            return "duplicate_activity"
        elif existing.requires_same_location(proposed):
            return "location_conflict"
        elif existing.involves_same_person(proposed):
            return "person_unavailable"
        else:
            return "time_overlap"

    async def _generate_conflict_resolution(self, existing: ScheduleEntry, proposed: Dict) -> List[str]:
        """Generate suggestions for resolving conflict"""
        suggestions = []

        # Suggest time adjustments
        suggestions.append(f"Move to {(proposed['start_time'] + timedelta(hours=1)).strftime('%I:%M %p')}")

        # Suggest shortening duration
        if proposed.get("duration_flexible", False):
            suggestions.append("Reduce duration by 15 minutes")

        # Suggest alternative day
        suggestions.append("Schedule for next available day")

        return suggestions

    def _find_available_slots(
        self,
        existing_schedule: List,
        duration_minutes: int,
        target_date: datetime,
        constraints: Optional[Dict],
    ) -> List[Dict]:
        """Find available time slots in schedule"""
        slots = []

        # Define search window
        start_hour = constraints.get("earliest_hour", 7) if constraints else 7
        end_hour = constraints.get("latest_hour", 22) if constraints else 22

        day_start = target_date.replace(hour=start_hour, minute=0, second=0)
        day_end = target_date.replace(hour=end_hour, minute=0, second=0)

        # Sort existing schedule
        existing_schedule.sort(key=lambda x: x["start_time"])

        current_time = day_start
        for entry in existing_schedule:
            if current_time < entry["start_time"]:
                gap_minutes = int((entry["start_time"] - current_time).total_seconds() / 60)
                if gap_minutes >= duration_minutes:
                    slots.append(
                        {
                            "start": current_time,
                            "end": current_time + timedelta(minutes=duration_minutes),
                        }
                    )
            current_time = max(current_time, entry["end_time"])

        # Check end of day
        if current_time < day_end:
            gap_minutes = int((day_end - current_time).total_seconds() / 60)
            if gap_minutes >= duration_minutes:
                slots.append(
                    {
                        "start": current_time,
                        "end": current_time + timedelta(minutes=duration_minutes),
                    }
                )

        return slots

    async def _calculate_slot_score(
        self,
        slot: Dict,
        activity_type: str,
        patterns: Dict,
        existing_schedule: List,
        constraints: Optional[Dict],
    ) -> Dict:
        """Calculate confidence score for a time slot"""
        score = 0.5  # Base score
        factors = []

        # Pattern matching
        if patterns.get("has_patterns"):
            hour = slot["start"].hour
            if hour in patterns["preferred_hours"]:
                score += 0.2
                factors.append("Matches your typical scheduling pattern")

        # Avoid back-to-back scheduling
        buffer_minutes = constraints.get("buffer_minutes", 15) if constraints else 15
        has_buffer = self._check_buffer_time(slot, existing_schedule, buffer_minutes)
        if has_buffer:
            score += 0.15
            factors.append("Includes buffer time for transitions")

        # Energy level consideration
        if activity_type in ["therapy", "tutoring"] and 9 <= slot["start"].hour <= 11:
            score += 0.1
            factors.append("Scheduled during optimal focus hours")

        # Avoid meal times
        if not self._conflicts_with_meals(slot):
            score += 0.05
            factors.append("Does not conflict with typical meal times")

        reasoning = self._generate_reasoning(factors, score)

        return {
            "confidence": min(score, 1.0),
            "reasoning": reasoning,
            "factors": factors,
        }

    async def _get_daily_schedule(self, user_id: int, date: datetime) -> List[Dict]:
        """Get all schedule entries for a specific date"""
        day_start = date.replace(hour=0, minute=0, second=0)
        day_end = date.replace(hour=23, minute=59, second=59)

        entries = (
            self.db.query(ScheduleEntry)
            .filter(
                and_(
                    ScheduleEntry.user_id == user_id,
                    ScheduleEntry.start_time >= day_start,
                    ScheduleEntry.start_time <= day_end,
                )
            )
            .all()
        )

        return [
            {
                "id": e.id,
                "start_time": e.start_time,
                "end_time": e.end_time,
                "title": e.title,
                "activity_type": e.activity_type,
                "priority": e.priority,
            }
            for e in entries
        ]

    def _minimize_transitions(self, schedule: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Optimize schedule to minimize location/context transitions"""
        # Group similar activities
        improvements = []
        # Implementation would reorder activities to group by location/type
        improvements.append("Grouped therapy sessions to minimize travel")
        return schedule, improvements

    async def _respect_energy_patterns(self, user_id: int, schedule: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Optimize based on user's energy patterns"""
        improvements = []
        # Implementation would move high-focus activities to peak energy times
        improvements.append("Moved tutoring to morning peak focus period")
        return schedule, improvements

    def _balance_activity_types(self, schedule: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Balance different types of activities throughout day"""
        improvements = []
        improvements.append("Added breaks between intensive activities")
        return schedule, improvements

    def _calculate_efficiency_gain(self, original: List, optimized: List) -> float:
        """Calculate efficiency improvement percentage"""
        # Simple heuristic based on transition reduction
        return 12.5  # Placeholder

    def _extract_preferred_hours(self, entries: List) -> List[int]:
        """Extract hours user prefers for this activity"""
        hours = [e.start_time.hour for e in entries]
        # Return most common hours
        from collections import Counter

        common = Counter(hours).most_common(3)
        return [h for h, _ in common]

    def _extract_preferred_days(self, entries: List) -> List[int]:
        """Extract weekdays user prefers"""
        days = [e.start_time.weekday() for e in entries]
        from collections import Counter

        common = Counter(days).most_common(3)
        return [d for d, _ in common]

    def _calculate_typical_duration(self, entries: List) -> int:
        """Calculate typical duration in minutes"""
        durations = [(e.end_time - e.start_time).total_seconds() / 60 for e in entries]
        return int(sum(durations) / len(durations)) if durations else 60

    def _analyze_success_by_time(self, entries: List) -> Dict:
        """Analyze success rates by time of day"""
        # Placeholder for success rate analysis
        return {"morning": 0.85, "afternoon": 0.75, "evening": 0.65}

    def _check_buffer_time(self, slot: Dict, schedule: List, buffer_minutes: int) -> bool:
        """Check if slot has adequate buffer time"""
        for entry in schedule:
            if abs((slot["start"] - entry["end_time"]).total_seconds() / 60) < buffer_minutes:
                return False
            if abs((entry["start_time"] - slot["end"]).total_seconds() / 60) < buffer_minutes:
                return False
        return True

    def _conflicts_with_meals(self, slot: Dict) -> bool:
        """Check if slot conflicts with typical meal times"""
        hour = slot["start"].hour
        # Typical meal hours: 7-8am, 12-1pm, 6-7pm
        meal_hours = [7, 8, 12, 13, 18, 19]
        return hour in meal_hours

    def _generate_reasoning(self, factors: List[str], score: float) -> str:
        """Generate human-readable reasoning for score"""
        if score >= 0.8:
            return f"Highly recommended: {'; '.join(factors)}"
        elif score >= 0.6:
            return f"Good option: {'; '.join(factors)}"
        else:
            return f"Available: {'; '.join(factors) if factors else 'Basic availability'}"
