# 🔌 API Documentation

Complete API reference for the Mew Assistant application.

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Session Management](#session-management)
- [Message Management](#message-management)
- [Summary Management](#summary-management)
- [Calendar Integration](#calendar-integration)
- [Voice Commands](#voice-commands)
- [Privacy Controls](#privacy-controls)
- [Kid & Parental Approval](#kid--parental-approval)
- [Error Handling](#error-handling)

---

## Overview

**Base URL**: `https://api.mew-assistant.example.com/api/v1`

**Environments**:
- Production: `https://api.mew-assistant.example.com`
- Staging: `https://staging.mew-assistant.example.com`
- Local: `http://localhost:8000`

**Authentication**: JWT Bearer Token (see Authentication section)

**Content-Type**: `application/json`

**API Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## Authentication

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "parent@example.com",
  "password": "SecureP@ss123",
  "name": "Jane Doe",
  "role": "parent"
}
```

**Response**:
```json
{
  "user_id": "uuid",
  "email": "parent@example.com",
  "name": "Jane Doe",
  "role": "parent",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "parent@example.com",
  "password": "SecureP@ss123"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

### Update Profile
```http
PUT /auth/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Jane Smith",
  "phone": "+1234567890"
}
```

### Change Password
```http
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldP@ss123",
  "new_password": "NewP@ss456"
}
```

---

## Session Management

### Create Session
```http
POST /sessions
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "session_type": "tutoring",
  "scheduled_at": "2024-01-15T14:00:00Z",
  "duration_minutes": 60,
  "participants": ["tutor@example.com", "student@example.com"],
  "notes": "Math tutoring - algebra"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "session_type": "tutoring",
  "scheduled_at": "2024-01-15T14:00:00Z",
  "duration_minutes": 60,
  "status": "scheduled",
  "created_at": "2024-01-10T10:00:00Z"
}
```

### Get Session
```http
GET /sessions/{session_id}
Authorization: Bearer <access_token>
```

### List Sessions
```http
GET /sessions?start_date=2024-01-01&end_date=2024-01-31&type=tutoring
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `start_date`: Filter by start date (ISO 8601)
- `end_date`: Filter by end date (ISO 8601)
- `type`: Filter by session type (scheduling, tutoring, caregiver)
- `status`: Filter by status (scheduled, completed, cancelled)
- `limit`: Number of results (default: 50, max: 100)
- `offset`: Pagination offset

### Update Session
```http
PUT /sessions/{session_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "scheduled_at": "2024-01-15T15:00:00Z",
  "notes": "Rescheduled to 3 PM"
}
```

### Cancel Session
```http
DELETE /sessions/{session_id}
Authorization: Bearer <access_token>
```

---

## Message Management

### Send Message (Ingest)
```http
POST /mew/ingest
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "channel": "email",
  "sender": "parent@example.com",
  "content": "Please schedule therapy for next Tuesday at 3 PM",
  "metadata": {
    "subject": "Therapy appointment",
    "timestamp": "2024-01-10T10:00:00Z"
  }
}
```

**Channels**: `email`, `sms`, `whatsapp`, `voice`, `web`

**Response**:
```json
{
  "message_id": "uuid",
  "status": "processed",
  "confidence_score": 0.95,
  "extracted_intent": "schedule_session",
  "action_taken": "Session scheduled for 2024-01-16T15:00:00Z",
  "requires_confirmation": false
}
```

### Confirm Action
```http
POST /mew/confirm
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message_id": "uuid",
  "confirmed": true,
  "modifications": {
    "time": "2024-01-16T14:00:00Z"
  }
}
```

### Get Message
```http
GET /messages/{message_id}
Authorization: Bearer <access_token>
```

### List Messages
```http
GET /messages?channel=email&start_date=2024-01-01
Authorization: Bearer <access_token>
```

---

## Summary Management

### Generate Summary
```http
POST /mew/summary
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "summary_type": "weekly",
  "start_date": "2024-01-08",
  "end_date": "2024-01-14",
  "include_recommendations": true
}
```

**Summary Types**: `daily`, `weekly`, `monthly`, `session`

**Response**:
```json
{
  "summary_id": "uuid",
  "period": "2024-01-08 to 2024-01-14",
  "highlights": [
    "Attended 3 therapy sessions",
    "Completed all homework assignments",
    "Made progress in reading skills"
  ],
  "concerns": [
    "Missed one tutoring session"
  ],
  "recommendations": [
    "Continue current therapy schedule",
    "Consider adding extra math tutoring"
  ],
  "metrics": {
    "sessions_attended": 5,
    "sessions_missed": 1,
    "homework_completion": 100
  },
  "generated_at": "2024-01-14T20:00:00Z"
}
```

### Get Summary
```http
GET /summaries/{summary_id}
Authorization: Bearer <access_token>
```

### List Summaries
```http
GET /summaries?type=weekly&limit=10
Authorization: Bearer <access_token>
```

---

## Calendar Integration

### Connect Calendar
```http
POST /calendar/connect
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "provider": "google",
  "credentials": {
    "access_token": "ya29.a0AfH6SMB...",
    "refresh_token": "1//0gB..."
  }
}
```

**Providers**: `google`, `apple`, `outlook`

### Sync Calendar
```http
POST /calendar/sync
Authorization: Bearer <access_token>
```

### Get Calendar Events
```http
GET /calendar/events?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <access_token>
```

### Create Calendar Event
```http
POST /calendar/events
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Therapy Session",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "location": "Therapy Center",
  "description": "Weekly therapy session",
  "attendees": ["parent@example.com", "therapist@example.com"],
  "reminders": [15, 60]
}
```

### Update Calendar Event
```http
PUT /calendar/events/{event_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "start_time": "2024-01-15T11:00:00Z",
  "end_time": "2024-01-15T12:00:00Z"
}
```

### Delete Calendar Event
```http
DELETE /calendar/events/{event_id}
Authorization: Bearer <access_token>
```

---

## Voice Commands

### Process Voice Command
```http
POST /voice/command
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "audio": <audio_file>,
  "language": "auto"
}
```

**Response**:
```json
{
  "command_id": "uuid",
  "detected_language": "en-US",
  "transcription": "Schedule therapy for next Tuesday at 3 PM",
  "intent": "schedule_session",
  "confidence": 0.95,
  "action_taken": "Session scheduled",
  "response_text": "I've scheduled therapy for Tuesday, January 16th at 3 PM",
  "response_audio_url": "https://..."
}
```

### Voice Platform Webhook
```http
POST /voice/webhook
Content-Type: application/json
Authorization: Bearer <platform_token>

{
  "platform": "alexa",
  "user_id": "user123",
  "intent": "GetSchedule",
  "slots": {
    "date": "tomorrow"
  },
  "session_id": "session123"
}
```

**Platforms**: `alexa`, `google`, `siri`, `tesla`

---

## Privacy Controls

### Export User Data
```http
GET /privacy/export
Authorization: Bearer <access_token>
```

**Response**: ZIP file with all user data

### Delete User Account
```http
DELETE /privacy/account
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "confirmation": "DELETE",
  "password": "UserP@ss123"
}
```

### Update Privacy Settings
```http
PUT /privacy/settings
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "data_collection": {
    "analytics": false,
    "voice_recordings": true,
    "usage_data": true
  },
  "marketing": {
    "email": false,
    "sms": false
  }
}
```

### Get Privacy Settings
```http
GET /privacy/settings
Authorization: Bearer <access_token>
```

---

## Kid & Parental Approval

### Kid Makes Request
```http
POST /kids/requests
Authorization: Bearer <kid_token>
Content-Type: application/json

