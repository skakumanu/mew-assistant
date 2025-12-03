# Mew Assistant - Complete Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Customer Zero Setup](#customer-zero-setup)
3. [Registration & Authentication](#registration--authentication)
4. [Features & Capabilities](#features--capabilities)
5. [Voice Integration](#voice-integration)
6. [API Documentation](#api-documentation)

---

# 🚀 Quick Start - Deploy Mew Assistant in 2 Hours

## What You'll Get
- ✅ Production-ready Mew Assistant running in Azure
- ✅ PostgreSQL database with encryption
- ✅ HTTPS/SSL enabled automatically
- ✅ Cost: ~$15-20/month (or FREE for 12 months with Azure Free Tier)
- ✅ Ready to use via SMS, email, voice, and web

---

## Prerequisites (5 minutes)

### 1. Create Azure Account
- Visit: https://azure.microsoft.com/free/
- Get $200 credit + 12 months free services
- No credit card required for first 30 days

### 2. Install Azure CLI
```bash
# Linux/WSL
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Mac
brew install azure-cli

# Windows
# Download from: https://aka.ms/installazurecliwindows
```

### 3. Login to Azure
```bash
az login
```

---

## Deployment (10 minutes)

### Option 1: Automated Script (Recommended)
```bash
# Clone and navigate to repo (if not already there)
cd mew-assistant

# Run the magic script
./infrastructure/azure/quick-deploy.sh
```

**That's it!** The script will:
1. Create all Azure resources
2. Configure database
3. Set up app service
4. Generate secure credentials
5. Give you the app URL

### Option 2: Manual Deployment
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for step-by-step manual instructions.

---

## Post-Deployment Setup (20 minutes)

### 1. Configure GitHub Secrets (for auto-deploy)
After running quick-deploy.sh, you'll have a `deployment-credentials.txt` file.

```bash
# Add to GitHub secrets:
# Settings > Secrets and variables > Actions > New repository secret

# Required secrets:
AZURE_WEBAPP_NAME=<your-app-name>
AZURE_WEBAPP_PUBLISH_PROFILE=<download from Azure Portal>
```

### 2. Configure Third-Party Services

#### OpenAI (for AI features)
```bash
az webapp config appsettings set \
  --resource-group mew-assistant-rg \
  --name <your-app-name> \
  --settings OPENAI_API_KEY="sk-..."
```

#### Email (Gmail example)
```bash
# Create App Password: https://myaccount.google.com/apppasswords
az webapp config appsettings set \
  --resource-group mew-assistant-rg \
  --name <your-app-name> \
  --settings \
    SMTP_HOST="smtp.gmail.com" \
    SMTP_USER="your-email@gmail.com" \
    SMTP_PASSWORD="your-app-password"
```

#### SMS/WhatsApp (Twilio)
```bash
# Sign up: https://www.twilio.com/try-twilio
az webapp config appsettings set \
  --resource-group mew-assistant-rg \
  --name <your-app-name> \
  --settings \
    TWILIO_ACCOUNT_SID="AC..." \
    TWILIO_AUTH_TOKEN="..." \
    TWILIO_PHONE_NUMBER="+1..."
```

---

## Start Using Mew (30 minutes)

### 1. Create Your Account
```bash
# Replace with your app URL from deployment-credentials.txt
APP_URL="https://your-app.azurewebsites.net"

curl -X POST $APP_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "SecurePassword123!",
    "full_name": "Your Name",
    "role": "parent"
  }'
```

### 2. Get Your Access Token
```bash
curl -X POST $APP_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "SecurePassword123!"
  }'

# Save the token you get back
export TOKEN="eyJ..."
```

### 3. Add Family Members
```bash
# Add your child
curl -X POST $APP_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "child@example.com",
    "password": "KidPassword123!",
    "full_name": "Child Name",
    "role": "child",
    "parent_email": "your-email@example.com"
  }'
```

### 4. Test Scheduling
```bash
# Schedule via API
curl -X POST $APP_URL/mew/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "web",
    "from": "your-email@example.com",
    "content": "Schedule dentist appointment for Tommy next Tuesday at 2pm"
  }'

# Check the confirmation
curl -X GET $APP_URL/mew/confirm \
  -H "Authorization: Bearer $TOKEN"
```

---

## Connect Voice Assistants (1 hour)

### Siri/iOS Shortcut
1. Open **Shortcuts** app on iPhone
2. Create new shortcut: **"Hey Siri, talk to Mew"**
3. Add action: **"Get contents of URL"**
   - URL: `https://your-app.azurewebsites.net/voice/webhook`
   - Method: POST
   - Headers: `Authorization: Bearer YOUR_TOKEN`
   - Body: Ask for input when run
4. Test: "Hey Siri, talk to Mew" → "Schedule soccer practice tomorrow at 4pm"

### Amazon Alexa
```bash
# Automated deployment
./scripts/deploy-alexa-skill.sh
```
Then say: **"Alexa, ask Mew to schedule dentist tomorrow"**

### Google Assistant
Coming soon! Check docs for updates.

---

## Connect Calendars

### Google Calendar
1. Visit: `https://your-app.azurewebsites.net/integrations/calendar/setup`
2. Login and authorize
3. Select calendars to sync

### Apple Calendar
1. Get your calendar URL from Settings
2. Add to Mew via API or web interface

---

## Monitor & Maintain

### View Logs
```bash
az webapp log tail \
  --resource-group mew-assistant-rg \
  --name <your-app-name>
```

### Check Costs
```bash
# View current month costs
az consumption usage list \
  --start-date $(date -d '1 month ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)
```

### Backup Database
```bash
# Automatic daily backups are already configured
# Manual backup:
az postgres flexible-server backup create \
  --name <your-db-name> \
  --resource-group mew-assistant-rg \
  --backup-name manual-$(date +%Y%m%d)
```

---

## Cost Breakdown (First Year)

### Free Tier (12 months)
- App Service B1: **FREE** ($13/month value)
- PostgreSQL B1: **FREE** ($5/month value)
- Storage: **$1/month**
- **Total: $1-2/month**

### After Free Tier
- **$15-20/month** for personal use
- **$50/month** for 100 families
- **$200/month** for 1,000 families

Set budget alert:
```bash
az consumption budget create \
  --budget-name mew-budget \
  --amount 25 \
  --time-grain Monthly
```

---

## Troubleshooting

### App not responding?
```bash
# Restart app
az webapp restart --resource-group mew-assistant-rg --name <your-app-name>

# Check health
curl https://your-app.azurewebsites.net/health
```

### Database connection failed?
```bash
# Check database status
az postgres flexible-server show \
  --resource-group mew-assistant-rg \
  --name <your-db-name>

# Restart database
az postgres flexible-server restart \
  --resource-group mew-assistant-rg \
  --name <your-db-name>
```

### Getting errors in logs?
```bash
# View last 100 lines
az webapp log tail \
  --resource-group mew-assistant-rg \
  --name <your-app-name> \
  | tail -100
```

---

## Next Steps

### Week 1: Personal Use
- [ ] Use it yourself for 1 week
- [ ] Test all features (SMS, email, voice)
- [ ] Note what works and what needs improvement

### Week 2-3: Family Testing
- [ ] Invite 2-3 close family/friends
- [ ] Gather feedback
- [ ] Iterate on UX

### Month 2: Soft Launch
- [ ] Invite 10-20 families from special needs community
- [ ] Set up feedback channels
- [ ] Monitor usage patterns and costs

### Month 3+: Public Launch
- [ ] Share on social media
- [ ] Post in special needs forums
- [ ] Consider non-profit structure (see docs/GOVERNANCE.md)

---

## Getting Help

- **Documentation**: Check `/docs` folder
- **Issues**: https://github.com/skakumanu/mew-assistant/issues
- **Discussions**: https://github.com/skakumanu/mew-assistant/discussions
- **Email**: (add your email once you're ready)

---

## Security Reminders

- [ ] **NEVER** commit `deployment-credentials.txt` to git
- [ ] Rotate API keys monthly
- [ ] Enable Azure Security Center
- [ ] Review access logs weekly
- [ ] Keep dependencies updated

---

**Ready to deploy?** Run: `./infrastructure/azure/quick-deploy.sh`

**Questions?** Open an issue on GitHub!

---



---

# Quick Start Registration Guide

## Access the Application

Your Mew Assistant is now running! Access it at:
- **API Documentation**: http://localhost:8888/docs
- **Alternative Docs**: http://localhost:8888/redoc
- **Base API**: http://localhost:8888

## Registration Steps

### Option 1: Using the Interactive API Docs (Easiest)

1. Open http://localhost:8888/docs in your browser
2. Find the **POST /auth/register** endpoint
3. Click "Try it out"
4. Fill in the JSON body:

```json
{
  "email": "your.email@example.com",
  "username": "your_username",
  "password": "YourSecurePassword123!",
  "full_name": "Your Full Name",
  "user_type": "parent"
}
```

5. Click "Execute"
6. You'll receive your user details and authentication token

### Option 2: Using cURL (Command Line)

```bash
curl -X POST "http://localhost:8888/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "username": "your_username",
    "password": "YourSecurePassword123!",
    "full_name": "Your Full Name",
    "user_type": "parent"
  }'
```

### Option 3: Using Python

```python
import requests

response = requests.post(
    "http://localhost:8888/auth/register",
    json={
        "email": "your.email@example.com",
        "username": "your_username",
        "password": "YourSecurePassword123!",
        "full_name": "Your Full Name",
        "user_type": "parent"
    }
)

print(response.json())
```

## User Types

- **parent**: Full access to all features (default)
- **caregiver**: Access to caregiver features, summaries
- **child**: Limited access, requires parental approval

## After Registration

1. **Save your access token** - you'll receive it in the response
2. **Login** to get a new token when needed:
   - Use `POST /auth/login` with your email and password
3. **Authorize** in Swagger UI:
   - Click the "Authorize" button at the top
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Now you can test all protected endpoints

## Quick Test After Registration

Once registered, try:

1. **Get your profile**:
```bash
curl -X GET "http://localhost:8888/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Create a session**:
```bash
curl -X POST "http://localhost:8888/sessions/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "web",
    "user_id": "YOUR_USER_ID"
  }'
```

3. **Send a message**:
```bash
curl -X POST "http://localhost:8888/mew/ingest" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Schedule a therapy session for tomorrow at 2pm",
    "channel": "web",
    "priority": "normal"
  }'
```

## Troubleshooting

### Blank Page on /docs
- Check browser console for errors (F12)
- Try refreshing the page
- Try /redoc instead

### Registration Fails
- Check if email/username already exists
- Ensure password meets requirements (min 8 chars)
- Verify all required fields are provided

### Connection Refused
- Ensure Podman containers are running: `podman ps`
- Check logs: `podman logs mew-app`
- Restart if needed: `./podman-start.sh`

## Next Steps

After successful registration:

1. ✅ Explore the API documentation at /docs
2. ✅ Set up your family profile
3. ✅ Configure calendar integrations
4. ✅ Test voice commands (if enabled)
5. ✅ Set up notification preferences

Need help? Check the README.md for detailed documentation.

---

# 🌟 Features Guide

Comprehensive guide to all features in the Mew Assistant application.

## Table of Contents
- [Mobile & Calendar Integration](#mobile--calendar-integration)
- [Voice Commands](#voice-commands)
- [Voice Platform Integration](#voice-platform-integration)
- [Kid-Friendly Features](#kid-friendly-features)
- [Parental Approval System](#parental-approval-system)

---

## Mobile & Calendar Integration

### Overview
Mew Assistant seamlessly integrates with Apple Calendar (iOS) and Google Calendar (Android) to provide intelligent scheduling for special needs families.

### Supported Platforms
- ✅ iOS (Apple Calendar via CalDAV)
- ✅ Android (Google Calendar via Google Calendar API)
- ✅ Web interface for cross-platform access

### Features

#### 1. Automatic Calendar Sync
```python
# Syncs every 5 minutes
- Pull events from mobile calendars
- Push Mew-created events to calendars
- Conflict detection and resolution
- Multi-calendar support per user
```

#### 2. Smart Scheduling
- **Therapy Sessions**: Auto-schedule recurring appointments
- **Tutoring**: Coordinate with tutor availability
- **Medical Appointments**: Send reminders with prep instructions
- **Family Time**: Block off family activities

#### 3. Calendar Sharing
- Share specific calendars with caregivers
- Permission levels: View, Edit, Manage
- Real-time updates across all devices

#### 4. Mobile Push Notifications
- Appointment reminders (15 min, 1 hour, 1 day before)
- Schedule changes
- Approval requests
- Daily agenda summary

### Setup Guide

#### iOS Setup
1. **Install the App**
   ```bash
   # Via TestFlight for beta
   # Via App Store for production release
   ```

2. **Connect Apple Calendar**
   - Open Mew Assistant app
   - Settings → Calendars → Connect Apple Calendar
   - Grant calendar access permission
   - Select calendars to sync

3. **Configure Notifications**
   - Settings → Notifications
   - Enable push notifications
   - Set reminder preferences

#### Android Setup
1. **Install the App**
   ```bash
   # Via Google Play Store
   ```

2. **Connect Google Calendar**
   - Open Mew Assistant app
   - Settings → Calendars → Connect Google Calendar
   - Sign in with Google account
   - Select calendars to sync

3. **Configure Notifications**
   - Settings → Notifications
   - Enable push notifications
   - Set reminder preferences

### API Endpoints

#### Get Calendar Events
```http
GET /api/v1/calendar/events?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

#### Create Calendar Event
```http
POST /api/v1/calendar/events
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Therapy Session",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "location": "Therapy Center",
  "attendees": ["parent@example.com"],
  "reminders": [15, 60]
}
```

#### Sync Calendar
```http
POST /api/v1/calendar/sync
Authorization: Bearer <token>
```

### Mobile App Features

#### Home Screen
- Today's agenda
- Upcoming appointments (next 7 days)
- Quick actions (Add event, Request change)

#### Calendar View
- Month view with color-coded events
- Week view with hourly breakdown
- Day view with detailed information

#### Notifications
- Smart notifications based on priority
- Quiet hours support
- Emergency override option

---

## Voice Commands

### Overview
Mew Assistant supports natural language voice commands in 100+ languages with automatic language detection.

### Supported Languages

#### Major Languages (50+ supported)
- English (US, UK, AU, CA, IN)
- Spanish (ES, MX, AR)
- French (FR, CA, BE)
- German (DE, AT, CH)
- Italian (IT)
- Portuguese (PT, BR)
- Chinese (Mandarin, Cantonese)
- Japanese
- Korean
- Arabic (Standard, Egyptian, Gulf)
- Russian
- Hindi
- And 40+ more...

### Voice Command Examples

#### Scheduling
```
"Schedule therapy session next Tuesday at 3 PM"
"Move dentist appointment to next week"
"Cancel soccer practice tomorrow"
"What's on my calendar today?"
"When is my next appointment?"
```

#### Tutoring
```
"Schedule math tutoring with Sarah"
"How is Tommy doing in reading?"
"Show me this week's homework"
"Request extra help with algebra"
```

#### Reminders
```
"Remind me to give medication at 8 PM"
"Set a reminder for school pickup"
"What reminders do I have today?"
```

#### Information Queries
```
"Summarize today's activities"
"What did the therapist say?"
"Show me this week's progress"
"Read my messages"
```

#### Kid Commands (with parental approval)
```
Kid: "Can I skip piano practice today?"
Mew: "I'll ask your parents for approval"

Kid: "Schedule play date with Alex on Saturday"
Mew: "I've sent this request to your mom for approval"
```

### Automatic Language Detection

Mew automatically detects the language being spoken:

```python
# User speaks in Spanish
User: "Programa terapia para el martes próximo a las 3"
Mew: "He programado la sesión de terapia para el martes a las 3 PM"

# Switches to English seamlessly
User: "What's my schedule tomorrow?"
Mew: "Tomorrow you have speech therapy at 10 AM and lunch with friends at noon"
```

### Voice Processing Pipeline

```
1. Audio Input → Azure Speech Service
2. Language Detection (automatic)
3. Speech-to-Text (in detected language)
4. Intent Recognition (OpenAI GPT-4)
5. Action Execution
6. Response Generation (in same language)
7. Text-to-Speech (natural voice)
8. Audio Output
```

### Voice Settings

```yaml
Settings:
  voice_speed: normal  # slow, normal, fast
  voice_gender: neutral  # male, female, neutral
  wake_word: "Hey Mew"
  confirmation_required: true
  language_preference: auto  # or specific language code
```

---

## Voice Platform Integration

### Overview
Access Mew Assistant through native voice platforms on any device.

### Supported Platforms

#### 1. Apple Siri (iOS, macOS, watchOS, HomePod)
**Setup:**
```bash
# Add to Siri Shortcuts
Settings → Siri & Search → Add Shortcut → Mew Assistant

# Example phrases:
"Hey Siri, ask Mew about my schedule"
"Hey Siri, tell Mew to reschedule therapy"
```

**Features:**
- Native iOS integration
- Handoff support
- Apple Watch compatibility
- HomePod voice control

#### 2. Amazon Alexa
**Setup:**
```bash
# Enable skill in Alexa app
Alexa app → Skills → Search "Mew Assistant" → Enable

# Example phrases:
"Alexa, ask Mew what's on my calendar"
"Alexa, tell Mew to add an appointment"
```

**Features:**
- Echo device support
- Fire tablet integration
- Alexa routines compatibility
- Multi-room audio

#### 3. Google Assistant
**Setup:**
```bash
# Link account in Google Home app
Google Home app → Settings → Services → Add Mew Assistant

# Example phrases:
"Hey Google, ask Mew about tomorrow's schedule"
"Hey Google, tell Mew to send a summary"
```

**Features:**
- Android phone integration
- Google Home devices
- Nest Hub display
- Google Assistant routines

#### 4. Tesla Integration (Grok)
**Setup:**
```bash
# Coming soon via Tesla API
# Voice commands in Tesla vehicles

# Example phrases:
"Drive me to therapy at 3 PM"
"What's my next appointment?"
"Call the therapist"
```

**Features:**
- In-car voice control
- Navigation integration
- Calendar sync
- Call initiation

### Webhook Integration

All platforms use a unified webhook API:

```http
POST /api/v1/voice/webhook
Content-Type: application/json
Authorization: Bearer <platform-token>

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

Response:
```json
{
  "speech": "Tomorrow you have therapy at 10 AM and lunch at noon",
  "display_text": "📅 Tomorrow's Schedule:\n- 10:00 AM: Therapy\n- 12:00 PM: Lunch",
  "should_end_session": false
}
```

### Platform-Specific Features

#### Alexa Skills
- Account linking with OAuth2
- Progressive response for long operations
- Display cards for Echo Show
- Multi-turn conversations

#### Siri Shortcuts
- Custom intent definitions
- Parameter suggestions
- Shortcut suggestions based on usage
- Apple Watch complications

#### Google Actions
- Interactive Canvas for visual responses
- Media playback support
- Location-based triggers
- Routine integration

---

## Kid-Friendly Features

### Overview
Special features designed to empower kids with special needs while maintaining parental oversight.

### Core Features

#### 1. Simplified Interface
```yaml
Design Principles:
  - Large, clear icons
  - High contrast colors
  - Simple language
  - Visual schedules
  - Audio feedback
  - Touch-friendly buttons
```

#### 2. Visual Schedule
```
Morning Routine:
🌅 Wake up        [✓]
🦷 Brush teeth    [✓]
🍳 Breakfast      [→]  <- Currently here
🎒 School prep    [ ]
🚌 Bus pickup     [ ]
```

#### 3. Communication Tools
- **Picture Cards**: Visual communication
- **Simple Phrases**: Pre-built common requests
- **Emoji Support**: Express feelings easily
- **Voice Input**: Speak naturally

#### 4. Reward System
```python
# Earn stars for completing tasks
task_completed → +1 star
week_goals_met → +5 stars
stars → unlock_rewards
```

#### 5. Request System

**Kid can request:**
- Schedule changes (requires approval)
- Play dates (requires approval)
- Activity swaps (requires approval)
- Help with homework (instant)
- Remind parent (instant)

**Example Flow:**
```
Kid: "Can I have a play date with Alex on Saturday?"
Mew: "That sounds fun! I'll ask your mom."
     [Sends approval request to parent]
     
Parent: [Approves in app]

Mew: "Good news! Your mom said yes to the play date!"
```

#### 6. Sensory-Friendly Options
```yaml
Settings:
  reduced_animations: true
  quiet_mode: true
  screen_filter: blue_light
  text_size: large
  audio_descriptions: enabled
```

#### 7. Emergency Features
- One-tap call parent
- "I need help" button
- Location sharing
- Emergency contacts

#### 8. Learning Mode
```
Progress tracking:
- Task completion rates
- Independence level
- Communication skills
- Social interactions
```

### Safety Features

```yaml
Kid Account Restrictions:
  - Cannot delete events
  - Cannot remove reminders
  - Cannot change emergency contacts
  - Cannot disable parental controls
  - All requests require approval
  - Activity logs sent to parents
```

---

## Parental Approval System

### Overview
Smart approval system that reduces parent overwhelm while maintaining control.

### Approval Levels

#### 1. Auto-Approved (No parent action needed)
```yaml
Auto-approved requests:
  - Help with homework
  - View schedule
  - Reminder for existing events
  - Communication with approved contacts
  - Routine tasks within trusted rules
```

#### 2. Smart Rules (Parent pre-authorizes)
```python
# Example: Weekday play dates with approved friends
rule = {
    "activity": "play_date",
    "allowed_friends": ["Alex", "Jordan", "Sam"],
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "time_range": "after_homework",
    "duration_max": "2_hours",
    "auto_approve": True
}
```

More smart rule examples:
```yaml
Screen Time Rule:
  activity: "screen_time"
  daily_limit: "2_hours"
  allowed_times: ["after_homework", "weekend_morning"]
  auto_approve: true

Activity Swap Rule:
  activity: "swap_activities"
  allowed_types: ["therapy", "tutoring"]
  notice_period: "24_hours_minimum"
  max_swaps_per_week: 2
  auto_approve: true

Treat Request Rule:
  activity: "special_treat"
  allowed_items: ["ice_cream", "cookie", "extra_dessert"]
  max_per_day: 1
  conditions: ["good_behavior", "homework_done"]
  auto_approve: true
```

#### 3. Quick Approval (One-tap decision)
```
Notification:
"Tommy wants to swap piano for swimming today"
[✓ Approve] [✗ Deny] [💬 Ask why]
```

#### 4. Batch Approval (Review weekly)
```
Weekly Digest (Sunday evening):
📋 5 requests this week:
- 3 play date requests [Review]
- 1 activity swap [Review]
- 1 extra screen time [Review]

[Approve All] [Review Each]
```

### Approval Priority Levels

#### 🔴 Urgent (requires immediate response)
- Medical appointment changes
- Emergency situations
- School-related urgent matters
- Last-minute cancellations

#### 🟡 Normal (respond within 24 hours)
- Schedule changes
- Play date requests
- Activity swaps
- Permission requests

#### 🟢 Low Priority (batch review)
- Routine changes
- Preference updates
- Non-urgent questions

### Smart Approval Features

#### 1. Context-Aware Suggestions
```python
Request: "Can I skip therapy today?"
Mew suggests to parent:
- Last attended: 2 days ago
- Next session: In 3 days
- Missed sessions this month: 0
- Recommendation: "Consider keeping - good attendance pattern"
```

#### 2. Conflict Detection
```python
Request: "Schedule play date Saturday 2 PM"
Mew notifies:
⚠️ Conflict detected: Soccer practice 1:30-3:00 PM
Suggestions:
- Move play date to 3:30 PM
- Reschedule soccer to morning
- Choose different day
```

#### 3. Learning from Approvals
```python
# System learns approval patterns
pattern = {
    "weekday_evening_playdates": usually_approved,
    "schoolnight_sleepovers": usually_denied,
    "homework_help_requests": always_approved,
    "therapy_skips": needs_reason
}
```

#### 4. Approval Delegation
```yaml
# Share approval responsibility
delegated_approvals:
  - parent1: full_access
  - parent2: full_access
  - caregiver: limited  # Can approve: snacks, schedule_view
  - grandparent: limited  # Can approve: play_dates, activities
```

### Notification Management

#### Smart Notification Timing
```python
# Don't bother parents during:
quiet_hours = {
    "workday_mornings": "7:00-9:00 AM",
    "bedtime": "9:00 PM-7:00 AM",
    "meetings": sync_with_calendar
}

# Batch non-urgent requests
if priority == "low":
    batch_until_optimal_time()  # E.g., after dinner
```

#### Notification Channels
```yaml
urgent: push_notification + SMS
normal: push_notification
low_priority: in_app_only + weekly_digest

emergency: call + push + SMS + all_caregivers
```

### Approval Analytics

Parents get weekly insights:
```
This Week's Summary:
✅ 12 requests approved automatically (smart rules)
📋 3 requests required your review
⏱️ Average response time: 2 hours
🎯 87% of requests aligned with your preferences

Top request types:
1. Play dates (5)
2. Activity swaps (3)
3. Screen time (2)

Recommendation: Consider creating a rule for play dates to reduce manual approvals
```

### Parental Control Dashboard

```
Dashboard Features:
- Real-time activity feed
- Approval queue
- Smart rule management
- Kid's daily summary
- Progress tracking
- Communication logs
- Calendar overview
- Emergency alerts
```

### Trust Building

```python
# Gradually increase kid's autonomy
trust_levels = {
    "level_1": "all_requests_need_approval",
    "level_2": "routine_requests_auto_approved",
    "level_3": "trusted_requests_auto_approved",
    "level_4": "most_requests_auto_approved"
}

# Promoted based on:
- Responsible behavior
- Following rules
- Good decision-making
- Parent comfort level
```

---

## Integration with Other Systems

### School Systems
- Canvas, Google Classroom integration
- Assignment tracking
- Grade monitoring
- Teacher communication

### Therapy Platforms
- Session notes sharing
- Progress tracking
- Goal setting
- Caregiver coordination

### Medical Records
- HIPAA-compliant integration
- Medication tracking
- Appointment reminders
- Health summaries

---

## Accessibility Features

```yaml
Visual:
  - High contrast mode
  - Large text support
  - Screen reader compatible
  - Color blind friendly palettes

Auditory:
  - Visual notifications
  - Closed captioning
  - Adjustable volume
  - Haptic feedback

Motor:
  - Voice control
  - Switch control support
  - Adjustable touch targets
  - One-handed mode

Cognitive:
  - Simple language option
  - Step-by-step guides
  - Visual schedules
  - Reduced complexity mode
```

---

## Privacy & Safety

All features are designed with privacy-first principles:
- ✅ End-to-end encryption for messages
- ✅ PII encryption at rest
- ✅ COPPA compliant
- ✅ Parental consent required
- ✅ Age-appropriate content
- ✅ Audit logs for all activities
- ✅ Right to deletion
- ✅ Data export available

---

**Last Updated**: 2024-11-15
**Version**: 2.0

---

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

---

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
