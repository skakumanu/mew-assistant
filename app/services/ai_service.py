"""
AI Service for intelligent scheduling features
Provides conflict detection, smart suggestions, and pattern learning
"""

import statistics
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.schemas.schedule import ScheduleConflict, ScheduleCreate, ScheduleSuggestion


class AIService:
    """Core AI service for scheduling intelligence"""

    def __init__(self):
        self.min_break_minutes = 15
        self.travel_time_per_mile = 2  # minutes

    def detect_conflicts(
        self, schedules: List[ScheduleCreate], min_break_minutes: Optional[int] = None
    ) -> List[ScheduleConflict]:
        """
        Detect scheduling conflicts including overlaps, insufficient breaks, and travel time

        Args:
            schedules: List of schedule entries to check
            min_break_minutes: Minimum break time required between activities

        Returns:
            List of detected conflicts
        """
        if min_break_minutes is not None:
            self.min_break_minutes = min_break_minutes

        conflicts = []

        # Sort schedules by start time
        sorted_schedules = sorted(schedules, key=lambda x: x.start_time)

        for i in range(len(sorted_schedules)):
            for j in range(i + 1, len(sorted_schedules)):
                schedule1 = sorted_schedules[i]
                schedule2 = sorted_schedules[j]

                # Check for time overlap
                if self._has_time_overlap(schedule1, schedule2):
                    conflicts.append(
                        ScheduleConflict(
                            type="time_overlap",
                            schedule1_id=i,
                            schedule2_id=j,
                            message=f"'{schedule1.title}' overlaps with '{schedule2.title}'",
                            severity="high",
                            suggested_resolution="Reschedule one of the activities",
                        )
                    )

                # Check for insufficient break time
                if self._has_insufficient_break(schedule1, schedule2):
                    conflicts.append(
                        ScheduleConflict(
                            type="insufficient_break",
                            schedule1_id=i,
                            schedule2_id=j,
                            message=f"Only {self._get_break_minutes(schedule1, schedule2)} minutes between activities",
                            severity="medium",
                            suggested_resolution=f"Add at least {self.min_break_minutes} minutes break",
                        )
                    )

                # Check for insufficient travel time (independent check)
                if hasattr(schedule1, "location") and hasattr(schedule2, "location"):
                    if schedule1.location and schedule2.location:
                        if self._has_insufficient_travel_time(schedule1, schedule2):
                            conflicts.append(
                                ScheduleConflict(
                                    type="insufficient_travel_time",
                                    schedule1_id=i,
                                    schedule2_id=j,
                                    message="Insufficient travel time between locations",
                                    severity="high",
                                    suggested_resolution="Increase buffer time or reorder activities",
                                )
                            )

        return conflicts

    def _has_time_overlap(self, s1: ScheduleCreate, s2: ScheduleCreate) -> bool:
        """Check if two schedules overlap in time"""
        return s1.start_time < s2.end_time and s1.end_time > s2.start_time

    def _has_insufficient_break(self, s1: ScheduleCreate, s2: ScheduleCreate) -> bool:
        """Check if there's insufficient break time between schedules"""
        if s1.end_time > s2.start_time:
            return False  # They overlap, not just insufficient break
        break_minutes = (s2.start_time - s1.end_time).total_seconds() / 60
        return break_minutes < self.min_break_minutes

    def _get_break_minutes(self, s1: ScheduleCreate, s2: ScheduleCreate) -> int:
        """Calculate break time in minutes"""
        return int((s2.start_time - s1.end_time).total_seconds() / 60)

    def _has_insufficient_travel_time(self, s1: ScheduleCreate, s2: ScheduleCreate) -> bool:
        """Check if there's insufficient time to travel between locations"""
        # Simple heuristic: assume at least 15 minutes travel time for different locations
        if s1.location != s2.location:
            break_minutes = (s2.start_time - s1.end_time).total_seconds() / 60
            return break_minutes < 15  # Need at least 15 minutes for travel
        return False

    def suggest_time_slots(
        self,
        duration_minutes: int,
        existing_schedules: Optional[List[ScheduleCreate]] = None,
        preferred_time_of_day: Optional[str] = None,
        activity_type: Optional[str] = None,
        patterns: Optional[Dict[str, Any]] = None,
    ) -> List[ScheduleSuggestion]:
        """
        Suggest optimal time slots for new activity

        Args:
            duration_minutes: Duration of the new activity
            existing_schedules: List of existing schedules to avoid
            preferred_time_of_day: Preferred time ('morning', 'afternoon', 'evening')
            activity_type: Type of activity for pattern-based suggestions
            patterns: Learned patterns for this activity type

        Returns:
            List of suggested time slots
        """
        suggestions = []
        existing_schedules = existing_schedules or []

        # Define time ranges based on preference
        time_ranges = self._get_time_ranges(preferred_time_of_day)

        # Use pattern data if available
        if patterns and activity_type and activity_type in patterns:
            preferred_hour = patterns[activity_type].get("preferred_hour")
            if preferred_hour:
                time_ranges.insert(0, (preferred_hour, preferred_hour + 2))

        # Generate suggestions for each time range
        for start_hour, end_hour in time_ranges:
            current_time = datetime.now().replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )
            end_time = datetime.now().replace(hour=end_hour, minute=0, second=0, microsecond=0)

            while current_time < end_time:
                proposed_end = current_time + timedelta(minutes=duration_minutes)

                # Check if this slot conflicts with existing schedules
                proposed_schedule = ScheduleCreate(
                    title="Proposed",
                    start_time=current_time,
                    end_time=proposed_end,
                    user_id=0,
                )

                conflicts = self.detect_conflicts([proposed_schedule] + existing_schedules)
                if not conflicts:
                    suggestions.append(
                        ScheduleSuggestion(
                            start_time=current_time,
                            end_time=proposed_end,
                            confidence_score=0.9,
                            reason="No conflicts detected",
                        )
                    )

                current_time += timedelta(minutes=30)  # Check every 30 minutes

                if len(suggestions) >= 5:  # Limit to 5 suggestions
                    break

            if len(suggestions) >= 5:
                break

        return suggestions

    def _get_time_ranges(self, preferred_time_of_day: Optional[str]) -> List[tuple]:
        """Get hour ranges based on time of day preference"""
        all_ranges = {
            "morning": [(8, 12)],
            "afternoon": [(12, 17)],
            "evening": [(17, 20)],
            None: [(8, 12), (12, 17), (17, 20)],
        }
        return all_ranges.get(preferred_time_of_day, all_ranges[None])

    def suggest_alternatives(
        self,
        conflicting_schedule: ScheduleCreate,
        existing_schedules: List[ScheduleCreate],
    ) -> List[ScheduleSuggestion]:
        """
        Suggest alternative time slots when a conflict is detected

        Args:
            conflicting_schedule: The schedule that has conflicts
            existing_schedules: Existing schedules causing conflicts

        Returns:
            List of alternative suggestions
        """
        duration_minutes = int(
            (conflicting_schedule.end_time - conflicting_schedule.start_time).total_seconds() / 60
        )

        return self.suggest_time_slots(
            duration_minutes=duration_minutes, existing_schedules=existing_schedules
        )

    def optimize_schedule(self, schedules: List[ScheduleCreate]) -> List[ScheduleCreate]:
        """
        Optimize schedule order considering location proximity and time efficiency

        Args:
            schedules: List of schedules to optimize

        Returns:
            Optimized list of schedules
        """
        if len(schedules) <= 1:
            return schedules

        # Group by date
        by_date = {}
        for schedule in schedules:
            date_key = schedule.start_time.date()
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(schedule)

        # Optimize each day separately
        optimized = []
        for date_key, day_schedules in by_date.items():
            # Sort by start time
            day_schedules.sort(key=lambda x: x.start_time)

            # If schedules have locations, try to group by proximity
            if all(hasattr(s, "location") and s.location for s in day_schedules):
                day_schedules = self._optimize_by_location(day_schedules)

            optimized.extend(day_schedules)

        return optimized

    def _optimize_by_location(self, schedules: List[ScheduleCreate]) -> List[ScheduleCreate]:
        """Optimize schedule order by location proximity (simple heuristic)"""
        # This is a simplified version - in production, use actual geocoding
        return schedules  # For now, keep original order

    def learn_patterns(
        self, historical_schedules: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Learn patterns from historical scheduling data

        Args:
            historical_schedules: List of past schedule data

        Returns:
            Dictionary of learned patterns per activity
        """
        patterns = {}

        # Group by activity
        by_activity = {}
        for schedule in historical_schedules:
            activity = schedule.get("activity")
            if activity:
                if activity not in by_activity:
                    by_activity[activity] = []
                by_activity[activity].append(schedule)

        # Analyze patterns for each activity
        for activity, activity_schedules in by_activity.items():
            patterns[activity] = {}

            # Find preferred hour
            hours = [s.get("hour") for s in activity_schedules if "hour" in s]
            if hours:
                patterns[activity]["preferred_hour"] = Counter(hours).most_common(1)[0][0]

            # Find typical duration
            durations = [s.get("duration") for s in activity_schedules if "duration" in s]
            if durations:
                patterns[activity]["typical_duration"] = Counter(durations).most_common(1)[0][0]

            # Determine frequency
            dates = [s.get("date") for s in activity_schedules if "date" in s]
            if len(dates) >= 2:
                patterns[activity]["frequency"] = self._determine_frequency(dates)

        return patterns

    def _determine_frequency(self, dates: List[Any]) -> str:
        """Determine activity frequency from dates"""
        if len(dates) < 2:
            return "unknown"

        # Convert to datetime if strings
        dt_dates = []
        for d in dates:
            if isinstance(d, str):
                dt_dates.append(datetime.fromisoformat(d))
            elif isinstance(d, datetime):
                dt_dates.append(d)

        if len(dt_dates) < 2:
            return "unknown"

        # Sort dates
        dt_dates.sort()

        # Calculate average gap
        gaps = [(dt_dates[i + 1] - dt_dates[i]).days for i in range(len(dt_dates) - 1)]
        avg_gap = statistics.mean(gaps)

        # Classify frequency
        if avg_gap <= 1:
            return "daily"
        elif avg_gap <= 7:
            return "weekly"
        elif avg_gap <= 14:
            return "biweekly"
        elif avg_gap <= 31:
            return "monthly"
        elif avg_gap <= 93:
            return "quarterly"
        else:
            return "occasional"

    def predict_next_occurrence(
        self, activity: str, historical_schedules: List[Dict[str, Any]]
    ) -> Optional[datetime]:
        """
        Predict next occurrence of an activity based on patterns

        Args:
            activity: Activity type
            historical_schedules: Historical data for this activity

        Returns:
            Predicted next occurrence datetime
        """
        activity_schedules = [
            s for s in historical_schedules if s.get("activity") == activity and "date" in s
        ]

        if len(activity_schedules) < 2:
            return None

        # Get dates
        dates = []
        for s in activity_schedules:
            d = s["date"]
            if isinstance(d, str):
                dates.append(datetime.fromisoformat(d))
            elif isinstance(d, datetime):
                dates.append(d)

        if len(dates) < 2:
            return None

        dates.sort()

        # Calculate average interval
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_interval = statistics.mean(intervals)

        # Predict next date
        last_date = dates[-1]
        next_date = last_date + timedelta(days=int(avg_interval))

        return next_date
