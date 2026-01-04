# Production Recovery Guide - v1.0.1 Incident

## Incident Summary
- **Date**: January 3, 2026
- **Impact**: Production Container App down (health endpoint timing out)
- **Root Cause**: Hardcoded DATABASE_URL in update-container-probes.ps1 broke database connection
- **Status**: Both revisions showing "Unhealthy" and "Failed"

## Problem
The v1.0.1 deployment script (`update-container-probes.ps1`) hardcoded a PostgreSQL connection string without proper SSL parameters, breaking the database connection. Rollback to previous revision failed because both revisions are now unhealthy.

## Recovery Steps

### 1. Rebuild Container Image (if needed)
```powershell
# From repository root
docker build -t mewassistantacr.azurecr.io/mew-assistant:v1.0.2 .
az acr login --name mewassistantacr
docker push mewassistantacr.azurecr.io/mew-assistant:v1.0.2
```

### 2. Update Container App with Correct Environment Variables
```powershell
# Get proper DATABASE_URL from Azure Key Vault or deployment scripts
# Format: postgresql://mewadmin:{password}@mew-assistant-db.postgres.database.azure.com:5432/mew_assistant?sslmode=require

az containerapp update \
  --name mew-assistant-prod \
  --resource-group mew-assistant-rg \
  --set-env-vars "DATABASE_URL=postgresql://mewadmin:PASSWORD_HERE@mew-assistant-db.postgres.database.azure.com:5432/mew_assistant?sslmode=require" \
  --image mewassistantacr.azurecr.io/mew-assistant:v1.0.2
```

### 3. Add Health Probes (Correctly)
```powershell
# ONLY add probes, do NOT modify DATABASE_URL
# Use the fixed update-container-probes.ps1 from hotfix/v1.0.2
.\update-container-probes.ps1
az containerapp update --name mew-assistant-prod --resource-group mew-assistant-rg --yaml ca-config-updated.json
```

## Prevention
- ✅ Fixed update-container-probes.ps1 to NOT modify DATABASE_URL
- ✅ Added comments explaining the script should only add health probes
- ⚠️  Need to store correct DATABASE_URL in Azure Key Vault for disaster recovery
- ⚠️  Need to document all environment variables in deployment guide

## Git Flow Applied
- Created hotfix/v1.0.2 branch from master
- Fixed update-container-probes.ps1
- Will merge to master and tag v1.0.2 after production recovery confirmed

## Next Steps
1. Recover production service with correct DATABASE_URL
2. Complete hotfix/v1.0.2 merge to master
3. Sync to develop
4. Update deployment documentation with environment variable management
