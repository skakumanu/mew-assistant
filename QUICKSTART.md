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
