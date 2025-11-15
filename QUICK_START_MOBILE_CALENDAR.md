# Quick Start: Mobile & Calendar Integration

## 🚀 Getting Started in 5 Minutes

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt
```

---

## 📱 Mobile Integration Quick Start

### 1. Initialize Mobile Services

#### iOS (APNs)
```python
from app.integrations.mobile_integration import MobileIntegration, MobilePlatform

mobile = MobileIntegration()

# Initialize APNs
credentials = {
    "key_path": "/path/to/AuthKey.p8",
    "key_id": "YOUR_KEY_ID",
    "team_id": "YOUR_TEAM_ID",
    "topic": "com.mewassistant.app"
}
await mobile.initialize_apns(credentials)
```

#### Android (FCM)
```python
credentials = {
    "service_account_path": "/path/to/firebase-service-account.json"
}
await mobile.initialize_fcm(credentials)
```

### 2. Send Your First Push Notification

```python
# Send to iOS device
await mobile.send_push_notification(
    platform=MobilePlatform.IOS,
    device_token="your_device_token",
    title="Therapy Reminder",
    body="Your session starts in 30 minutes",
    badge=1
)

# Send to Android device
await mobile.send_push_notification(
    platform=MobilePlatform.ANDROID,
    device_token="your_device_token",
    title="Therapy Reminder",
    body="Your session starts in 30 minutes"
)
```

### 3. Generate Deep Links

```python
links = mobile.generate_deep_link(
    screen="session/details",
    params={"session_id": "123"}
)

print(f"iOS: {links['ios']}")
print(f"Android: {links['android']}")
print(f"Universal: {links['universal']}")
```

### 4. API Usage Examples

```bash
# Register device
curl -X POST "http://localhost:8000/mobile/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "device_token": "abc123...",
    "device_info": {"model": "iPhone 14", "os_version": "17.0"}
  }'

# Send notification
curl -X POST "http://localhost:8000/mobile/notifications/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "device_token": "abc123...",
    "title": "Reminder",
    "body": "Medication time!",
    "badge": 1
  }'
```

---

## 📅 Calendar Integration Quick Start

### 1. Connect to Calendar Provider

#### Google Calendar
```python
from app.integrations.calendar_integration import CalendarIntegration, CalendarProvider

calendar = CalendarIntegration()

# Connect to Google Calendar
credentials = {
    "token": "your_oauth2_token",
    "refresh_token": "refresh_token"
}
await calendar.connect_google_calendar(credentials)
```

#### Apple iCloud Calendar
```python
credentials = {
    "username": "your@icloud.com",
    "app_specific_password": "xxxx-xxxx-xxxx-xxxx",
    "server": "https://caldav.icloud.com"
}
await calendar.connect_apple_calendar(credentials)
```

#### Microsoft Outlook
```python
credentials = {
    "client_id": "your_client_id",
    "tenant_id": "your_tenant_id",
    "client_secret": "your_client_secret"
}
await calendar.connect_outlook_calendar(credentials)
```

### 2. Create Your First Calendar Event

```python
from datetime import datetime, timedelta

start = datetime.now() + timedelta(days=1, hours=14)
end = start + timedelta(hours=1)

event_id = await calendar.create_event(
    provider=CalendarProvider.GOOGLE,
    title="Therapy Session",
    start_time=start,
    end_time=end,
    description="Weekly therapy with Dr. Smith",
    location="123 Main St",
    attendees=["therapist@example.com", "parent@example.com"],
    reminder_minutes=30
)

print(f"Event created: {event_id}")
```

### 3. Get Upcoming Events

```python
events = await calendar.get_upcoming_events(
    provider=CalendarProvider.GOOGLE,
    days_ahead=7
)

for event in events:
    print(f"{event['title']} - {event['start']}")
```

### 4. API Usage Examples

```bash
# Connect to Google Calendar
curl -X POST "http://localhost:8000/calendar/connect/google" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {"token": "oauth2_token"}
  }'

# Create event
curl -X POST "http://localhost:8000/calendar/events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "title": "Therapy Session",
    "start_time": "2024-01-15T14:00:00Z",
    "end_time": "2024-01-15T15:00:00Z",
    "description": "Weekly therapy",
    "reminder_minutes": 30
  }'

