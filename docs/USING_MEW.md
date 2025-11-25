# Using Mew Assistant - Quick Start Guide

Congratulations! You've successfully authenticated with Google OAuth. Here's what you can do now:

## Your Access Token
Save your access token for making API calls:
```bash
export TOKEN="your_access_token_here"
export APP_URL="https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io"
```

## Test Your Authentication
```bash
# Get your user profile
curl -X GET $APP_URL/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Core Features

### 1. Calendar Integration
```bash
# Connect your Google Calendar
curl -X POST $APP_URL/calendar/connect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "calendar_id": "primary"
  }'

# List your calendars
curl -X GET $APP_URL/calendar/list \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Schedule Management
```bash
# Get schedule summary
curl -X GET $APP_URL/mew/summary \
  -H "Authorization: Bearer $TOKEN"

# Ingest a scheduling request (via voice or text)
curl -X POST $APP_URL/mew/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Schedule dentist appointment next Tuesday at 2pm",
    "channel": "siri"
  }'
```

### 3. Voice Commands (via Siri)
Once you set up the Siri Shortcut (see SIRI_SETUP_GUIDE.md):

- "Hey Siri, ask Mew what's my schedule today"
- "Hey Siri, tell Mew to schedule therapy tomorrow at 3pm"
- "Hey Siri, ask Mew for my weekly summary"

### 4. Kid Account Management
```bash
# Add a kid account (requires parent role)
curl -X POST $APP_URL/auth/kid/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Child Name",
    "age": 10,
    "avatar_emoji": "��"
  }'
```

## Next Steps

1. **Set up Siri Shortcut**: Follow `docs/SIRI_SETUP_GUIDE.md`
2. **Connect Calendar**: Link your Google Calendar for automatic scheduling
3. **Configure Preferences**: Set your timezone, notification preferences
4. **Invite Family**: Add other parents or caregivers

## Getting Help

- Test endpoints: `$APP_URL/docs` (Swagger UI)
- View all schedules: `$APP_URL/mew/summary`
- Get confirmations: `$APP_URL/mew/confirm`

## Mobile Access

Access Mew from your phone:
1. Visit: `$APP_URL/auth/simple/login`
2. Sign in with Google
3. Save to home screen for quick access
