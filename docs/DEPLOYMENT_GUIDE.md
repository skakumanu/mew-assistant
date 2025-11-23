# Mew Assistant - Azure Deployment Guide

## Current Situation

Your Azure subscription has **0 quota for App Services**. You have two options:

### Option 1: Request Azure Quota Increase (Recommended for Cloud Deployment)

1. Go to Azure Portal: https://portal.azure.com
2. Search for "Quotas" in the top search bar
3. Select "App Service"
4. Click "+ New Quota Request"
5. Request:
   - **Basic App Service Plan**: 1 instance minimum
   - **Region**: East US (or your preferred region)
   - **Reason**: "Running Mew Assistant - a FastAPI application for special needs family scheduling"

**Processing time**: Usually 1-3 business days for small quota increases.

### Option 2: Deploy Locally with Podman (Available NOW - $0/month)

You can start using Mew Assistant immediately on your local machine:

```bash
# Start the app with PostgreSQL
./podman-start.sh

# Access the app at:
# http://localhost:8000
# API docs: http://localhost:8000/docs
```

**Advantages**:
- ✅ Start using immediately
- ✅ No Azure costs
- ✅ Full control over data
- ✅ Can migrate to cloud later

**Disadvantages**:
- ⚠️ Only accessible from your computer
- ⚠️ Requires your computer to be running
- ⚠️ No automatic backups (you manage manually)

## Cost Comparison

### Local Deployment (Podman)
- **Cost**: $0/month
- **Setup time**: 5 minutes
- **Access**: Local only

### Azure Basic Tier (When quota approved)
- **Cost**: ~$13-15/month
  - App Service Basic B1: ~$13/month
  - Storage Account: ~$0.02/month
  - Optional PostgreSQL: ~$15/month (can use SQLite initially)
- **Setup time**: 30 minutes
- **Access**: Internet-accessible

### Azure Container Instances (When quota approved)
- **Cost**: ~$10-15/month (pay only when running)
  - Container: ~$0.014/hour = ~$10/month
  - Storage: ~$1/month
- **Setup time**: 20 minutes
- **Access**: Internet-accessible

## Recommended Deployment Path

### Phase 1: Start Now (Week 1)
```bash
# Deploy locally with Podman
./podman-start.sh

# Start using the app for your family
# Test features, provide feedback, iterate
```

### Phase 2: Request Azure Quota (Week 1)
1. Request Basic App Service quota in Azure Portal
2. Continue using local deployment
3. Document any issues or feature requests

### Phase 3: Deploy to Azure (Week 2-3, after quota approved)
```bash
# Once quota is approved, deploy to Azure
az deployment group create \
  --resource-group mew-assistant-rg \
  --template-file main-simple.bicep \
  --parameters appName=mew-assistant location=eastus
```

### Phase 4: Transition to Non-Profit (Month 3-6)
Once the app is stable and useful:
1. Form non-profit organization
2. Apply for Azure credits ($3,500/year for non-profits)
3. Transfer repository
4. Invite contributors

## Quick Start Guide (Local Deployment)

### 1. Install Prerequisites
```bash
# Already installed: Podman, Python 3.11+, PostgreSQL client
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferences
nano .env
```

### 3. Start the Application
```bash
# Start all services (API + Database)
./podman-start.sh

# Verify it's running
curl http://localhost:8000/health

# Open API documentation
# Visit: http://localhost:8000/docs
```

### 4. Create Your First User
```bash
# Use the API to register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-secure-password",
    "full_name": "Your Name",
    "role": "parent"
  }'
```

### 5. Start Scheduling!
Visit http://localhost:8000/docs and explore:
- `/api/v1/sessions` - Create chat sessions
- `/api/v1/messages` - Send messages to Mew
- `/api/v1/confirm` - Confirm scheduling changes
- `/api/v1/summary` - Get daily summaries

## Mobile Access (While Running Locally)

### Option A: Local Network Access
```bash
# Find your local IP
ip addr show | grep "inet " | grep -v 127.0.0.1

# Update .env to bind to all interfaces
# Then access from phone: http://192.168.x.x:8000
```