{
  "request_type": "play_date",
  "description": "Play date with Alex on Saturday",
  "details": {
    "friend": "Alex",
    "date": "2024-01-20",
    "time": "14:00",
    "duration_hours": 2
  }
}
```

**Response**:
```json
{
  "request_id": "uuid",
  "status": "pending_approval",
  "submitted_at": "2024-01-15T10:00:00Z",
  "message_to_kid": "I've sent your request to your parents. They'll let you know soon!"
}
```

### Parent Lists Approval Requests
```http
GET /approvals/pending
Authorization: Bearer <parent_token>
```

**Response**:
```json
{
  "pending_requests": [
    {
      "request_id": "uuid",
      "kid_name": "Tommy",
      "request_type": "play_date",
      "description": "Play date with Alex on Saturday",
      "submitted_at": "2024-01-15T10:00:00Z",
      "priority": "normal",
      "context": {
        "last_play_date": "2024-01-08",
        "conflicts": null,
        "recommendation": "Approve - good social activity"
      }
    }
  ]
}
```

### Parent Approves/Denies Request
```http
POST /approvals/{request_id}/decision
Authorization: Bearer <parent_token>
Content-Type: application/json

{
  "decision": "approved",
  "message_to_kid": "Yes, you can have a play date with Alex! Have fun!",
  "modifications": {
    "time": "15:00"
  }
}
```

**Decision**: `approved`, `denied`, `needs_modification`

### Get Smart Rules
```http
GET /approvals/rules
Authorization: Bearer <parent_token>
```

### Create Smart Rule
```http
POST /approvals/rules
Authorization: Bearer <parent_token>
Content-Type: application/json

