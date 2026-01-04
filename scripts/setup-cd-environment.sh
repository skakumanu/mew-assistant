#!/bin/bash

# Setup script to configure Azure Key Vault for GitHub Actions CD
# Run this once to enable automated credential deployment

set -e

# Configuration
VAULT_NAME="mew-assistant-9240-kv"
RESOURCE_GROUP="mew-assistant-rg"
CONTAINER_APP="mew-assistant-prod"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "========================================="
echo "🔐 Azure Key Vault CD Setup"
echo "========================================="
echo ""
echo "Configuration:"
echo "  Vault: $VAULT_NAME"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Container App: $CONTAINER_APP"
echo "  Subscription: $SUBSCRIPTION_ID"
echo ""

# Step 1: Verify Key Vault exists and check secrets
echo "📋 Step 1: Verifying Key Vault secrets..."
REQUIRED_SECRETS=(
  "database-url"
  "jwt-secret"
  "secret-key"
  "google-client-id"
  "google-client-secret"
  "microsoft-client-id"
  "microsoft-client-secret"
)

MISSING_SECRETS=()
for secret in "${REQUIRED_SECRETS[@]}"; do
  if az keyvault secret show --vault-name "$VAULT_NAME" --name "$secret" &>/dev/null; then
    echo "  ✓ $secret"
  else
    echo "  ✗ $secret (MISSING)"
    MISSING_SECRETS+=("$secret")
  fi
done

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
  echo ""
  echo "⚠️  Missing secrets in Key Vault:"
  for secret in "${MISSING_SECRETS[@]}"; do
    echo "    - $secret"
  done
  echo ""
  echo "Add them with:"
  echo "  az keyvault secret set --vault-name $VAULT_NAME --name SECRET_NAME --value SECRET_VALUE"
  echo ""
fi

# Step 2: Get Container App Managed Identity
echo ""
echo "🔍 Step 2: Getting Container App Managed Identity..."
IDENTITY_ID=$(az containerapp identity show \
  --name "$CONTAINER_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "principalId" -o tsv)

if [ -z "$IDENTITY_ID" ]; then
  echo "  ✗ Could not get identity. Enable Managed Identity first:"
  echo "    az containerapp identity assign --name $CONTAINER_APP --resource-group $RESOURCE_GROUP"
  exit 1
fi

echo "  ✓ Identity ID: $IDENTITY_ID"

# Step 3: Grant Key Vault access
echo ""
echo "🔐 Step 3: Granting Key Vault access to Container App..."

VAULT_SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$VAULT_NAME"

# Check if role already assigned
EXISTING_ROLE=$(az role assignment list \
  --assignee "$IDENTITY_ID" \
  --scope "$VAULT_SCOPE" \
  --role "Key Vault Secrets User" \
  --query "[0].id" -o tsv)

if [ ! -z "$EXISTING_ROLE" ] && [ "$EXISTING_ROLE" != "None" ]; then
  echo "  ✓ Key Vault Secrets User role already assigned"
else
  echo "  Assigning Key Vault Secrets User role..."
  az role assignment create \
    --role "Key Vault Secrets User" \
    --assignee "$IDENTITY_ID" \
    --scope "$VAULT_SCOPE"
  echo "  ✓ Role assigned"
fi

# Step 4: Verify GitHub Actions configuration
echo ""
echo "📚 Step 4: Verifying GitHub Actions setup..."
echo ""
echo "Required GitHub Secrets (Settings → Secrets and Variables → Actions):"
echo "  - AZURE_CREDENTIALS (Service Principal JSON)"
echo "  - AZURE_SUBSCRIPTION_ID"
echo "  - RESOURCE_GROUP: $RESOURCE_GROUP"
echo "  - ACR_NAME (Container Registry name)"
echo ""

# Step 5: Test Container App environment
echo "✅ Step 5: Verifying Container App environment..."
CONTAINER_ENV=$(az containerapp show \
  --name "$CONTAINER_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.template.containers[0].env" -o json)

echo "  Current environment variables:"
echo "$CONTAINER_ENV" | jq '.[] | select(.value != null) | {name: .name, has_value: true}' 2>/dev/null || \
echo "$CONTAINER_ENV" | jq '.[] | {name: .name, value_type: (if .value then "direct" else "reference" end)}' 2>/dev/null || \
echo "  Could not parse environment"

# Step 6: Final instructions
echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Verify GitHub Secrets are set:"
echo "   https://github.com/YOUR_ORG/mew-assistant/settings/secrets/actions"
echo ""
echo "2. Add missing Key Vault secrets if needed:"
for secret in "${MISSING_SECRETS[@]}"; do
  echo "   az keyvault secret set --vault-name $VAULT_NAME --name $secret --value YOUR_VALUE"
done
echo ""
echo "3. Test CD pipeline by creating a version tag:"
echo "   git tag -a v1.0.3 -m 'Test CD deployment'"
echo "   git push origin v1.0.3"
echo ""
echo "4. Monitor deployment:"
echo "   - GitHub Actions: https://github.com/YOUR_ORG/mew-assistant/actions"
echo "   - Azure Portal: Container Apps → mew-assistant-prod"
echo ""
echo "Credential flow during deployment:"
echo "  GitHub Secrets (encrypted)"
echo "         ↓"
echo "  GitHub Actions Workflow (uses az login)"
echo "         ↓"
echo "  Azure Container App Update (references Key Vault)"
echo "         ↓"
echo "  Container Managed Identity (fetches secrets at runtime)"
echo "         ↓"
echo "  Application Environment Variables"
echo ""
echo "For troubleshooting, see docs/CONTINUOUS_DEPLOYMENT_CREDENTIALS.md"
echo ""
