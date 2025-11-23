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
# Customer Zero Setup Guide 🎉

Welcome! You're the first user (Customer Zero) of Mew Assistant. This guide will help you get started in minutes.

## 🚀 Super Quick Start (2 Minutes)

### Option 1: Web (Easiest!)

1. **Visit**: https://mew-app-eastus2.azurewebsites.net
2. **Click**: "Get Started" button
3. **Enter**: Your name and email
4. **Check Email**: Click the magic link we sent you
5. **Done!** Start using Mew

### Option 2: SMS/Text

1. **Text**: "START YourName" to the Mew number
2. **Click**: The link we text back to you
3. **Done!** Reply with schedule requests

### Option 3: Voice (Alexa/Siri/Google)

#### Alexa
```
You: "Alexa, enable Mew Assistant skill"
Alexa: "Mew Assistant enabled. What's your name?"
You: "Srini"
Alexa: "Hi Srini! Check your email for a setup link"
```

#### Siri
```
You: "Hey Siri, setup Mew Assistant"
[Opens Safari with setup page]
Tap: "Add to Siri"
Done!
```

#### Google Assistant
```
You: "Hey Google, talk to Mew Assistant"
Google: "Sure, here's Mew Assistant"
[Follow voice prompts]
```

## 📅 Connect Your Calendar (Optional - 30 Seconds)

After you complete quick start:

### Google Calendar
1. Click "Connect Google Calendar" button
2. Choose your Google account
3. Click "Allow"
4. Done! Mew can now see and manage your schedule

### Apple Calendar
1. Click "Connect Apple Calendar" button  
2. Sign in with Apple ID
3. Allow calendar access
4. Done!

**Note**: You can skip this and add it later from Settings

## 🗣️ Start Using Voice Commands

Once setup is complete, you can:

### Through Alexa:
```
"Alexa, ask Mew to schedule therapy tomorrow at 3pm"
"Alexa, ask Mew what's on my schedule today"
"Alexa, ask Mew to reschedule the dentist appointment"
```

### Through Siri:
```
"Hey Siri, ask Mew to add a reminder"
"Hey Siri, ask Mew what's next on my schedule"
"Hey Siri, tell Mew to cancel today's appointment"
```

### Through Google:
```
"Hey Google, ask Mew to show my week"
"Hey Google, ask Mew to find time for a doctor visit"
"Hey Google, tell Mew I need to reschedule"
```

## 👨‍👩‍👧‍👦 Add Family Members (Optional)

### Add a Child:
1. Say: "Hey Mew, add my son Alex"
2. Mew: "Sure! How old is Alex?"
3. You: "7 years old"
4. Done! Alex can now make schedule requests (with your approval)

### Add a Caregiver:
1. Say: "Add caregiver Maria, email maria@example.com"
2. Mew: "I sent Maria an invite!"
3. Done! Maria can view and manage schedules

### Kid-Friendly Mode:
Kids can talk to Mew too!
```
Kid: "Mew, can I have a playdate with Emma tomorrow?"
Mew: "I'll ask mom/dad!"
[You get approval request on your phone]
You: "Yes" or "Not tomorrow, maybe Friday"
Mew tells kid: "Mom said Friday works better!"
```

## 📱 Mobile App Setup

### iPhone:
1. Open Safari: mew-assistant.org/mobile
2. Tap share icon → "Add to Home Screen"
3. Tap the Mew icon on your home screen
4. Done! Works like a native app

### Android:
1. Open Chrome: mew-assistant.org/mobile  
2. Tap menu → "Add to Home Screen"
3. Tap the Mew icon
4. Done!

## 🎯 Common First Tasks

### Schedule an Appointment:
```
"Schedule physical therapy for tomorrow at 2pm"
"Add doctor visit next Tuesday morning"
"Schedule IEP meeting for next week"
```

### Check Schedule:
```
"What's on my schedule today?"
"What do we have this week?"
"When is Alex's next therapy session?"
```

### Set Reminders:
```
"Remind me to give medication at 8am daily"
"Remind me about school pickup at 2:30pm"
"Set up medication reminder for Alex"
```

### Get Help:
```
"Help" - Shows all available commands
"What can you do?" - Explains features
"How do I...?" - Guides you through tasks
```

## 🌍 Language Support

Mew speaks 100+ languages and auto-detects!

Switch languages anytime:
```
"Switch to Spanish"
"Cambia a español"
"用中文"
"Parle français"
```

Mew automatically detects and responds in your language.

## 🔒 Privacy & Safety

- ✅ All data encrypted
- ✅ HIPAA compliant
- ✅ Kids' data protected (COPPA compliant)
- ✅ You control all data
- ✅ Delete anytime with "Delete my account"

## 💡 Pro Tips

1. **Morning Briefing**: Say "Good morning Mew" for daily schedule
2. **Smart Suggestions**: Mew learns your patterns and suggests optimal times
3. **Conflict Detection**: Mew warns you about scheduling conflicts
4. **Emergency Override**: Say "Emergency" for immediate priority
5. **Batch Requests**: "Show me all appointments this month and reschedule the conflicting ones"

## 🆘 Need Help?

### Quick Help:
- Say: "Help"
- Text: "HELP" 
- Email: support@mew-assistant.org

### Tutorial:
- Say: "Give me a tutorial"
- Visit: mew-assistant.org/tutorial

### Community:
- Discord: discord.gg/mew-assistant
- Forum: community.mew-assistant.org

## 🎉 You're All Set!

You're ready to let Mew handle your scheduling!

### Try These Now:
1. "What's my schedule for today?"
2. "Schedule a therapy session for next Monday at 10am"
3. "Remind me about medication at 8pm"

**Welcome to the Mew family! 🐱**

---

## 📝 Your Customer Zero Credentials

As the first user, here's your setup:

- **Email**: skakumanu@gmail.com
- **Dashboard**: https://mew-app-eastus2.azurewebsites.net/dashboard
- **API Access**: Available at /docs for advanced usage
- **Support**: Direct line to the development team!

### Special Customer Zero Features:
- ✨ Early access to all new features
- ✨ Priority support
- ✨ Influence product direction
- ✨ Free premium features for life
- ✨ Your feedback shapes Mew for everyone

Thank you for being the first! 🙏
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
