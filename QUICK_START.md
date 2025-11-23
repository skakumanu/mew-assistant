# 🚀 Quick Start Guide - Customer Zero

Welcome! This guide will help you get started with Mew Assistant as our first user.

## 📱 Access Your Mew Assistant

**Live Azure Deployment:**
- **API URL:** https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io
- **Docs:** https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/docs

## 1️⃣ Quick Account Setup

You're already registered! Just login:

```bash
curl -X POST https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

Save your access token from the response!

## 2️⃣ Connect Your Calendar (Apple/Google)

### Option A: Apple Calendar (iCloud)

1. **Get App-Specific Password:**
   - Go to https://appleid.apple.com
   - Sign in → Security → App-Specific Passwords
   - Click "Generate Password"
   - Name it "Mew Assistant"
   - Copy the generated password

2. **Connect to Mew:**
   ```bash
   curl -X POST https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/calendar/connect \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "provider": "apple",
       "credentials": {
         "apple_id": "your-apple-id@icloud.com",
         "app_password": "xxxx-xxxx-xxxx-xxxx"
       }
     }'
   ```

### Option B: Google Calendar

1. **Enable Google Calendar API:**
   - Go to https://console.cloud.google.com
   - Create a new project or select existing
   - Enable "Google Calendar API"
   - Create OAuth 2.0 credentials
   - Download credentials JSON

2. **Connect to Mew:**
   ```bash
   curl -X POST https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/calendar/connect \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "provider": "google",
       "credentials": {
         "client_id": "your-client-id",
         "client_secret": "your-client-secret",
         "refresh_token": "your-refresh-token"
       }
     }'
   ```

## 3️⃣ Mobile Access (From Your Phone)

### iOS (Safari/Chrome)

1. Open Safari or Chrome on your iPhone
2. Visit: https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/docs
3. Bookmark this page for quick access
4. Use the API endpoints directly or wait for our mobile app

### Android (Chrome)

1. Open Chrome on your Android device
2. Visit: https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/docs
3. Add to Home Screen for app-like experience
4. Use the API endpoints

### Quick Mobile Testing

Save this as a bookmark or use a mobile API client like "HTTP Client" (iOS) or "HTTP Request Maker" (Android):

```
POST https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/auth/login
Content-Type: application/json

{
  "email": "your-email@example.com",
  "password": "your-password"
}
```

## 4️⃣ Voice Integration Setup

### Siri Shortcuts (iOS)

1. Open **Shortcuts** app on iPhone
2. Tap **+** to create new shortcut
3. Add "Get Contents of URL" action
4. Configure:
   - URL: `https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/voice/siri`
   - Method: POST
   - Headers: 
     - `Authorization: Bearer YOUR_TOKEN`
     - `Content-Type: application/json`
   - Body: `{"text": "Shortcut Input"}`
5. Name it "Ask Mew"
6. Test: "Hey Siri, Ask Mew to schedule dentist appointment tomorrow"

### Amazon Alexa

1. Coming soon - We'll publish the Alexa Skill
2. Enable "Mew Assistant" skill in Alexa app
3. Link your account
4. Say: "Alexa, ask Mew to show my schedule"

### Google Assistant

1. Coming soon - We'll publish Google Action
2. Enable "Mew Assistant" in Google Home app
3. Link your account
4. Say: "Hey Google, talk to Mew about my calendar"

## 5️⃣ Test Your Setup

### Check Calendar Connection
```bash
curl -X GET https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/calendar/events \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create a Schedule Event
```bash
curl -X POST https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/mew/ingest \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "api",
    "content": "Schedule dentist appointment tomorrow at 3pm"
  }'
```

### Get Daily Summary
```bash
curl -X GET https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/mew/summary \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 6️⃣ Common Commands

| What You Want | Voice/Text Command |
|--------------|-------------------|
| Schedule appointment | "Schedule [activity] [when]" |
| Check schedule | "What's on my calendar?" |
| Daily summary | "Give me today's summary" |
| Add reminder | "Remind me to [task] at [time]" |
| Check conflicts | "Any conflicts today?" |

## 🆘 Need Help?

- **API Docs:** https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/docs
- **GitHub Issues:** https://github.com/skakumanu/mew-assistant/issues
- **Email Support:** Open an issue for now

## 📊 Monitor Your Usage

Check logs and usage:
```bash
curl -X GET https://mew-app.politecoast-f8c6a8e3.eastus.azurecontainerapps.io/health \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🎯 Next Steps

1. ✅ Connect your calendar (Apple or Google)
2. ✅ Test from mobile device
3. ✅ Set up Siri Shortcut
4. ✅ Try voice commands
5. ✅ Share feedback!

---

**Welcome to Mew Assistant - Your AI family scheduler!** 🎉

*Last Updated: 2025-01-23*
