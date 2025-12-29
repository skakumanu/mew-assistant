"""
Comprehensive tests for AI integration features including:
- Conflict detection
- Smart suggestions
- Pattern learning
"""

from datetime import datetime, timedelta

import pytest

from app.schemas.schedule import ScheduleCreate
from app.services.ai_service import AIService


class TestConflictDetection:
    """Test AI-powered schedule conflict detection"""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    @pytest.fixture
    def sample_schedules(self):
        return [
            ScheduleCreate(
                title="Math Tutoring",
                start_time=datetime.now() + timedelta(hours=1),
                end_time=datetime.now() + timedelta(hours=2),
                user_id=1,
            ),
            ScheduleCreate(
                title="Speech Therapy",
                start_time=datetime.now() + timedelta(hours=1, minutes=30),
                end_time=datetime.now() + timedelta(hours=2, minutes=30),
                user_id=1,
            ),
        ]

    def test_detect_time_overlap_conflict(self, ai_service, sample_schedules):
        """Test detection of direct time overlaps"""
        conflicts = ai_service.detect_conflicts(sample_schedules)
        assert len(conflicts) > 0
        assert conflicts[0].type == "time_overlap"

    def test_detect_travel_time_conflict(self, ai_service):
        """Test detection of insufficient travel time"""
        schedules = [
            ScheduleCreate(
                title="Doctor at Hospital A",
                start_time=datetime.now() + timedelta(hours=1),
                end_time=datetime.now() + timedelta(hours=2),
                location="Hospital A, 123 Main St",
                user_id=1,
            ),
            ScheduleCreate(
                title="Therapy at Center B",
                start_time=datetime.now() + timedelta(hours=2, minutes=10),
                end_time=datetime.now() + timedelta(hours=3),
                location="Center B, 789 Oak Ave",
                user_id=1,
            ),
        ]
        conflicts = ai_service.detect_conflicts(schedules)
        assert any(c.type == "insufficient_travel_time" for c in conflicts)

    def test_detect_break_time_violation(self, ai_service):
        """Test detection of insufficient break time"""
        schedules = [
            ScheduleCreate(
                title="Morning Therapy",
                start_time=datetime.now() + timedelta(hours=1),
                end_time=datetime.now() + timedelta(hours=2),
                user_id=1,
            ),
            ScheduleCreate(
                title="Afternoon Session",
                start_time=datetime.now() + timedelta(hours=2, minutes=5),
                end_time=datetime.now() + timedelta(hours=3),
                user_id=1,
            ),
        ]
        conflicts = ai_service.detect_conflicts(schedules, min_break_minutes=15)
        assert any(c.type == "insufficient_break" for c in conflicts)

    def test_no_conflict_with_adequate_spacing(self, ai_service):
        """Test that no conflicts detected with proper spacing"""
        schedules = [
            ScheduleCreate(
                title="Morning Session",
                start_time=datetime.now() + timedelta(hours=1),
                end_time=datetime.now() + timedelta(hours=2),
                user_id=1,
            ),
            ScheduleCreate(
                title="Afternoon Session",
                start_time=datetime.now() + timedelta(hours=3),
                end_time=datetime.now() + timedelta(hours=4),
                user_id=1,
            ),
        ]
        conflicts = ai_service.detect_conflicts(schedules)
        assert len(conflicts) == 0


class TestSmartSuggestions:
    """Test AI-powered smart scheduling suggestions"""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    def test_suggest_optimal_time_slots(self, ai_service):
        """Test generation of optimal time slot suggestions"""
        existing_schedules = [
            ScheduleCreate(
                title="Morning Routine",
                start_time=datetime.now().replace(hour=8, minute=0),
                end_time=datetime.now().replace(hour=9, minute=0),
                user_id=1,
            )
        ]

        suggestions = ai_service.suggest_time_slots(
            duration_minutes=60,
            existing_schedules=existing_schedules,
            preferred_time_of_day="afternoon",
        )

        assert len(suggestions) > 0
        assert all(s.start_time.hour >= 12 for s in suggestions)

    def test_suggest_alternative_for_conflict(self, ai_service):
        """Test suggestion of alternatives when conflict detected"""
        conflicting_schedule = ScheduleCreate(
            title="New Appointment",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            user_id=1,
        )

        existing = [
            ScheduleCreate(
                title="Existing Appointment",
                start_time=datetime.now() + timedelta(hours=1, minutes=30),
                end_time=datetime.now() + timedelta(hours=2, minutes=30),
                user_id=1,
            )
        ]

        alternatives = ai_service.suggest_alternatives(conflicting_schedule, existing)

        assert len(alternatives) > 0
        for alt in alternatives:
            conflicts = ai_service.detect_conflicts([alt] + existing)
            assert len(conflicts) == 0

    def test_optimize_schedule_order(self, ai_service):
        """Test optimization of schedule ordering"""
        schedules = [
            ScheduleCreate(
                title="Location C",
                start_time=datetime.now() + timedelta(hours=3),
                end_time=datetime.now() + timedelta(hours=4),
                location="789 Oak St",
                user_id=1,
            ),
            ScheduleCreate(
                title="Location A",
                start_time=datetime.now() + timedelta(hours=1),
                end_time=datetime.now() + timedelta(hours=2),
                location="123 Main St",
                user_id=1,
            ),
            ScheduleCreate(
                title="Location B",
                start_time=datetime.now() + timedelta(hours=2),
                end_time=datetime.now() + timedelta(hours=3),
                location="456 Elm Ave",
                user_id=1,
            ),
        ]

        optimized = ai_service.optimize_schedule(schedules)

        assert len(optimized) == len(schedules)
        # Check that optimization considers location proximity
        assert optimized != schedules  # Should be reordered


