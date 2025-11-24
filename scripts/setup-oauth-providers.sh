#!/bin/bash
set -e

echo "==================================="
echo "OAuth Provider Setup for Mew Assistant"
echo "==================================="
echo ""

# Get Azure Container App URL
APP_URL="https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io"
CALLBACK_URL="$APP_URL/auth/oauth/callback"

echo "Your Mew Assistant is deployed at: $APP_URL"
echo "OAuth Callback URL: $CALLBACK_URL"
echo ""

echo "==================================="
echo "Step 1: Set up Google OAuth"
echo "==================================="
echo "1. Go to: https://console.cloud.google.com/apis/credentials"
echo "2. Create a new project or select existing"
echo "3. Click 'Create Credentials' > 'OAuth 2.0 Client ID'"
echo "4. Application type: 'Web application'"
echo "5. Name: 'Mew Assistant'"
echo "6. Authorized redirect URIs: $CALLBACK_URL"
echo "7. Copy the Client ID and Client Secret"
echo ""
read -p "Enter Google Client ID: " GOOGLE_CLIENT_ID
read -p "Enter Google Client Secret: " GOOGLE_CLIENT_SECRET

echo ""
echo "==================================="
echo "Step 2: Set up Microsoft OAuth"
echo "==================================="
echo "1. Go to: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
echo "2. Click 'New registration'"
echo "3. Name: 'Mew Assistant'"
echo "4. Supported account types: 'Accounts in any organizational directory and personal Microsoft accounts'"
echo "5. Redirect URI: Web - $CALLBACK_URL"
echo "6. Register the application"
echo "7. Copy the 'Application (client) ID'"
echo "8. Go to 'Certificates & secrets' > 'New client secret'"
echo "9. Copy the secret value"
echo ""
read -p "Enter Microsoft Client ID: " MICROSOFT_CLIENT_ID
read -p "Enter Microsoft Client Secret: " MICROSOFT_CLIENT_SECRET

echo ""
echo "==================================="
echo "Step 3: Storing credentials in Azure Key Vault"
echo "==================================="

KEYVAULT_NAME="mew-keyvault-dev"

# Store Google credentials
az keyvault secret set --vault-name $KEYVAULT_NAME --name "google-client-id" --value "$GOOGLE_CLIENT_ID"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "google-client-secret" --value "$GOOGLE_CLIENT_SECRET"

# Store Microsoft credentials
az keyvault secret set --vault-name $KEYVAULT_NAME --name "microsoft-client-id" --value "$MICROSOFT_CLIENT_ID"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "microsoft-client-secret" --value "$MICROSOFT_CLIENT_SECRET"

echo ""
echo "✅ OAuth credentials stored successfully!"
echo ""

echo "==================================="
echo "Step 4: Update Container App Environment Variables"
echo "==================================="

az containerapp update \
  --name mew-assistant-dev \
  --resource-group mew-assistant-rg \
  --set-env-vars \
    GOOGLE_CLIENT_ID="secretref:google-client-id" \
    GOOGLE_CLIENT_SECRET="secretref:google-client-secret" \
    MICROSOFT_CLIENT_ID="secretref:microsoft-client-id" \
    MICROSOFT_CLIENT_SECRET="secretref:microsoft-client-secret" \
    OAUTH_REDIRECT_URI="$CALLBACK_URL"

echo ""
echo "✅ Container App updated with OAuth credentials!"
echo ""

echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo "You can now test OAuth login at: $APP_URL/auth/oauth/login"
echo ""
