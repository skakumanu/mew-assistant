#!/bin/bash
# Finish Azure Container App Deployment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
RESOURCE_GROUP="mew-assistant-dev-rg"
LOCATION="westus2"
APP_NAME="mew-assistant-dev"
ACR_NAME="mewassistantdevacr"
CONTAINER_ENV="mew-env-dev"
DB_SERVER="mew-db-dev"

echo -e "${GREEN}Finishing Azure Container App deployment...${NC}"

# Get ACR credentials
echo -e "${YELLOW}Getting ACR credentials...${NC}"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Get DB connection string
echo -e "${YELLOW}Getting database info...${NC}"
DB_HOST=$(az postgres flexible-server show --resource-group $RESOURCE_GROUP --name $DB_SERVER --query fullyQualifiedDomainName -o tsv)

# Generate secure credentials
JWT_SECRET=$(openssl rand -base64 32)
DB_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)

# Create Container Apps environment if not exists
echo -e "${YELLOW}Creating Container Apps environment...${NC}"
az containerapp env create \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --only-show-errors || echo "Environment may already exist"

# Deploy Container App
echo -e "${YELLOW}Deploying Container App...${NC}"
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image "${ACR_NAME}.azurecr.io/mew-assistant:latest" \
  --registry-server "${ACR_NAME}.azurecr.io" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 2 \
  --cpu 0.5 \
  --memory 1Gi \
  --env-vars \
    "DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@${DB_HOST}:5432/mew_db" \
    "JWT_SECRET_KEY=${JWT_SECRET}" \
    "ENVIRONMENT=production" \
  --only-show-errors

# Get the app URL
APP_URL=$(az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

# Save credentials
cat > deployment-credentials.txt << EOF
========================================
MEW ASSISTANT - Azure Deployment Details
========================================

Application URL: https://${APP_URL}
API Documentation: https://${APP_URL}/docs

Database:
---------
Host: ${DB_HOST}
Database: mew_db
Username: postgres
Password: ${DB_PASSWORD}

Container Registry:
-------------------
Server: ${ACR_NAME}.azurecr.io
Username: ${ACR_USERNAME}
Password: ${ACR_PASSWORD}

Application Secrets:
--------------------
JWT Secret: ${JWT_SECRET}

Resource Group: ${RESOURCE_GROUP}
Location: ${LOCATION}

Next Steps:
-----------
1. Test the API: curl https://${APP_URL}/health
2. Register a user: See README.md for examples
3. Monitor logs: az containerapp logs tail --name ${APP_NAME} --resource-group ${RESOURCE_GROUP}

IMPORTANT: Store these credentials securely!
========================================
EOF

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${YELLOW}App URL: https://${APP_URL}${NC}"
echo -e "${YELLOW}Credentials saved to: deployment-credentials.txt${NC}"
echo -e "${RED}IMPORTANT: Store deployment-credentials.txt securely and delete from disk!${NC}"
