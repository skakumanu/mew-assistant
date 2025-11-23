# Voice Assistant Integration Guide

Complete guide for integrating Mew Assistant with voice platforms and enabling multilingual voice commands.

## Table of Contents
- [Overview](#overview)
- [Supported Platforms](#supported-platforms)
- [Supported Languages](#supported-languages)
- [Platform Setup](#platform-setup)
- [Voice Commands](#voice-commands)
- [Voice Registration](#voice-registration)
- [Testing](#testing)

## Overview

Mew Assistant supports seamless voice integration across multiple platforms with automatic language detection for 20+ languages. Users can schedule appointments, set reminders, and manage their family calendar using natural voice commands.

### Key Features
- ✅ Multi-platform support (Siri, Alexa, Google Assistant, Tesla Grok)
- ✅ Automatic language detection (20+ languages)
- ✅ Natural language understanding
- ✅ Voice-to-text and text-to-speech
- ✅ Voice-based registration
- ✅ Context-aware responses

## Supported Platforms

### 1. Apple Siri Shortcuts (iOS/macOS)
### 2. Amazon Alexa Skills Kit
### 3. Google Assistant Actions
### 4. Tesla Grok
### 5. Generic Voice Interface (any platform)

## Supported Languages

### Full Support (Voice Recognition + TTS)
- 🇺🇸 English (US) - `en-US`
- 🇪🇸 Spanish (Spain) - `es-ES`
- 🇫🇷 French (France) - `fr-FR`
- 🇩🇪 German (Germany) - `de-DE`
- 🇮🇹 Italian (Italy) - `it-IT`
- 🇧🇷 Portuguese (Brazil) - `pt-BR`
- 🇨🇳 Chinese (Mandarin) - `zh-CN`
- 🇯🇵 Japanese - `ja-JP`
- 🇰🇷 Korean - `ko-KR`
- 🇸🇦 Arabic (Saudi Arabia) - `ar-SA`
- 🇮🇳 Hindi (India) - `hi-IN`
- 🇷🇺 Russian - `ru-RU`

**Note:** Language is auto-detected if not specified. 100+ languages supported via Azure Cognitive Services.

## Platform Setup

### Apple Siri Shortcuts

#### Prerequisites
- iOS 13+ or macOS 10.15+
- Mew Assistant account
- Shortcuts app installed

#### Setup Steps

1. **Create API Token**
   ```bash
   curl -X POST https://your-app.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "your-email@example.com",
       "password": "your-password"
     }'
   ```
   Save the returned `access_token`.

2. **Create Shortcut in iOS**
   - Open Shortcuts app
   - Tap "+" to create new shortcut
   - Add "Ask for Input" action
     - Prompt: "What would you like to schedule?"
   - Add "Get Contents of URL" action
     - URL: `https://your-app.com/voice/siri/shortcuts`
     - Method: POST
     - Headers:
       - `Authorization: Bearer YOUR_TOKEN`
       - `Content-Type: application/json`
     - Request Body: JSON
       ```json
       {
         "text": "{Provided Input}",
         "language": "en-US",
         "provider": "siri"
       }
       ```
   - Add "Show Result" action
   - Name your shortcut "Mew Scheduler"

3. **Invoke with Siri**
   ```
   "Hey Siri, Mew Scheduler"
   "Schedule appointment with Dr. Smith tomorrow at 2pm"
   ```

---

### Amazon Alexa Skills Kit

#### Prerequisites
- Amazon Developer account
- Mew Assistant account
- AWS Lambda (optional, for advanced features)

#### Setup Steps

1. **Create Alexa Skill**
   - Go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
   - Click "Create Skill"
   - Skill name: "Mew Assistant"
   - Model: Custom
   - Hosting: Provision your own

2. **Configure Interaction Model**

   Add custom intents:
   
   **ScheduleAppointmentIntent**
   ```json
   {
     "name": "ScheduleAppointmentIntent",
     "slots": [
       {
         "name": "person",
         "type": "AMAZON.Person"
       },
       {
         "name": "time",
         "type": "AMAZON.DATE"
       }
     ],
     "samples": [
       "schedule appointment with {person} on {time}",
       "book appointment with {person} at {time}",
       "set up meeting with {person} for {time}"
     ]
   }
   ```

   **SetReminderIntent**
   ```json
   {
     "name": "SetReminderIntent",
     "slots": [
       {
         "name": "task",
         "type": "AMAZON.SearchQuery"
       },
       {
         "name": "time",
         "type": "AMAZON.DATE"
       }
     ],
     "samples": [
       "remind me to {task} at {time}",
       "set reminder for {task} on {time}"
     ]
   }
   ```

3. **Configure Endpoint**
   - Endpoint Type: HTTPS
   - Default Region: `https://your-app.com/voice/alexa/skill`
   - SSL Certificate: My development endpoint is a sub-domain...

4. **Enable Account Linking**
   - Authorization URI: `https://your-app.com/auth/authorize`
   - Access Token URI: `https://your-app.com/auth/token`
   - Client ID: Your OAuth client ID
   - Scopes: `voice:commands`, `calendar:write`

5. **Test**
   ```
   "Alexa, ask Mew Assistant to schedule therapy tomorrow at 3pm"
   "Alexa, tell Mew to show my appointments today"
   ```

---

### Google Assistant Actions

#### Prerequisites
- Google Cloud account
- Actions Console access
- Mew Assistant account

#### Setup Steps

1. **Create Actions Project**
   - Go to [Actions Console](https://console.actions.google.com/)
   - Create new project: "Mew Assistant"

2. **Configure Conversational Actions**
   
   Create `intent` for scheduling:
   ```yaml
   intent: schedule_appointment
   training:
     - schedule appointment with $person at $time
     - book meeting with $person on $time
   parameters:
     - name: person
       type: sys.any
     - name: time
       type: sys.date-time
   ```

3. **Set Webhook URL**
   - Fulfillment: `https://your-app.com/voice/google/action`
   - Authentication: OAuth 2.0
   - Configure account linking

4. **Test**
   ```
   "Hey Google, talk to Mew Assistant"
   "Schedule pickup at school at 3:30"
   ```

---

### Tesla Grok Integration

#### Setup Steps

1. **Configure Webhook**
   Tesla vehicles with Grok support can use:
   ```
   Endpoint: https://your-app.com/voice/grok/command
   ```

2. **Voice Commands in Tesla**
   ```
   "Grok, schedule therapy session tomorrow at 2pm"
   "Grok, what's on my calendar today?"
   ```

---

### Generic Voice Interface

For any other platform or custom implementation:

```bash
curl -X POST https://your-app.com/voice/command \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "text=Schedule appointment tomorrow at 2pm" \
  -F "provider=generic" \
  -F "language=en-US"
```

Or with audio:
```bash
curl -X POST https://your-app.com/voice/command \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@voice_command.wav" \
  -F "provider=generic"
```

## Voice Commands

### Scheduling Commands

```
✅ "Schedule appointment with Dr. Smith tomorrow at 2pm"
✅ "Book therapy session on Friday at 3pm"
✅ "Set up meeting with teacher next Monday at 10am"
✅ "Schedule pickup at school at 3:30 today"
```

### Reminder Commands

```
✅ "Remind me to give medication at 8am"
✅ "Set reminder for homework at 5pm"
✅ "Remind me to call therapist tomorrow"
```

### Query Commands

```
✅ "What's on my calendar today?"
✅ "Show me appointments for tomorrow"
✅ "What's my schedule this week?"
✅ "When is my next appointment?"
```

### Cancellation Commands

```
✅ "Cancel appointment with Dr. Smith"
✅ "Delete my 2pm appointment tomorrow"
✅ "Remove reminder for homework"
```

### Help Commands

```
✅ "Help"
✅ "What can you do?"
✅ "How do I schedule appointments?"
✅ "Tutorial"
```

## Voice Registration

Register for Mew Assistant using voice commands:

### Step 1: Start Registration
```
"Register new account"
OR
"Sign up"
```

### Step 2: Provide Email
```
Response: "Let's get you registered. What's your email address?"
You: "my.email@example.com"
```

### Step 3: Create Password
```
Response: "Great! Now please create a password"
You: "My password is [speak your secure password]"
```

### Step 4: Confirm
```
Response: "Perfect! Your account is created. Would you like a quick tutorial?"
```

### Passwordless Option
```
"Register with passwordless authentication"
```

## Testing

### Test Voice Command Processing

```bash
# Test with text input
curl -X POST https://your-app.com/voice/command \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule appointment tomorrow at 2pm",
    "provider": "generic",
    "language": "en-US"
  }'
```

### Test Language Detection

```bash
# Spanish
curl -X POST https://your-app.com/voice/command \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "text=Programar cita mañana a las 2pm" \
  -F "provider=generic"

# French
curl -X POST https://your-app.com/voice/command \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "text=Planifier rendez-vous demain à 14h" \
  -F "provider=generic"
```

### Test Platform-Specific Endpoints

```bash
# Siri
curl -X POST https://your-app.com/voice/siri/shortcuts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Schedule dentist appointment Friday at 10am"}'

# Alexa
curl -X POST https://your-app.com/voice/alexa/skill \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Show my calendar for today"}'

# Google Assistant
curl -X POST https://your-app.com/voice/google/action \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Set reminder for medication at 8am"}'
```

### Get Supported Languages

```bash
curl -X GET https://your-app.com/voice/supported-languages
```

### Get Platform-Specific Help

```bash
curl -X GET https://your-app.com/voice/help/siri?language=en-US
curl -X GET https://your-app.com/voice/help/alexa?language=es-ES
```

## Troubleshooting

### Issue: Voice command not recognized
**Solution:** Check language setting or let it auto-detect
```bash
curl -X POST https://your-app.com/voice/command \
  -F "text=your command" \
  -F "provider=generic"
  # Language will be auto-detected
```

### Issue: Authentication failed
**Solution:** Verify your access token is valid
```bash
curl -X GET https://your-app.com/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issue: Platform-specific integration not working
**Solution:** Check webhook configuration and endpoint URLs

## Privacy & Security

- All voice data is processed securely
- Audio files are not stored permanently
- Transcriptions are encrypted at rest
- COPPA compliant for children's voice data
- HIPAA compliant for health-related commands

## Next Steps

- [Calendar Integration](calendar-integration.md)
- [AI Scheduling](ai-scheduling.md)
- [Mobile App Setup](mobile-setup.md)
- [Compliance & Privacy](compliance.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/skakumanu/mew-assistant/issues
- Documentation: https://github.com/skakumanu/mew-assistant
