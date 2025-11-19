#!/bin/bash
# Azure Deployment Script for Mew Assistant
# Usage: ./deploy-azure.sh [environment]
# Example: ./deploy-azure.sh dev

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
RESOURCE_GROUP="mew-assistant-${ENVIRONMENT}-rg"
LOCATION="eastus"
APP_NAME="mew-assistant-${ENVIRONMENT}"
ACR_NAME="mewassistant${ENVIRONMENT}acr"
DB_NAME="mew-db-${ENVIRONMENT}"
CONTAINER_ENV="mew-env-${ENVIRONMENT}"

echo -e "${GREEN}Starting Azure Deployment for Mew Assistant${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${RED}Not logged in to Azure. Running 'az login'...${NC}"
    az login
fi

echo -e "${GREEN}✓ Azure CLI ready${NC}"

# Show current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${YELLOW}Current subscription: ${SUBSCRIPTION}${NC}"
read -p "Continue with this subscription? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please set the correct subscription with: az account set --subscription <subscription-id>"
    exit 1
fi

# Generate secure passwords
echo -e "${YELLOW}Generating secure credentials...${NC}"
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Create resource group
echo -e "${GREEN}Creating resource group...${NC}"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

# Create Container Registry
echo -e "${GREEN}Creating Azure Container Registry...${NC}"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true \
  --output table

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Build and push Docker image
echo -e "${GREEN}Building and pushing Docker image...${NC}"
az acr build \
  --registry $ACR_NAME \
  --image mew-assistant:latest \
  --image mew-assistant:$(git rev-parse --short HEAD) \
  --file Dockerfile \
  .

# Create PostgreSQL Flexible Server
echo -e "${GREEN}Creating PostgreSQL database...${NC}"
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_NAME \
  --location $LOCATION \
  --admin-user mewadmin \
  --admin-password "$DB_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 14 \
  --public-access 0.0.0.0 \
  --output table

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_NAME \
  --database-name mew_assistant

# Get database connection string
DB_HOST="${DB_NAME}.postgres.database.azure.com"
DB_CONNECTION_STRING="postgresql://mewadmin:${DB_PASSWORD}@${DB_HOST}:5432/mew_assistant?sslmode=require"

# Create Key Vault
echo -e "${GREEN}Creating Azure Key Vault...${NC}"
VAULT_NAME="mew-vault-${ENVIRONMENT}"
az keyvault create \
  --name $VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

# Store secrets in Key Vault
echo -e "${GREEN}Storing secrets in Key Vault...${NC}"
az keyvault secret set --vault-name $VAULT_NAME --name "DATABASE-URL" --value "$DB_CONNECTION_STRING"
az keyvault secret set --vault-name $VAULT_NAME --name "SECRET-KEY" --value "$SECRET_KEY"
az keyvault secret set --vault-name $VAULT_NAME --name "JWT-SECRET-KEY" --value "$JWT_SECRET"

# Create Container App Environment
echo -e "${GREEN}Creating Container App Environment...${NC}"
az containerapp env create \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

# Deploy Container App
echo -e "${GREEN}Deploying Container App...${NC}"
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image ${ACR_NAME}.azurecr.io/mew-assistant:latest \
  --target-port 8888 \
  --ingress external \
  --registry-server ${ACR_NAME}.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 0 \
  --max-replicas 3 \
  --secrets \
    database-url="$DB_CONNECTION_STRING" \
    secret-key="$SECRET_KEY" \
    jwt-secret="$JWT_SECRET" \
  --env-vars \
    DATABASE_URL=secretref:database-url \
    SECRET_KEY=secretref:secret-key \
    JWT_SECRET_KEY=secretref:jwt-secret \
    AZURE_KEY_VAULT_URL="https://${VAULT_NAME}.vault.azure.net/" \
  --output table

# Get the app URL
APP_URL=$(az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  -o tsv)

# Save deployment credentials
CRED_FILE="deployment-credentials-${ENVIRONMENT}.txt"
cat > $CRED_FILE <<EOF
Mew Assistant Deployment Credentials
=====================================
Environment: ${ENVIRONMENT}
Deployed: $(date)

Application URL: https://${APP_URL}
API Docs: https://${APP_URL}/docs

Database:
  Host: ${DB_HOST}
  Database: mew_assistant
  Username: mewadmin
  Password: ${DB_PASSWORD}

Azure Key Vault: ${VAULT_NAME}

Container Registry:
  Server: ${ACR_NAME}.azurecr.io
  Username: ${ACR_USERNAME}
  
Resource Group: ${RESOURCE_GROUP}
Location: ${LOCATION}

IMPORTANT: Store these credentials securely and delete this file!
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Application URL: ${GREEN}https://${APP_URL}${NC}"
echo -e "API Documentation: ${GREEN}https://${APP_URL}/docs${NC}"
echo ""
echo -e "${YELLOW}Credentials saved to: ${CRED_FILE}${NC}"
echo -e "${RED}IMPORTANT: Store credentials securely and delete the file!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the application at https://${APP_URL}/docs"
echo "2. Register your first user"
echo "3. Configure monitoring and alerts"
echo "4. Set up automated backups"
echo ""
echo -e "${GREEN}Happy scheduling!${NC}"