### Option B: Tailscale (Recommended)
```bash
# Install Tailscale for secure remote access
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Access from anywhere on your Tailscale network
# https://tailscale-hostname:8000
```

## Backup Strategy (Local Deployment)

### Automatic Backups
```bash
# Add to crontab for daily backups
crontab -e

# Add this line for daily 2 AM backups:
0 2 * * * /home/srinu/mew-assistant/scripts/backup-database.sh
```

### Manual Backup
```bash
# Backup database
./scripts/backup-database.sh

# Backups stored in: ./backups/
```

## Monitoring

### View Logs
```bash
# API logs
podman logs mew-assistant-api

# Database logs
podman logs mew-assistant-db

# Follow logs in real-time
podman logs -f mew-assistant-api
```

### Health Checks
```bash
# Check if services are running
./podman-stop.sh --status

# Check API health
curl http://localhost:8000/health
```

## Troubleshooting

### Port Already in Use
```bash
# Stop existing containers
./podman-stop.sh

# Check what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

### Database Connection Issues
```bash
# Restart database container
podman restart mew-assistant-db

# Check database logs
podman logs mew-assistant-db
```

### Reset Everything
```bash
# Stop and remove all containers
./podman-stop.sh

# Remove volumes (WARNING: deletes data)
podman volume rm mew-postgres-data

# Start fresh
./podman-start.sh
```

## Next Steps

1. **Start using locally** - Begin testing with your family
2. **Request Azure quota** - Submit quota increase request today
3. **Document feedback** - Note features that work well and need improvement
4. **Plan migration** - Once quota approved, we'll deploy to Azure
5. **Build community** - Share with other special needs families

## Support

- GitHub Issues: https://github.com/skakumanu/mew-assistant/issues
- Email: (add your email)
- Discord: (create if community grows)

---

**Current Status**: ✅ Ready for local deployment
**Next Milestone**: Azure quota approval for cloud deployment
**Estimated Timeline**: Cloud-ready in 1-3 business days
# Quick Azure Deployment Guide

## Prerequisites
- Azure CLI installed and logged in (`az login`)
- Docker/Podman installed (for local testing)
- Git repository access

## One-Command Deployment

```bash
./deploy-azure.sh dev
```

This will:
1. Create all Azure resources
2. Build and push Docker image
3. Deploy the application
4. Set up PostgreSQL database
5. Configure Key Vault for secrets
6. Generate secure credentials

## What Gets Created

### Resources
- **Resource Group**: mew-assistant-dev-rg
- **Container Registry**: mewassistantdevacr
- **PostgreSQL Server**: mew-db-dev
- **Container App**: mew-assistant-dev
- **Key Vault**: mew-vault-dev

### Estimated Monthly Cost
- **Development**: ~$20-30/month
- **Production**: ~$50-100/month (with scaling)

## Manual Deployment (Step by Step)

If you prefer manual control:

### 1. Create Resource Group
```bash
az group create --name mew-assistant-rg --location eastus
```

### 2. Create Container Registry
```bash
az acr create --resource-group mew-assistant-rg \
  --name mewassistantacr --sku Basic --admin-enabled true
```

### 3. Build and Push Image
```bash
az acr build --registry mewassistantacr \
  --image mew-assistant:latest .
```

### 4. Create PostgreSQL Database
```bash
az postgres flexible-server create \
  --resource-group mew-assistant-rg \
  --name mew-db \
  --location eastus \
  --admin-user mewadmin \
  --admin-password <YOUR_SECURE_PASSWORD> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 14 \
  --public-access 0.0.0.0
```

### 5. Create Container App Environment
```bash
az containerapp env create \
  --name mew-env \
  --resource-group mew-assistant-rg \
  --location eastus
```

### 6. Deploy Application
```bash
az containerapp create \
  --name mew-assistant \
  --resource-group mew-assistant-rg \
  --environment mew-env \
  --image mewassistantacr.azurecr.io/mew-assistant:latest \
  --target-port 8888 \
  --ingress external \
  --registry-server mewassistantacr.azurecr.io \
  --env-vars DATABASE_URL=<connection_string>
```

## Post-Deployment

### 1. Test the Application
```bash
curl https://<your-app-url>/health
```

### 2. Access API Documentation
Visit: `https://<your-app-url>/docs`