class TestPatternLearning:
    """Test AI pattern learning from user behavior"""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    def test_learn_preferred_times(self, ai_service):
        """Test learning of user's preferred scheduling times"""
        historical_schedules = [
            {"hour": 9, "activity": "tutoring"},
            {"hour": 9, "activity": "tutoring"},
            {"hour": 14, "activity": "therapy"},
            {"hour": 14, "activity": "therapy"},
        ]

        patterns = ai_service.learn_patterns(historical_schedules)

        assert "tutoring" in patterns
        assert patterns["tutoring"]["preferred_hour"] == 9
        assert "therapy" in patterns
        assert patterns["therapy"]["preferred_hour"] == 14

    def test_learn_activity_duration_patterns(self, ai_service):
        """Test learning typical duration for activities"""
        historical_schedules = [
            {"activity": "tutoring", "duration": 60},
            {"activity": "tutoring", "duration": 60},
            {"activity": "tutoring", "duration": 90},
            {"activity": "therapy", "duration": 45},
            {"activity": "therapy", "duration": 45},
        ]

        patterns = ai_service.learn_patterns(historical_schedules)

        assert patterns["tutoring"]["typical_duration"] == 60  # Most common
        assert patterns["therapy"]["typical_duration"] == 45

    def test_learn_frequency_patterns(self, ai_service):
        """Test learning of activity frequency patterns"""
        historical_schedules = [
            {"activity": "tutoring", "date": "2025-01-01"},
            {"activity": "tutoring", "date": "2025-01-08"},
            {"activity": "tutoring", "date": "2025-01-15"},
            {"activity": "doctor", "date": "2025-01-01"},
            {"activity": "doctor", "date": "2025-04-01"},
        ]

        patterns = ai_service.learn_patterns(historical_schedules)

        assert patterns["tutoring"]["frequency"] == "weekly"
        assert patterns["doctor"]["frequency"] == "quarterly"

    def test_predict_next_occurrence(self, ai_service):
        """Test prediction of next activity occurrence"""
        historical_schedules = [
            {"activity": "tutoring", "date": datetime(2025, 1, 1)},
            {"activity": "tutoring", "date": datetime(2025, 1, 8)},
            {"activity": "tutoring", "date": datetime(2025, 1, 15)},
        ]

        prediction = ai_service.predict_next_occurrence(
            "tutoring", historical_schedules
        )

        assert prediction is not None
        assert prediction.date() == datetime(2025, 1, 22).date()


class TestAIServiceIntegration:
    """Integration tests for complete AI service workflow"""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    def test_end_to_end_schedule_creation(self, ai_service):
        """Test complete workflow: detect conflicts, suggest alternatives, optimize"""
        new_schedule = ScheduleCreate(
            title="New Therapy Session",
            start_time=datetime.now() + timedelta(hours=2),
            end_time=datetime.now() + timedelta(hours=3),
            user_id=1,
        )

        existing = [
            ScheduleCreate(
                title="Existing Session",
                start_time=datetime.now() + timedelta(hours=2, minutes=15),
                end_time=datetime.now() + timedelta(hours=3, minutes=15),
                user_id=1,
            )
        ]

        # Step 1: Detect conflicts
        conflicts = ai_service.detect_conflicts([new_schedule] + existing)
        assert len(conflicts) > 0

        # Step 2: Get suggestions
        alternatives = ai_service.suggest_alternatives(new_schedule, existing)
        assert len(alternatives) > 0

        # Step 3: Optimize
        optimized = ai_service.optimize_schedule(alternatives[:1] + existing)
        final_conflicts = ai_service.detect_conflicts(optimized)
        assert len(final_conflicts) == 0

    def test_pattern_based_suggestions(self, ai_service):
        """Test that suggestions incorporate learned patterns"""
        historical = [
            {"activity": "tutoring", "hour": 10, "duration": 60},
            {"activity": "tutoring", "hour": 10, "duration": 60},
        ]

        patterns = ai_service.learn_patterns(historical)

        suggestions = ai_service.suggest_time_slots(
            duration_minutes=60, activity_type="tutoring", patterns=patterns
        )

        # Should prefer morning time based on patterns
        assert any(s.start_time.hour == 10 for s in suggestions)
