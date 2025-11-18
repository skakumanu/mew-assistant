# 🚀 Quick Start Deployment Guide

## Phase 0: Immediate Deployment (Start Using Today!)

**Goal**: Get Mew Assistant running in Azure within 2-4 hours for ~$15-25/month

### Prerequisites Checklist
- [ ] Azure account (free tier available)
- [ ] Azure CLI installed
- [ ] GitHub account connected
- [ ] Phone number for SMS testing
- [ ] Email account for testing

---

## Option A: Azure Free Tier (Best for Getting Started)

### Total Cost: $0-5/month for first 12 months

**What You Get Free:**
- App Service: B1 tier free for 12 months
- PostgreSQL: B1 tier free for 12 months  
- 5GB storage
- 750 hours/month compute

### Quick Deploy Steps

#### 1. Install Azure CLI (if not already installed)
```bash
# On Linux/WSL
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verify installation
az --version
```

#### 2. Login to Azure
```bash
az login
```

#### 3. Run Automated Setup Script
```bash
# This script will:
# - Create resource group
# - Deploy PostgreSQL database
# - Deploy App Service
# - Configure environment variables
# - Deploy the application

./infrastructure/azure/quick-deploy.sh
```

#### 4. Configure Your Environment
After deployment, the script will output your app URL. Update these settings:

```bash
# Set your personal info
az webapp config appsettings set \
  --resource-group mew-assistant-rg \
  --name mew-assistant-app \
  --settings \
    SMTP_HOST="smtp.gmail.com" \
    SMTP_USER="your-email@gmail.com" \
    SMTP_PASSWORD="your-app-password" \
    TWILIO_PHONE_NUMBER="your-twilio-number"
```

---

## Option B: Pay-As-You-Go (Most Economical Long-Term)

### Total Cost: ~$15-25/month

**Services & Costs:**
- App Service (B1): ~$13/month
- PostgreSQL (B1): ~$5/month
- Blob Storage: ~$1/month
- Bandwidth: ~$1/month
- Key Vault: $0.03/month
- **Total: ~$20/month**

### Deploy with Terraform

```bash
cd infrastructure/azure/terraform

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy (takes 5-10 minutes)
terraform apply

# Get your app URL
terraform output app_url
```

---

## Option C: Container-Based (Most Flexible)

### Total Cost: ~$25-35/month

```bash
# Build and push to Azure Container Registry
az acr create --resource-group mew-assistant-rg \
  --name mewassistantacr --sku Basic

az acr build --registry mewassistantacr \
  --image mew-assistant:latest .

# Deploy to Container Instances
az container create \
  --resource-group mew-assistant-rg \
  --name mew-assistant \
  --image mewassistantacr.azurecr.io/mew-assistant:latest \
  --dns-name-label mew-assistant \
  --ports 8000
```

---

## Post-Deployment Setup (15 minutes)

### 1. Create Your Admin Account
```bash
curl -X POST https://your-app.azurewebsites.net/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "YourSecurePassword123!",
    "full_name": "Your Name",
    "role": "parent"
  }'
```

### 2. Set Up Voice Assistant Integration

**For Siri/iOS:**
1. Open Shortcuts app
2. Create new shortcut: "Talk to Mew"
3. Add action: "Get contents of URL"
4. URL: `https://your-app.azurewebsites.net/voice/webhook`
5. Method: POST
6. Request Body: Ask Siri

**For Alexa:**
```bash
# Deploy Alexa skill (automated)
./scripts/deploy-alexa-skill.sh
```

### 3. Configure Calendar Integration

```bash
# Google Calendar
curl -X POST https://your-app.azurewebsites.net/integrations/calendar/google/setup \
  -H "Authorization: Bearer YOUR_TOKEN"

# Follow OAuth flow in browser
```

### 4. Test Your Setup

```bash
# Send test message
curl -X POST https://your-app.azurewebsites.net/mew/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms",
    "from": "+1234567890",
    "content": "Schedule dentist appointment for Tommy next Tuesday at 2pm"
  }'

# Check response
curl https://your-app.azurewebsites.net/mew/summary
```

---

## Scaling Options (As You Grow)

### When You Hit 100 Users (~$50/month)
```bash
# Upgrade to S1 tier
az appservice plan update \
  --name mew-assistant-plan \
  --resource-group mew-assistant-rg \
  --sku S1
```

### When You Hit 1,000 Users (~$200/month)
- Move to Azure Kubernetes Service (AKS)
- Add Azure Cache for Redis
- Use Azure Front Door for CDN

### When You Hit 10,000 Users (~$1,000/month)
- Multi-region deployment
- Azure Cosmos DB for global distribution
- Azure Cognitive Services at scale

---

## Cost Monitoring

### Set Up Budget Alerts
```bash
az consumption budget create \
  --budget-name mew-assistant-budget \
  --amount 30 \
  --time-grain Monthly \
  --start-date 2024-01-01 \
  --end-date 2025-12-31
```

### View Current Costs
```bash
# Check daily costs
az consumption usage list \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)
```

---

## Troubleshooting

### App won't start?
```bash
# Check logs
az webapp log tail \
  --resource-group mew-assistant-rg \
  --name mew-assistant-app

# Restart app
az webapp restart \
  --resource-group mew-assistant-rg \
  --name mew-assistant-app
```

### Database connection issues?
```bash
# Test database connection
az postgres flexible-server connect \
  --name mew-assistant-db \
  --admin-user mewadmin
```

### Out of memory?
```bash
# Scale up temporarily
az webapp config set \
  --resource-group mew-assistant-rg \
  --name mew-assistant-app \
  --always-on true \
  --http20-enabled true
```

---

## Backup & Recovery

### Automated Backups (Already Configured)
- Database: Daily backups, 7-day retention
- App Config: Stored in Key Vault
- User Data: Encrypted in PostgreSQL

### Manual Backup
```bash
# Backup database
az postgres flexible-server backup create \
  --name mew-assistant-db \
  --resource-group mew-assistant-rg \
  --backup-name manual-backup-$(date +%Y%m%d)
```

---

## Security Checklist

- [ ] Enable Azure AD authentication
- [ ] Rotate all secrets in Key Vault
- [ ] Enable SSL/TLS only
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up Azure Security Center

---

## Next Steps

1. **Week 1**: Use it yourself, gather feedback
2. **Week 2**: Invite 2-3 trusted families to test
3. **Week 3**: Refine based on feedback
4. **Month 2**: Soft launch to 10-20 families
5. **Month 3**: Public beta launch

**Support**: Issues? Check `/docs/TROUBLESHOOTING.md` or open a GitHub issue.

**Cost Questions**: See `/docs/COST_OPTIMIZATION.md` for detailed breakdown.