### 3. Register First User
```bash
curl -X POST https://<your-app-url>/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "secure_password",
    "full_name": "Your Name",
    "role": "parent"
  }'
```

### 4. Test Authentication
```bash
curl -X POST https://<your-app-url>/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "secure_password"
  }'
```

## Monitoring & Management

### View Logs
```bash
az containerapp logs show \
  --name mew-assistant \
  --resource-group mew-assistant-rg \
  --follow
```

### Scale Application
```bash
az containerapp update \
  --name mew-assistant \
  --resource-group mew-assistant-rg \
  --min-replicas 1 \
  --max-replicas 5
```

### Update Application
```bash
# Build new image
az acr build --registry mewassistantacr \
  --image mew-assistant:v2 .

# Update container app
az containerapp update \
  --name mew-assistant \
  --resource-group mew-assistant-rg \
  --image mewassistantacr.azurecr.io/mew-assistant:v2
```

## Troubleshooting

### Check Application Status
```bash
az containerapp show \
  --name mew-assistant \
  --resource-group mew-assistant-rg \
  --query properties.runningStatus
```

### View Recent Revisions
```bash
az containerapp revision list \
  --name mew-assistant \
  --resource-group mew-assistant-rg \
  --output table
```

### Connect to Database
```bash
psql "postgresql://mewadmin:<password>@mew-db.postgres.database.azure.com:5432/mew_assistant?sslmode=require"
```

## Security Best Practices

1. **Never commit credentials** - Use Azure Key Vault
2. **Enable firewall rules** - Restrict database access
3. **Use managed identities** - For Azure service authentication
4. **Enable Application Insights** - For monitoring
5. **Set up alerts** - For unusual activity
6. **Regular backups** - Configure automated backups

## Cost Optimization

### For Development
- Use Burstable tier for PostgreSQL
- Scale to zero when not in use
- Use Basic SKU for Container Registry

### For Production
- Use Standard tier for PostgreSQL
- Enable auto-scaling
- Implement caching with Redis
- Use Azure CDN for static content

## Cleanup (Remove All Resources)

```bash
az group delete --name mew-assistant-rg --yes --no-wait
```

## Support

For issues:
1. Check application logs
2. Review Azure Portal metrics
3. Open GitHub issue
4. Check documentation

## Next Steps

After deployment:
1. Configure custom domain
2. Set up SSL certificate
3. Enable Application Insights
4. Configure CI/CD pipeline
5. Set up automated backups
6. Add monitoring alerts

## Useful Commands

```bash
# Check resource costs
az consumption usage list --resource-group mew-assistant-rg

# List all resources
az resource list --resource-group mew-assistant-rg --output table

# Export resource configuration
az group export --name mew-assistant-rg > resources.json

# Set up auto-shutdown (for dev)
az containerapp update --name mew-assistant \
  --resource-group mew-assistant-rg \
  --min-replicas 0
```
# Mew Assistant - Deployment Summary

## ✅ Phase 4B: AI Integration - COMPLETED

### What Was Built
1. **AI Service** (`app/services/ai_service.py`)
   - Conflict detection (time overlap, insufficient break, travel time)
   - Smart time slot suggestions with pattern learning
   - Schedule optimization by location and time
   - Historical pattern analysis and prediction

2. **Comprehensive Test Suite** (`tests/test_ai_integration.py`)
   - 13 tests covering all AI features
   - 100% pass rate
   - 90% code coverage for AI service

3. **Schema Updates**
   - Added `ScheduleCreate` for AI operations
   - Updated `ScheduleConflict` and `ScheduleSuggestion` for compatibility

### Test Results
```
✓ 13 passed, 26 warnings in 1.43s
✓ 90% code coverage for AI service
✓ All conflict detection scenarios working
✓ Pattern learning operational
✓ End-to-end integration tests passing
```

## 🚀 Phase 4C: Azure Deployment - IN PROGRESS

### Prerequisites
- ✅ Azure CLI installed and logged in
- ✅ Azure subscription selected
- ✅ Git repository ready

### Deployment Options