{
  "rule_name": "Weekday play dates",
  "conditions": {
    "request_type": "play_date",
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "after_time": "homework_done",
    "approved_friends": ["Alex", "Jordan"]
  },
  "auto_approve": true,
  "max_per_week": 2
}
```

---

## Error Handling

All API errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "details": {
      "field": "scheduled_at",
      "expected": "ISO 8601 format"
    },
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid authentication |
| `PERMISSION_DENIED` | 403 | User lacks required permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Temporary service issue |

### Rate Limits

| Tier | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Anonymous | 10 | 100 |
| Authenticated | 100 | 10,000 |
| Premium | 1,000 | 100,000 |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642253400
```

---

## Webhooks

Subscribe to events:

```http
POST /webhooks/subscriptions
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["session.created", "session.updated", "approval.requested"],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload**:
```json
{
  "event": "session.created",
  "data": {
    "session_id": "uuid",
    "session_type": "tutoring",
    "scheduled_at": "2024-01-15T14:00:00Z"
  },
  "timestamp": "2024-01-10T10:00:00Z",
  "signature": "sha256=..."
}
```

**Verify Signature**:
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## SDKs

### Python
```python
from mew_assistant import MewClient

client = MewClient(api_key="your_api_key")

# Create session
session = client.sessions.create(
    session_type="tutoring",
    scheduled_at="2024-01-15T14:00:00Z",
    duration_minutes=60
)

# Get summary
summary = client.summaries.create(
    summary_type="weekly",
    start_date="2024-01-08",
    end_date="2024-01-14"
)
```

### JavaScript/TypeScript
```javascript
import { MewClient } from '@mew-assistant/sdk';

const client = new MewClient({ apiKey: 'your_api_key' });

// Create session
const session = await client.sessions.create({
  sessionType: 'tutoring',
  scheduledAt: '2024-01-15T14:00:00Z',
  durationMinutes: 60
});

// Get summary
const summary = await client.summaries.create({
  summaryType: 'weekly',
  startDate: '2024-01-08',
  endDate: '2024-01-14'
});
```

---

## Testing

### Test API Keys

Use these for testing (staging only):
```
Test Parent: test_parent_key_abc123
Test Kid: test_kid_key_xyz789
Test Caregiver: test_caregiver_key_def456
```

### Example Requests

Full examples available at: https://github.com/your-org/mew-assistant/tree/main/examples

---

## Support

**API Support**: api-support@mew-assistant.example.com
**Documentation**: https://docs.mew-assistant.example.com
**Status Page**: https://status.mew-assistant.example.com

**Last Updated**: 2024-11-15
**API Version**: v1
