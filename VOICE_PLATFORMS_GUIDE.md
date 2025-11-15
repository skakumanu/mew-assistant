# Multi-Platform Voice Assistant Integration - Phase 8

## Overview
Mew Assistant now seamlessly integrates with **all major voice platforms** to provide hands-free family coordination:

- **Apple Siri** (iOS, macOS, HomePod, Apple Watch)
- **Amazon Alexa** (Echo devices, Fire TV)
- **Google Assistant** (Android, Google Home)
- **Tesla Voice** (In-vehicle commands)

## Features

### Universal Voice Access
- **Natural Language Processing**: Speak naturally in any supported language
- **Automatic Language Detection**: System auto-detects 100+ languages
- **Context-Aware**: Understands family context and preferences
- **Multi-Platform Sync**: Commands work across all platforms

### Supported Commands

#### Scheduling
```
"Hey Siri, tell Mew to schedule therapy at 2pm tomorrow"
"Alexa, ask Mew when is my next appointment"
"Ok Google, have Mew reschedule piano lessons to Friday"
"Tesla, schedule pickup at school at 3:30"
```

#### Summaries
```
"Hey Siri, ask Mew for today's summary"
"Alexa, what's on my schedule today"
"Ok Google, get my family's weekly summary"
"Tesla, what's next on my schedule"
```

#### Queries
```
"Hey Siri, ask Mew when is tutoring"
"Alexa, when did we last see the therapist"
"Ok Google, what time is dinner"
```

## Platform-Specific Setup

### Apple Siri Integration

#### iOS Shortcuts
1. Open **Shortcuts** app on iPhone/iPad
2. Tap **+** to create new shortcut
3. Add **"Get Contents of URL"** action
4. URL: `https://your-mew-instance.com/api/v1/voice/siri/webhook`
5. Method: **POST**
6. Add **"Speak Text"** action to hear response
7. Name shortcut **"Mew"** or **"Ask Mew"**

#### SiriKit Integration (for iOS App)
```swift
// In your iOS app's Info.plist
<key>NSUserActivityTypes</key>
<array>
    <string>INCreateEventIntent</string>
    <string>INSetTaskAttributeIntent</string>
</array>
```

#### HomePod/Apple Watch
Works automatically once iOS shortcuts are configured.

**Example:**
```
"Hey Siri, Mew schedule therapy"
"Hey Siri, run Mew summary"
```

### Amazon Alexa Integration

#### Enable Mew Skill
1. Open **Alexa app**
2. Go to **Skills & Games**
3. Search for **"Mew Assistant"**
4. Click **Enable**
5. Link your Mew account

#### Custom Invocations
```
"Alexa, ask Mew to schedule"
"Alexa, open Mew"
"Alexa, tell Mew I need a summary"
```

#### Skill Configuration
```json
{
  "manifest": {
    "publishingInformation": {
      "name": "Mew Assistant",
      "summary": "Family assistant for scheduling"
    },
    "apis": {
      "custom": {
        "endpoint": {
          "uri": "https://your-mew-instance.com/api/v1/voice/alexa/webhook"
        }
      }
    }
  }
}
```

### Google Assistant Integration

#### Enable Action
1. Open **Google Home** app
2. Tap **+** → **Set up device** → **Works with Google**
3. Search for **"Mew Assistant"**
4. Sign in to link account

#### Voice Commands
```
"Ok Google, talk to Mew"
"Ok Google, ask Mew about my schedule"
"Ok Google, tell Mew to reschedule"
```

#### Actions Console Setup
```yaml
actions:
  - name: MAIN
    intent:
      name: actions.intent.MAIN
    fulfillment:
      url: https://your-mew-instance.com/api/v1/voice/google/webhook
```

### Tesla Integration

#### In-Vehicle Setup
1. Open **Tesla app**
2. Go to **Profile** → **Settings**
3. Select **Voice Commands**
4. Enable **Third-Party Apps**
5. Add **Mew Assistant**

#### Voice Commands While Driving
```
"Schedule pickup at school at 3pm"
"What's next on my schedule"
"Navigate to therapy appointment"
```