#### Option 1: Azure Container Apps (Recommended - Most Economical)
**Monthly Cost: ~$15-30**

**Benefits:**
- Serverless, scales to zero
- Built-in HTTPS
- Auto-scaling
- Managed certificates

**Steps:**
```bash
# 1. Set variables
RESOURCE_GROUP="mew-assistant-rg"
LOCATION="eastus"
APP_NAME="mew-assistant"

# 2. Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# 3. Create Container Registry
az acr create --resource-group $RESOURCE_GROUP \
  --name mewassistantacr --sku Basic

# 4. Build and push image
az acr build --registry mewassistantacr \
  --image mew-assistant:latest .

# 5. Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name mew-assistant-db \
  --location $LOCATION \
  --admin-user mewadmin \
  --admin-password <SECURE_PASSWORD> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32

# 6. Create Container App Environment
az containerapp env create \
  --name mew-assistant-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 7. Deploy Container App
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment mew-assistant-env \
  --image mewassistantacr.azurecr.io/mew-assistant:latest \
  --target-port 8888 \
  --ingress external \
  --registry-server mewassistantacr.azurecr.io \
  --env-vars \
    DATABASE_URL=<connection_string> \
    SECRET_KEY=<your_secret_key> \
    AZURE_KEY_VAULT_URL=<your_vault_url>
```

#### Option 2: Azure Web App for Containers
**Monthly Cost: ~$55-75**

Better for consistent traffic, includes:
- Always-on capability
- Better monitoring
- Custom domains easier

#### Option 3: Azure Kubernetes Service (AKS)
**Monthly Cost: ~$150+**

Only if you need:
- Complex microservices
- Advanced orchestration
- High availability requirements

### Environment Variables Required

Create `.env` file (DO NOT commit):
```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/mew_assistant

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Azure
AZURE_KEY_VAULT_URL=https://<your-vault>.vault.azure.net/

# AI/ML (Optional)
OPENAI_API_KEY=<your-key-if-using-gpt>

# Integrations (Optional)
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
SENDGRID_API_KEY=<your-key>
```

### Security Checklist
- [ ] Secrets stored in Azure Key Vault
- [ ] Database firewall rules configured
- [ ] HTTPS/TLS enabled
- [ ] Environment variables secured
- [ ] Application Insights enabled
- [ ] Backup policy configured

### Post-Deployment
1. Run database migrations
2. Create admin user
3. Test endpoints
4. Configure monitoring alerts
5. Set up automated backups

## 📊 Cost Optimization Tips

### For Personal Use (You as Customer Zero)
1. **Use Azure Container Apps** - Scales to zero when not used
2. **Burstable PostgreSQL tier** - B1ms is sufficient for dev/personal
3. **Basic Container Registry** - No need for Premium
4. **Start without AI services** - Add Azure OpenAI later if needed
5. **Use Azure Free Credits** - $200 for first 30 days

### Current Estimated Monthly Costs
```
Container App (minimal use):     $5-10
PostgreSQL Flexible (Burstable): $10-15
Container Registry (Basic):      $5
Key Vault:                       $0 (free tier)
Storage:                         $1-2
-------------------------------------------
TOTAL:                          $21-32/month
```

### When Moving to Production
- Scale PostgreSQL to Standard tier
- Add Application Gateway for advanced routing
- Enable Redis cache for sessions
- Add Azure CDN for static content
- Implement Azure Front Door for global distribution

## 🎯 Next Steps

1. **Complete Azure Deployment** ✓ In Progress
2. **Voice Integration** - Implement Siri/Alexa/Grok integration
3. **Mobile Apps** - React Native for iOS/Android
4. **Beta Testing** - Test with your family first
5. **Non-Profit Setup** - Prepare for public release

## 📝 Notes

- All sensitive data checked and removed from repository
- CI/CD pipeline passing with guardrails
- 13/13 AI integration tests passing
- Ready for deployment once Azure resources created

## 🔗 Useful Links

- [Azure Container Apps Pricing](https://azure.microsoft.com/pricing/details/container-apps/)
- [PostgreSQL Flexible Server](https://azure.microsoft.com/services/postgresql/)
- [Azure Key Vault](https://azure.microsoft.com/services/key-vault/)
