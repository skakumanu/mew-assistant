#!/bin/bash

# Mew Assistant - Minimal Azure Deployment (Container + PostgreSQL)
# Uses Azure Container Instances and minimal services

set -e

echo "🚀 Starting Minimal Mew Assistant Deployment..."

# Configuration
RESOURCE_GROUP="mew-assistant-rg"
LOCATION="westus2" # Changed location
APP_NAME="mew-assistant"
UNIQUE_SUFFIX=$(date +%s | tail -c 5)

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  App Name: $APP_NAME-$UNIQUE_SUFFIX"

# Check if resource group exists, if not create it
if [ $(az group exists --name $RESOURCE_GROUP) = false ]; then
    echo "📦 Creating resource group..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
else
    echo "📦 Resource group already exists"
fi

# Deploy minimal infrastructure
echo "🏗️  Deploying minimal infrastructure..."
echo "Note: This deployment uses pay-as-you-go pricing (no free tier available)"
echo "Estimated cost: ~\$30-50/month"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Deployment cancelled."
    exit 1
fi

# Create PostgreSQL server using minimal SKU
echo "🗄️  Creating PostgreSQL server..."
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME="mewassistant${UNIQUE_SUFFIX}db"

az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_NAME \
  --location $LOCATION \
  --admin-user mewadmin \
  --admin-password "$DB_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0 \
  --yes

# Create database
echo "📊 Creating database..."
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_NAME \
  --database-name mewassistant

# Get connection string
DB_HOST=$(az postgres flexible-server show \
  --resource-group $RESOURCE_GROUP \
  --name $DB_NAME \
  --query fullyQualifiedDomainName \
  -o tsv)

echo "✅ Deployment completed successfully!"
echo ""
echo "📝 Connection Details:"
echo "  Database Host: $DB_HOST"
echo "  Database Name: mewassistant"
echo "  Admin User: mewadmin"
echo "  Admin Password: $DB_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Save these credentials securely!"
echo ""
echo "🔑 Connection String:"
echo "postgresql://mewadmin:$DB_PASSWORD@$DB_HOST/mewassistant?sslmode=require"
echo ""
echo "📦 Next Steps:"
echo "1. Save the database password in a secure location"
echo "2. Update your .env file with the connection string"
echo "3. Run 'podman-compose up' to start the application locally"
echo "4. The app will connect to Azure PostgreSQL"
echo ""
echo "💰 Estimated Monthly Cost: ~\$12-15 USD (PostgreSQL only)"
