#!/bin/bash
set -e

RESOURCE_GROUP="mew-assistant-dev-rg"
APP_NAME="mew-assistant-dev"
KV_NAME="mew-assistant-kv-dev"

echo "Enabling system-assigned managed identity..."
az containerapp identity assign \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --system-assigned

echo "Getting principal ID..."
PRINCIPAL_ID=$(az containerapp identity show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

echo "Principal ID: $PRINCIPAL_ID"

echo "Granting Key Vault access..."
az keyvault set-policy \
  --name $KV_NAME \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list

echo "Setting secrets from Key Vault..."
az containerapp secret set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    google-client-id="keyvaultref:https://$KV_NAME.vault.azure.net/secrets/GOOGLE-CLIENT-ID,identityref:system" \
    google-client-secret="keyvaultref:https://$KV_NAME.vault.azure.net/secrets/GOOGLE-CLIENT-SECRET,identityref:system"

echo "Updating environment variables..."
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    "GOOGLE_CLIENT_ID=secretref:google-client-id" \
    "GOOGLE_CLIENT_SECRET=secretref:google-client-secret" \
    "OAUTH_REDIRECT_URI=https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback"

echo "OAuth configuration complete!"
