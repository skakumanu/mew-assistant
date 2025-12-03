#!/bin/bash
set -e

echo "🔧 Microsoft OAuth Setup Script"
echo "================================"
echo ""

# Check if we have the required info
if [ -z "$MICROSOFT_CLIENT_ID" ] || [ -z "$MICROSOFT_CLIENT_SECRET" ]; then
    echo "⚠️  Please set environment variables first:"
    echo ""
    echo "export MICROSOFT_CLIENT_ID='your-client-id-here'"
    echo "export MICROSOFT_CLIENT_SECRET='your-client-secret-here'"
    echo ""
    echo "Get these from Azure Portal → Microsoft Entra ID → App registrations"
    exit 1
fi

echo "📦 Step 1: Adding secrets to Azure Key Vault..."
az keyvault secret set \
  --vault-name mew-assistant-kv-dev \
  --name MICROSOFT-CLIENT-ID \
  --value "$MICROSOFT_CLIENT_ID" \
  --output none

az keyvault secret set \
  --vault-name mew-assistant-kv-dev \
  --name MICROSOFT-CLIENT-SECRET \
  --value "$MICROSOFT_CLIENT_SECRET" \
  --output none

echo "✅ Secrets stored in Key Vault"
echo ""

echo "🔗 Step 2: Getting subscription and identity info..."
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
IDENTITY_ID="/subscriptions/${SUBSCRIPTION_ID}/resourcegroups/mew-assistant-dev-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mew-assistant-dev-identity"

echo "Subscription ID: $SUBSCRIPTION_ID"
echo ""

echo "🔐 Step 3: Linking Key Vault secrets to Container App..."
az containerapp secret set \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --secrets \
    microsoft-client-id=keyvaultref:https://mew-assistant-kv-dev.vault.azure.net/secrets/MICROSOFT-CLIENT-ID,identityref:${IDENTITY_ID} \
    microsoft-client-secret=keyvaultref:https://mew-assistant-kv-dev.vault.azure.net/secrets/MICROSOFT-CLIENT-SECRET,identityref:${IDENTITY_ID} \
  --output none

echo "✅ Secrets linked"
echo ""

echo "🚀 Step 4: Updating Container App environment variables..."
az containerapp update \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --set-env-vars \
    MICROSOFT_CLIENT_ID=secretref:microsoft-client-id \
    MICROSOFT_CLIENT_SECRET=secretref:microsoft-client-secret \
  --output none

echo "✅ Environment variables updated"
echo ""

echo "⏳ Step 5: Waiting for deployment to complete..."
sleep 10

echo ""
echo "🎉 Microsoft OAuth Setup Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Verify redirect URI in Azure AD app registration:"
echo "   https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback/microsoft"
echo ""
echo "2. Test OAuth login:"
echo "   https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login"
echo ""
echo "3. Sign in with: skakumanu@hotmail.com"
echo ""
echo "4. Check logs if issues:"
echo "   az containerapp logs show --name mew-assistant-dev --resource-group mew-assistant-dev-rg --tail 100 --follow"
echo ""
