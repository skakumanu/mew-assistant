#!/bin/bash
set -e

echo "🚀 Mew Assistant - Quick Azure Deployment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="mew-assistant-rg"
LOCATION="eastus"
APP_NAME="mew-assistant-$(openssl rand -hex 4)"
DB_NAME="mew-db-$(openssl rand -hex 4)"
DB_ADMIN="mewadmin"
DB_PASSWORD="$(openssl rand -base64 24)Aa1!"
PLAN_NAME="mew-plan"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  App Name: $APP_NAME"
echo "  Database: $DB_NAME"
echo ""

# Check if user is logged in
echo -e "${BLUE}🔐 Checking Azure CLI login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged in. Please run 'az login' first${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Logged in${NC}"

# Create resource group
echo ""
echo -e "${BLUE}📦 Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION --output none
echo -e "${GREEN}✅ Resource group created${NC}"

# Create PostgreSQL server
echo ""
echo -e "${BLUE}🗄️  Creating PostgreSQL database (this takes 5-10 minutes)...${NC}"
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_NAME \
  --location $LOCATION \
  --admin-user $DB_ADMIN \
  --admin-password "$DB_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 14 \
  --public-access 0.0.0.0 \
  --output none

echo -e "${GREEN}✅ Database created${NC}"

# Create database
echo ""
echo -e "${BLUE}📊 Creating application database...${NC}"
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_NAME \
  --database-name mew_assistant \
  --output none
echo -e "${GREEN}✅ Database created${NC}"

# Create App Service Plan
echo ""
echo -e "${BLUE}⚙️  Creating App Service Plan...${NC}"
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1 \
  --is-linux \
  --output none
echo -e "${GREEN}✅ App Service Plan created${NC}"

# Create Web App
echo ""
echo -e "${BLUE}🌐 Creating Web App...${NC}"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --name $APP_NAME \
  --runtime "PYTHON:3.11" \
  --output none
echo -e "${GREEN}✅ Web App created${NC}"

# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)

# Configure app settings
echo ""
echo -e "${BLUE}⚙️  Configuring environment variables...${NC}"
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    DATABASE_URL="postgresql://$DB_ADMIN:$DB_PASSWORD@$DB_NAME.postgres.database.azure.com/mew_assistant" \
    SECRET_KEY="$SECRET_KEY" \
    JWT_SECRET_KEY="$JWT_SECRET" \
    ENVIRONMENT="production" \
    LOG_LEVEL="INFO" \
    CORS_ORIGINS="*" \
    AZURE_STORAGE_CONNECTION_STRING="" \
    OPENAI_API_KEY="" \
    ANTHROPIC_API_KEY="" \
    SMTP_HOST="" \
    SMTP_PORT="587" \
    SMTP_USER="" \
    SMTP_PASSWORD="" \
    TWILIO_ACCOUNT_SID="" \
    TWILIO_AUTH_TOKEN="" \
    TWILIO_PHONE_NUMBER="" \
  --output none
echo -e "${GREEN}✅ Environment configured${NC}"

# Configure deployment
echo ""
echo -e "${BLUE}🚀 Configuring GitHub deployment...${NC}"
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "uvicorn app.main:app --host 0.0.0.0 --port 8000" \
  --output none
echo -e "${GREEN}✅ Deployment configured${NC}"

# Get app URL
APP_URL="https://$APP_NAME.azurewebsites.net"

# Create deployment credentials file
echo ""
echo -e "${BLUE}💾 Saving deployment credentials...${NC}"
cat > deployment-credentials.txt << EOF
Mew Assistant Azure Deployment
================================

App URL: $APP_URL
Resource Group: $RESOURCE_GROUP
App Name: $APP_NAME

Database Details:
-----------------
Host: $DB_NAME.postgres.database.azure.com
Database: mew_assistant
Username: $DB_ADMIN
Password: $DB_PASSWORD

Connection String:
postgresql://$DB_ADMIN:$DB_PASSWORD@$DB_NAME.postgres.database.azure.com/mew_assistant

Application Secrets:
--------------------
SECRET_KEY: $SECRET_KEY
JWT_SECRET_KEY: $JWT_SECRET

Next Steps:
-----------
1. Deploy your code:
   gh workflow run deploy.yml

2. Configure third-party services:
   az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings \\
     OPENAI_API_KEY="your-key" \\
     SMTP_HOST="smtp.gmail.com" \\
     SMTP_USER="your-email@gmail.com"

3. Access your app:
   $APP_URL

4. View logs:
   az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME

Important: Keep this file secure! It contains sensitive credentials.
EOF

chmod 600 deployment-credentials.txt

echo -e "${GREEN}✅ Credentials saved to deployment-credentials.txt${NC}"

# Summary
echo ""
echo -e "${GREEN}=========================================="
echo "🎉 Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}📱 Your Mew Assistant is ready at:${NC}"
echo -e "   ${GREEN}$APP_URL${NC}"
echo ""
echo -e "${BLUE}📝 Credentials saved to:${NC} deployment-credentials.txt"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "   1. Deploy your code:"
echo "      ${GREEN}git push origin main${NC}"
echo ""
echo "   2. Configure API keys in Azure Portal or run:"
echo "      ${GREEN}az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings OPENAI_API_KEY='your-key'${NC}"
echo ""
echo "   3. Test your deployment:"
echo "      ${GREEN}curl $APP_URL/health${NC}"
echo ""
echo -e "${RED}⚠️  IMPORTANT: Store deployment-credentials.txt securely!${NC}"
echo ""

# Offer to open in browser
read -p "Open app in browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    xdg-open "$APP_URL" 2>/dev/null || open "$APP_URL" 2>/dev/null || echo "Please visit: $APP_URL"
fi
