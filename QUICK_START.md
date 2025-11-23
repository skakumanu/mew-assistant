# Mew Assistant - Quick Start Guide

## 🚀 Your App is Live!

**Production URL**: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io

## 📱 Access Points

### 1. Web Interface
- **API Docs**: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/docs
- **ReDoc**: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/redoc

### 2. Voice Assistants
- **Alexa**: "Alexa, ask Mew to schedule therapy"
- **Siri**: "Hey Siri, schedule with Mew"
- **Google**: "Hey Google, talk to Mew Assistant"

### 3. Messaging
- **Email**: Send to your configured email
- **SMS**: Text your scheduled number
- **WhatsApp**: Message your WhatsApp Business number

## 🔑 Quick Test

### 1. Register an Account
```bash
curl -X POST https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourSecurePassword123!",
    "full_name": "Your Name",
    "role": "parent"
  }'
```

### 2. Login
```bash
curl -X POST https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourSecurePassword123!"
  }'
```

### 3. Test Voice Command
```bash
TOKEN="your_jwt_token_here"

curl -X POST https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/voice/generic \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule therapy for tomorrow at 3pm",
    "language": "en"
  }'
```

## �� Common Tasks

### Schedule an Event
Use voice or text:
- "Schedule therapy tomorrow at 3pm"
- "Add dentist appointment next Tuesday 10am"
- "Create pickup reminder for 2:30pm today"

### Check Schedule
- "What's on my schedule today?"
- "Show me tomorrow's appointments"
- "List this week's events"

### Get Summary
- "Give me a daily summary"
- "What did I miss?"
- "Summarize today's activities"

## 💡 Features Ready to Use

✅ Multi-language voice commands (100+ languages)  
✅ Smart scheduling with conflict detection  
✅ Calendar integration (Google, Apple)  
✅ SMS/Email/WhatsApp ingestion  
✅ Mobile push notifications  
✅ AI-powered suggestions  
✅ Parental approval workflow  
✅ Kid-friendly interface  

## 📊 Monitor Your App

### Azure Portal
1. Go to: https://portal.azure.com
2. Navigate to: Resource Groups → mew-assistant-dev-rg
3. Check: Container App health, logs, metrics

### View Logs
```bash
az containerapp logs show \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --follow
```

### Check Health
```bash
curl https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/
```

## 🔒 Security Notes

- JWT tokens expire in 30 minutes
- Use HTTPS for all requests
- Secrets stored in Azure Key Vault
- Database encrypted at rest
- Rate limiting enabled

## 💰 Current Costs

Estimated: **$45-75/month**
- Monitor via Azure Cost Management
- Auto-scaling enabled (0-2 instances)
- Scales down when not in use

## 🆘 Troubleshooting

### App Not Responding
```bash
az containerapp revision restart \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --revision $(az containerapp revision list \
    --name mew-assistant-dev \
    --resource-group mew-assistant-dev-rg \
    --query "[0].name" -o tsv)
```

### View Error Logs
```bash
az containerapp logs show \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --tail 100
```

### Redeploy Latest Version
```bash
./deploy-azure.sh
```

## 📞 Next Steps

1. **Test the app** - Try all features
2. **Invite users** - Share with family/testers
3. **Setup voice** - Configure Alexa/Siri/Google
4. **Connect calendars** - Link Google/Apple calendars
5. **Configure mobile** - Setup push notifications

## 🎉 You're All Set!

Your Mew Assistant is:
- ✅ Deployed to production
- ✅ Secure and compliant
- ✅ Ready for real users
- ✅ Cost-optimized
- ✅ Fully documented

**Have fun and make life easier for special needs families!** 🌟

---

**Need Help?**
- Documentation: `/docs/` folder
- Issues: https://github.com/skakumanu/mew-assistant/issues
- Live App: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
