#!/bin/bash

# Mew Assistant - Azure Deployment Script
# This script deploys the complete Mew Assistant infrastructure to Azure

set -e

echo "🚀 Starting Mew Assistant Azure Deployment..."

# Configuration
RESOURCE_GROUP="mew-assistant-rg"
LOCATION="eastus"
APP_NAME="mew-assistant"
UNIQUE_SUFFIX=$(date +%s | tail -c 5)

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  App Name: $APP_NAME-$UNIQUE_SUFFIX"

# Create Resource Group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy infrastructure using Bicep
echo "🏗️  Deploying infrastructure..."
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file main.bicep \
  --parameters appName=$APP_NAME uniqueSuffix=$UNIQUE_SUFFIX

# Get deployment outputs
echo "📤 Getting deployment outputs..."
WEBAPP_NAME=$(az deployment group show -g $RESOURCE_GROUP -n main --query properties.outputs.webAppName.value -o tsv)
DB_HOST=$(az deployment group show -g $RESOURCE_GROUP -n main --query properties.outputs.dbHost.value -o tsv)
VAULT_NAME=$(az deployment group show -g $RESOURCE_GROUP -n main --query properties.outputs.keyVaultName.value -o tsv)

echo "✅ Infrastructure deployed successfully!"
echo ""
echo "📝 Deployment Details:"
echo "  Web App: https://$WEBAPP_NAME.azurewebsites.net"
echo "  Database Host: $DB_HOST"
echo "  Key Vault: $VAULT_NAME"
echo ""
echo "🔑 Next steps:"
echo "  1. Set up your secrets in Key Vault: $VAULT_NAME"
echo "  2. Deploy your application code"
echo "  3. Configure custom domain (optional)"
echo ""
echo "💰 Estimated monthly cost: ~\$30-50 USD"