**Safety Features:**
- Brief responses while driving
- Automatic navigation integration
- Context-aware (knows you're driving)

## API Endpoints

### Webhook Endpoints

#### Siri Webhook
```http
POST /api/v1/voice/siri/webhook
Content-Type: application/json
Authorization: Bearer <siri-signature>

{
  "intent": "INCreateEventIntent",
  "slots": {
    "title": "Therapy Session",
    "startDate": "2024-01-15T14:00:00Z"
  },
  "user_id": "user_123"
}
```

#### Alexa Webhook
```http
POST /api/v1/voice/alexa/webhook
Content-Type: application/json

{
  "version": "1.0",
  "session": {
    "user": {"userId": "user_123"},
    "application": {"applicationId": "skill_id"}
  },
  "request": {
    "type": "IntentRequest",
    "intent": {
      "name": "ScheduleAppointment",
      "slots": {
        "Activity": {"value": "therapy"}
      }
    }
  }
}
```

#### Google Assistant Webhook
```http
POST /api/v1/voice/google/webhook
Content-Type: application/json

{
  "user": {"userId": "user_123"},
  "inputs": [{
    "intent": "schedule.create",
    "arguments": [
      {"name": "activity", "value": "therapy"}
    ]
  }]
}
```

#### Tesla Webhook
```http
POST /api/v1/voice/tesla/webhook
Content-Type: application/json
X-Tesla-Signature: <signature>

{
  "vehicle_id": "vehicle_123",
  "user_id": "user_123",
  "command": "schedule",
  "parameters": {
    "activity": "pickup",
    "time": "3:30 PM"
  },
  "driving": true
}
```

## Multi-Language Support

All voice platforms support **automatic language detection** for:

### Americas
- English, Spanish, Portuguese, French

### Europe
- German, Italian, Dutch, Polish, Russian, Ukrainian

### Asia
- Mandarin, Cantonese, Japanese, Korean, Hindi, Tamil, Arabic

### And 90+ more languages...

**No configuration needed** - system auto-detects the language spoken!

## Security

### Authentication
- **Signature Verification**: All requests verified with platform-specific signatures
- **OAuth 2.0**: Account linking with secure tokens
- **Rate Limiting**: Protection against abuse

### Privacy
- **COPPA Compliant**: Kid-safe voice interactions
- **HIPAA Compliant**: Secure health information
- **Data Encryption**: All voice data encrypted in transit and at rest

### Parental Controls
- Kids' voice commands require **parent approval** for sensitive actions
- Smart approval rules reduce approval fatigue
- Audit logs of all voice interactions

## Development

### Register New Platform
```python
from app.integrations.voice_platforms import BaseVoicePlatform

class MyPlatform(BaseVoicePlatform):
    async def authenticate(self, credentials):
        # Verify request
        return True
    
    async def handle_intent(self, intent, slots, user_id):
        # Process command
        return {"success": True, "speech": "Done"}
    
    async def send_response(self, response):
        # Format response
        return True
    
    async def register_skill(self, config):
        # Register with platform
        return True
```

### Testing
```bash
# Test Siri integration
curl -X POST http://localhost:8000/api/v1/voice/siri/webhook \
  -H "Content-Type: application/json" \
  -d '{"intent": "INCreateEventIntent", "slots": {...}}'

# Test Alexa integration
curl -X POST http://localhost:8000/api/v1/voice/alexa/webhook \
  -H "Content-Type: application/json" \
  -d '{"version": "1.0", "request": {...}}'
```

## Architecture

### Flow Diagram
```
Voice Platform (Siri/Alexa/Google/Tesla)
    ↓
Platform-Specific Webhook
    ↓
Authentication Layer
    ↓
Intent Parser
    ↓
Message Service (with language detection)
    ↓
Response Formatter
    ↓
Voice Platform Response
```

### Components
- **`BaseVoicePlatform`**: Abstract base class for all platforms
- **`SiriIntegration`**: Apple Siri/SiriKit handler
- **`AlexaIntegration`**: Amazon Alexa skill handler
- **`GoogleAssistantIntegration`**: Google Actions handler
- **`TeslaIntegration`**: Tesla voice command handler
- **`voice_platforms_router`**: FastAPI router for webhooks

## Deployment

### Environment Variables
```bash
# Siri
SIRI_APP_ID=your_app_id
SIRI_SIGNING_KEY=your_key

# Alexa
ALEXA_SKILL_ID=your_skill_id
ALEXA_CLIENT_ID=your_client_id
ALEXA_CLIENT_SECRET=your_secret

# Google
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_SERVICE_ACCOUNT=service_account.json

# Tesla
TESLA_API_KEY=your_api_key
```

### Podman Deployment
```bash
# Build with voice support
podman-compose build

# Start services
podman-compose up -d

# Verify voice platforms
curl http://localhost:8000/api/v1/voice/platforms
```

## Monitoring

### Logging
All voice interactions are logged with:
- Platform name
- Intent/command
- User ID
- Success/failure
- Response time
- Language detected

### Analytics
```python
# View voice usage
GET /api/v1/voice/analytics

# Response:
{
  "total_interactions": 1250,
  "by_platform": {
    "siri": 450,
    "alexa": 380,
    "google_assistant": 320,
    "tesla": 100
  },
  "languages": {
    "en": 850,
    "es": 200,
    "fr": 120,
    "other": 80
  }
}
```

## Troubleshooting

### Siri Not Responding
- Verify Shortcut configuration
- Check webhook URL is accessible
- Ensure HTTPS with valid certificate

### Alexa Skill Not Found
- Confirm skill is published
- Check account linking
- Verify skill ID matches

### Google Assistant Issues
- Ensure Actions project is deployed
- Verify webhook URL in console
- Check OAuth configuration

### Tesla Commands Not Working
- Confirm API key is valid
- Check vehicle is connected
- Verify third-party apps enabled

## Future Enhancements
- [ ] Samsung Bixby support
- [ ] Microsoft Cortana support
- [ ] Custom wake words
- [ ] Offline mode for critical commands
- [ ] Voice biometrics for authentication

## Contributing
See CONTRIBUTING.md for guidelines on adding new voice platform integrations.

## License
MIT License - See LICENSE file
