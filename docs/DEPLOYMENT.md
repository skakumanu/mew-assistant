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
