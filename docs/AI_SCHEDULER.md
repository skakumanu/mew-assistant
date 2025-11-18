# AI-Powered Scheduling System

## Overview

Mew's AI Scheduler provides intelligent conflict detection, resolution suggestions, and pattern-based scheduling recommendations for families managing complex schedules.

## Features

### 1. Conflict Detection

Automatically detects scheduling conflicts with three severity levels:

- **Low**: Minor overlaps (< 15 minutes), easy to adjust
- **Medium**: Moderate conflicts (15-30 minutes) that need attention  
- **High**: Major conflicts (> 30 minutes) or involving critical activities

```python
POST /ai-scheduler/detect-conflicts
{
  "start_time": "2025-01-15T10:00:00",
  "end_time": "2025-01-15T11:00:00",
  "title": "Therapy Session",
  "activity_type": "therapy",
  "priority": "high"
}
```

**Response:**
```json
[
  {
    "conflicting_entry_id": 123,
    "conflicting_title": "Doctor Appointment",
    "conflict_type": "time_overlap",
    "severity": "high",
    "overlap_minutes": 45,
    "suggestions": [
      "Move to 02:00 PM",
      "Schedule for next available day"
    ]
  }
]
```

### 2. Smart Time Suggestions

AI learns from your scheduling patterns to suggest optimal times:

```python
POST /ai-scheduler/suggest-times
{
  "activity_type": "therapy",
  "duration_minutes": 60,
  "preferred_date": "2025-01-20T00:00:00",
  "constraints": {
    "earliest_hour": 8,
    "latest_hour": 18,
    "buffer_minutes": 15
  }
}
```

**Response:**
```json
[
  {
    "start_time": "2025-01-20T10:00:00",
    "end_time": "2025-01-20T11:00:00",
    "confidence_score": 0.85,
    "reasoning": "Highly recommended: Matches your typical scheduling pattern; Includes buffer time for transitions; Scheduled during optimal focus hours",
    "factors": [
      "Matches your typical scheduling pattern",
      "Includes buffer time for transitions",
      "Scheduled during optimal focus hours"
    ]
  }
]
```

### 3. Schedule Optimization

Optimize your entire day based on specific goals:

```python
POST /ai-scheduler/optimize-schedule
{
  "date": "2025-01-15T00:00:00",
  "optimization_goals": [
    "minimize_transitions",
    "respect_energy_levels",
    "balance_activities"
  ]
}
```

**Optimization Goals:**

- **minimize_transitions**: Group similar activities, reduce travel time
- **respect_energy_levels**: Schedule high-focus tasks during peak energy periods
- **balance_activities**: Distribute different activity types throughout the day

### 4. Pattern Learning

The AI learns from your scheduling history to provide personalized recommendations:

**Learning Status Endpoint:**
```python
GET /ai-scheduler/learning-status
```

**Requirements for Pattern Learning:**
- Minimum 5 completed activities of the same type
- Activities from the past 90 days
- Completion tracking (success/failure)

**What the AI Learns:**
- Preferred hours for different activities
- Preferred days of the week
- Typical activity duration
- Success rates by time of day

## Activity Types

Supported activity types for pattern recognition:

- `therapy` - Therapy sessions
- `tutoring` - Educational sessions
- `medical` - Medical appointments
- `social` - Social activities
- `exercise` - Physical activities
- `meal` - Meal times
- `sleep` - Sleep schedule
- `other` - General activities

## Priority Levels

Schedule entries support four priority levels:

- `low` - Flexible activities
- `normal` - Standard activities (default)
- `high` - Important activities
- `urgent` - Critical activities (therapy, medical)

## Conflict Resolution

### Automatic Resolution

For low-severity conflicts, the AI can auto-resolve based on preferences:

```python
# User preferences affecting auto-resolution
{
  "allow_overlap_for_therapy": true,
  "buffer_minutes": 15,
  "earliest_schedule_hour": 7,
  "latest_schedule_hour": 22
}
```

### Manual Resolution

For medium/high severity conflicts, the AI provides suggestions but requires user decision.

## Best Practices

### 1. Mark Completion Status

Always mark activities as completed to improve AI learning:

```python
PATCH /calendar/events/{id}
{
  "status": "completed",
  "completed_successfully": true,
  "completion_notes": "Session went well"
}
```

### 2. Set Realistic Constraints

Use constraints to guide suggestions:

```python
{
  "earliest_hour": 8,      # Don't suggest before 8am
  "latest_hour": 18,       # Don't suggest after 6pm
  "buffer_minutes": 15     # Allow 15min between activities
}
```

### 3. Build History

Use the system for at least 2 weeks to build meaningful patterns for AI learning.

### 4. Review Suggestions

Always review AI suggestions - they're recommendations, not requirements.

## Configuration

### User Preferences

Set scheduling preferences via:

```python
PUT /api/user/preferences
{
  "allow_overlap_for_therapy": false,
  "buffer_minutes": 15,
  "earliest_schedule_hour": 7,
  "latest_schedule_hour": 22,
  "peak_energy_hours": [9, 10, 11],
  "low_energy_hours": [14, 15],
  "minimize_transitions": true,
  "respect_energy_levels": true,
  "balance_activities": true
}
```

## Integration with Calendar

The AI Scheduler integrates with:

- Google Calendar
- Apple Calendar  
- Microsoft Outlook

Conflicts are detected across all integrated calendars.

## Privacy & Security

- All scheduling data is encrypted at rest
- Pattern learning happens on your data only
- No data is shared across users
- AI models run locally (no external AI service)

## Performance

- Conflict detection: < 100ms for typical schedules
- Suggestions: < 500ms including pattern analysis
- Optimization: < 2s for full day optimization

## Limitations

- Pattern learning requires minimum 5 data points per activity type
- Optimization works best with 3-10 activities per day
- Historical data limited to past 90 days
- Maximum 50 suggestions per request

## Future Enhancements

- Multi-user coordination (family scheduling)
- Weather-based activity suggestions
- Integration with transportation services
- Predictive rescheduling for anticipated delays
- Machine learning model improvements

## Support

For issues or questions:
- GitHub Issues: https://github.com/skakumanu/mew-assistant/issues
- Documentation: https://github.com/skakumanu/mew-assistant/wiki

---

**Note**: The AI Scheduler is designed to assist, not replace, human decision-making. Always review suggestions before accepting them, especially for critical activities.