# Get upcoming events
curl -X POST "http://localhost:8000/calendar/events/upcoming" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "days_ahead": 7
  }'
```

---

## 🎯 Common Use Cases

### Use Case 1: Therapy Appointment Flow

```python
# 1. Create calendar event
event_id = await calendar.create_event(
    provider=CalendarProvider.GOOGLE,
    title="Therapy with Emma",
    start_time=appointment_time,
    end_time=appointment_time + timedelta(hours=1),
    reminder_minutes=30
)

# 2. Send push notification reminder
await mobile.send_push_notification(
    platform=MobilePlatform.IOS,
    device_token=parent_device_token,
    title="Upcoming Therapy",
    body="Emma's therapy session in 30 minutes",
    data={"event_id": event_id, "type": "therapy"}
)

# 3. Generate deep link for details
links = mobile.generate_deep_link(
    screen="therapy/session",
    params={"event_id": event_id}
)
```

### Use Case 2: Medication Reminder

```python
# Schedule daily reminder
await mobile.send_scheduled_reminder(
    user_id=user_id,
    platform=MobilePlatform.IOS,
    device_token=device_token,
    title="Medication Reminder",
    body="Time for morning medication",
    scheduled_time="2024-01-15T08:00:00Z",
    data={"medication_id": "med_123"}
)
```

### Use Case 3: Multi-Device Family Notification

```python
# Send to all family devices
device_tokens = [
    mom_ios_token,
    dad_android_token,
    caregiver_android_token
]

await mobile.send_batch_notifications(
    platform=MobilePlatform.IOS,  # or send separately per platform
    device_tokens=device_tokens,
    title="Schedule Change",
    body="Tomorrow's therapy moved to 3 PM",
    data={"type": "schedule_change"}
)
```

---

## 🔧 Configuration Checklist

### iOS Setup
- [ ] Apple Developer Account
- [ ] APNs Authentication Key (.p8 file)
- [ ] Key ID from Apple Developer Portal
- [ ] Team ID from Apple Developer Portal
- [ ] App Bundle ID

### Android Setup
- [ ] Firebase project created
- [ ] Cloud Messaging enabled
- [ ] Service account JSON downloaded
- [ ] FCM configured in app

### Google Calendar Setup
- [ ] Google Cloud Project created
- [ ] Calendar API enabled
- [ ] OAuth2 credentials configured
- [ ] Consent screen configured

### Apple Calendar Setup
- [ ] iCloud account
- [ ] App-specific password generated
- [ ] CalDAV access enabled

### Outlook Calendar Setup
- [ ] Microsoft 365 account
- [ ] App registration in Azure AD
- [ ] Microsoft Graph API permissions
- [ ] Client secret generated

---

## 📚 Additional Resources

- [Full API Documentation](README.md)
- [Integration Tests](tests/test_mobile_integration.py)
- [Calendar Tests](tests/test_calendar_integration.py)
- [Implementation Summary](MOBILE_CALENDAR_SUMMARY.md)

---

## 💡 Tips & Best Practices

1. **Always validate device tokens** before sending notifications
2. **Use batch notifications** for multiple devices to improve efficiency
3. **Handle timezone properly** when creating calendar events
4. **Set appropriate reminder times** (15-60 minutes typically works best)
5. **Include deep links** in notification data for better UX
6. **Test on both iOS and Android** before production deployment
7. **Monitor notification delivery rates** and adjust as needed
8. **Respect user notification preferences** and do-not-disturb settings

---

## 🐛 Troubleshooting

### Mobile Notifications Not Sending
- Verify device token is valid
- Check APNs/FCM credentials are configured
- Ensure certificates are not expired
- Verify app has notification permissions

### Calendar Events Not Creating
- Check OAuth tokens are valid
- Verify calendar permissions granted
- Ensure timezone formatting is correct
- Check for conflicting events

### Deep Links Not Working
- Verify URL schemes configured in mobile app
- Check universal links domain association
- Test on actual devices, not just simulators

---

**Need Help?** Check the [full documentation](README.md) or [open an issue](https://github.com/skakumanu/mew-assistant/issues).
