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
