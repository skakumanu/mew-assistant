# Integration Setup Guide

Complete guide for configuring external service integrations with Mew Assistant.

## Table of Contents

1. [Email (Gmail/SMTP)](#email-setup)
2. [SMS (Twilio)](#sms-setup)
3. [WhatsApp (Twilio)](#whatsapp-setup)
4. [AI (OpenAI/Anthropic)](#ai-setup)
5. [Calendar (Google)](#calendar-setup)
6. [Testing](#testing)

---

## Email Setup

### Gmail Configuration

1. **Enable 2-Factor Authentication**
   - Go to Google Account → Security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Visit: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)"
   - Name it: "Mew Assistant"
   - Copy the generated 16-character password

3. **Configure .env**
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password-here
   
   IMAP_SERVER=imap.gmail.com
   IMAP_PORT=993
   IMAP_USER=your-email@gmail.com
   IMAP_PASSWORD=your-app-password-here
   ```

---

## SMS Setup

### Twilio Configuration

1. **Create Twilio Account**
   - Sign up at https://www.twilio.com/try-twilio
   - Verify your email and phone number

2. **Get Credentials**
   - Go to Console Dashboard
   - Copy Account SID and Auth Token

3. **Get Phone Number**
   - Navigate to Phone Numbers → Manage → Buy a number
   - Choose a number with SMS capability
   - Purchase the number

4. **Configure Webhook**
   - Go to Phone Numbers → Active Numbers
   - Click your number
   - Scroll to "Messaging"
   - Configure webhook:
     - URL: `https://your-domain.com/webhooks/sms/incoming`
     - HTTP Method: POST

5. **Update .env**
   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your-auth-token-here
   TWILIO_PHONE_NUMBER=+15551234567
   ```

---

## WhatsApp Setup

### Twilio WhatsApp Configuration

1. **Enable WhatsApp**
   - In Twilio Console → Messaging → Try it out → Try WhatsApp
   - Follow the sandbox setup instructions
   - Save the sandbox number

2. **Configure Webhook**
   - Go to Programmable Messaging → Settings → WhatsApp Sandbox Settings
   - Set webhook URL: `https://your-domain.com/webhooks/whatsapp/incoming`
   - HTTP Method: POST

3. **Update .env**
   ```bash
   TWILIO_WHATSAPP_NUMBER=+14155238886
   ```

4. **Testing (Sandbox Mode)**
   - Send "join <your-sandbox-code>" to the Twilio WhatsApp number
   - You'll receive a confirmation message
   - Now you can send/receive test messages

---

## AI Setup

### OpenAI Configuration

1. **Create Account**
   - Sign up at https://platform.openai.com/signup

2. **Generate API Key**
   - Go to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Name it: "Mew Assistant"
   - Copy the key (shown only once!)

3. **Add Credits**
   - Go to Billing → Add payment method
   - Add initial credits ($5-10 recommended for testing)

4. **Update .env**
   ```bash
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxx
   AI_MODEL=gpt-4
   ```

### Anthropic Configuration

1. **Create Account**
   - Sign up at https://console.anthropic.com/

2. **Generate API Key**
   - Go to Settings → API Keys
   - Create new key
   - Copy the key

3. **Update .env**
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxx
   AI_MODEL=claude-3-sonnet-20240229
   ```

---

## Calendar Setup

### Google Calendar Configuration

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create new project: "Mew Assistant"

2. **Enable Calendar API**
   - Navigate to APIs & Services → Library
   - Search for "Google Calendar API"
   - Click Enable

3. **Create Service Account**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → Service Account
   - Name: "mew-calendar-service"
   - Grant role: "Editor"
   - Click Done

4. **Generate Key**
   - Click on the created service account
   - Go to Keys tab
   - Add Key → Create new key → JSON
   - Download the JSON file
   - Save as `google-credentials.json` in your project

5. **Share Calendar**
   - Open Google Calendar
   - Settings → Select calendar
   - Share with specific people
   - Add the service account email (from JSON file)
   - Permission: "Make changes to events"

6. **Update .env**
   ```bash
   GOOGLE_CREDENTIALS_FILE=./google-credentials.json
   GOOGLE_CALENDAR_ID=primary
   ```

---

## Testing

### Test All Integrations

```bash
# Run integration tests
./test_integrations.sh
```

### Test Individual Services

**Email:**
```bash
curl -X POST http://localhost:8000/test/email \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test"}'
```

**SMS:**
```bash
curl -X POST http://localhost:8000/test/sms \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Test SMS"}'
```

**WhatsApp:**
```bash
curl -X POST http://localhost:8000/test/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Test WhatsApp"}'
```

### Webhook Testing with ngrok

```bash
# Start ngrok
ngrok http 8000

# Use the ngrok URL for webhooks
# Example: https://abc123.ngrok.io/webhooks/sms/incoming

# Send test SMS to your Twilio number
# Check logs to see webhook received
```

---

## Security Best Practices

1. **Never commit .env file**
   - Already in `.gitignore`
   - Use environment variables in production

2. **Rotate API Keys Regularly**
   - Change keys every 90 days
   - Immediately rotate if compromised

3. **Use Webhook Validation**
   - Verify Twilio request signatures
   - Validate incoming webhook sources

4. **Limit API Key Permissions**
   - Use minimum required scopes
   - Enable IP restrictions where possible

5. **Monitor Usage**
   - Set up billing alerts
   - Track API usage regularly

---

## Troubleshooting

### Common Issues

**Email not sending:**
- Check app password (not regular password)
- Verify SMTP settings
- Check firewall/port 587

**SMS webhook not receiving:**
- Verify webhook URL is publicly accessible
- Check Twilio webhook logs
- Ensure URL uses HTTPS (not HTTP)

**AI responses failing:**
- Check API key validity
- Verify billing/credits
- Review rate limits

**Calendar events not creating:**
- Verify service account email is shared
- Check JSON credentials file path
- Ensure Calendar API is enabled

For more help, see the main README.md or open an issue on GitHub.
