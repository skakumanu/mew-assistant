# Azure Key Vault Setup for CD - Implementation Guide

This guide helps you set up Azure Key Vault to securely manage credentials for GitHub Actions CD deployment.

---

## Step 1: Create Azure Key Vault (if not exists)

```bash
VAULT_NAME="mew-assistant-9240-kv"
RESOURCE_GROUP="mew-assistant-rg"
LOCATION="westus2"

# Create Key Vault
az keyvault create \
  --name "$VAULT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --enabled-for-deployment true \
  --enabled-for-disk-encryption false \
  --enable-rbac-authorization true

echo "✓ Key Vault created: $VAULT_NAME"
```

---

## Step 2: Add Secrets to Key Vault

```bash
VAULT_NAME="mew-assistant-9240-kv"

# Database credentials
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "database-url" \
  --value "postgresql://mewadmin:mew_password_2026_secure@mew-assistant-db.postgres.database.azure.com:5432/mew_assistant?sslmode=require"

# FastAPI secrets
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "secret-key" \
  --value "your-long-secure-fastapi-secret-key-min-32-chars"

# JWT secret
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "jwt-secret" \
  --value "your-long-secure-jwt-signing-key-min-32-chars"

# Google OAuth
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "google-client-id" \
  --value "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"

az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "google-client-secret" \
  --value "YOUR_GOOGLE_CLIENT_SECRET"

# Microsoft OAuth
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "microsoft-client-id" \
  --value "YOUR_MICROSOFT_CLIENT_ID"

az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "microsoft-client-secret" \
  --value "YOUR_MICROSOFT_CLIENT_SECRET"

# Verify all secrets created
echo "Verifying secrets in Key Vault..."
az keyvault secret list --vault-name "$VAULT_NAME" --query "[].name" -o tsv | sed 's/^/  ✓ /'
```

---

## Step 3: Configure Container App Managed Identity

```bash
CONTAINER_APP="mew-assistant-prod"
RESOURCE_GROUP="mew-assistant-rg"
VAULT_NAME="mew-assistant-9240-kv"

# Enable Managed Identity (if not already enabled)
az containerapp identity assign \
  --name "$CONTAINER_APP" \
  --resource-group "$RESOURCE_GROUP"

# Get the Container App's Managed Identity Object ID
IDENTITY_ID=$(az containerapp identity show \
  --name "$CONTAINER_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "principalId" -o tsv)

echo "Managed Identity ID: $IDENTITY_ID"

# Get Vault Resource ID
VAULT_ID=$(az keyvault show \
  --name "$VAULT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "id" -o tsv)

# Grant "Key Vault Secrets User" role to Container App
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "$IDENTITY_ID" \
  --scope "$VAULT_ID"

echo "✓ Granted Key Vault Secrets User role to $CONTAINER_APP"
```

---

## Step 4: Verify Container App Environment Configuration

```bash
CONTAINER_APP="mew-assistant-prod"
RESOURCE_GROUP="mew-assistant-rg"

# Show current environment variables
echo "Current Container App environment:"
az containerapp show \
  --name "$CONTAINER_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.template.containers[0].env" -o table

# All secretref: values should be present (values are hidden)
# They will be resolved at runtime by Managed Identity
```

Expected output:
```
Name                      Value
------------------------  -----------
DATABASE_URL              secretref:database-url
JWT_SECRET_KEY            secretref:jwt-secret
SECRET_KEY                secretref:secret-key
GOOGLE_CLIENT_ID          secretref:google-client-id
GOOGLE_CLIENT_SECRET      secretref:google-client-secret
MICROSOFT_CLIENT_ID       secretref:microsoft-client-id
MICROSOFT_CLIENT_SECRET   secretref:microsoft-client-secret
BASE_URL                  https://mew-assistant-prod...
ENVIRONMENT               production
```

---

## Step 5: Configure GitHub Actions Secrets

Go to your GitHub repository:
**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

### `AZURE_CREDENTIALS`
Service Principal credentials (JSON format):

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "github-actions-mew" \
  --role "Contributor" \
  --scopes "/subscriptions/$(az account show --query id -o tsv)"

# Copy the full JSON output and paste as AZURE_CREDENTIALS in GitHub
```

### `AZURE_SUBSCRIPTION_ID`
```bash
az account show --query id -o tsv
```

### `RESOURCE_GROUP`
```
mew-assistant-rg
```

### `ACR_NAME`
```
mewassistantacr
```

---

## Step 6: Verify CD Credential Deployment

### Option A: Test with Staging Deployment

```bash
# Push to develop to trigger staging deployment
git push origin develop

# Watch GitHub Actions: https://github.com/YOUR_ORG/mew-assistant/actions

# Verify staging deployment got credentials:
# 1. Check GitHub Actions logs for ✅ credential verification
# 2. Test staging health endpoint
# 3. Verify OAuth login works in staging
```

### Option B: Test with Production Deployment

```bash
# Create version tag to trigger production deployment
git tag -a v1.0.3 -m "Test CD credential deployment"
git push origin v1.0.3

# Watch GitHub Actions for deployment progress
# Monitor Container App in Azure Portal
```

### Option C: Manual Verification

```bash
# Check if deployment used correct credentials
az containerapp logs show \
  --name mew-assistant-prod \
  --resource-group mew-assistant-rg \
  --tail 50

# Should see: "Database connection successful" or similar
# NOT "connection failed" or "authentication error"
```

---

## Step 7: Monitor Deployment

### GitHub Actions Workflow

The CD workflow now includes a credential verification step:

```yaml
- name: 🔐 Verify Key Vault Credentials (Pre-deployment Check)
  run: |
    for secret in database-url jwt-secret secret-key google-client-id ...; do
      if az keyvault secret show --vault-name $VAULT_NAME --name "$secret" &>/dev/null; then
        echo "  ✓ $secret"
      else
        echo "  ✗ MISSING: $secret"
        exit 1
      fi
    done
```

This ensures all credentials exist before attempting deployment.

### Deployment Flow

1. **Developer pushes tag** → GitHub Actions triggered
2. **Security guardrails check** → Tests, compliance, secrets scan
3. **Credential verification** → All Key Vault secrets validated
4. **Azure authentication** → Service Principal logs in
5. **Image build & push** → Docker image → ACR
6. **Container App update** → Uses secretref: for credentials
7. **Container starts** → Managed Identity fetches from vault
8. **Health check** → Verifies deployment success

---

## Troubleshooting

### Problem: "MISSING: database-url"

**Cause:** Secret not created in Key Vault

**Solution:**
```bash
az keyvault secret set \
  --vault-name mew-assistant-9240-kv \
  --name "database-url" \
  --value "postgresql://..."
```

### Problem: "Access denied to Key Vault"

**Cause:** Container App Managed Identity doesn't have role

**Solution:**
```bash
IDENTITY_ID=$(az containerapp identity show \
  --name mew-assistant-prod \
  --resource-group mew-assistant-rg \
  --query "principalId" -o tsv)

az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "$IDENTITY_ID" \
  --scope "/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.KeyVault/vaults/mew-assistant-9240-kv"
```

### Problem: "Invalid AZURE_CREDENTIALS format"

**Cause:** GitHub secret not in valid JSON format

**Solution:**
```bash
# Verify format
az ad sp create-for-rbac --name "test" | jq . > /tmp/creds.json

# Paste contents of /tmp/creds.json into GitHub as AZURE_CREDENTIALS
```

### Problem: GitHub Actions fails but no clear error

**Solution:**
1. Check GitHub Actions logs (full output)
2. Look for ✓ or ✗ in credential verification step
3. Check Azure Portal → Container Apps → Revisions → Logs
4. Check Key Vault → Access policies → Verify Managed Identity has role

---

## Security Checklist

- [ ] Key Vault created with RBAC enabled
- [ ] All 7 required secrets added to vault
- [ ] Container App Managed Identity enabled
- [ ] Container App has "Key Vault Secrets User" role on vault
- [ ] GitHub AZURE_CREDENTIALS secret set correctly
- [ ] GitHub workflow uses `secretref:` (not inline values)
- [ ] Service Principal limited to specific subscription
- [ ] Database backup configured before deployments
- [ ] Health check enabled post-deployment
- [ ] Audit logging enabled on Key Vault

---

## Rotation Schedule

### Monthly: Check credential expiration
```bash
# Google OAuth - check in Google Cloud Console
# Microsoft Entra - check in Azure AD
# Database password - check expiration date
```

### When Rotating: Update Secret
```bash
# Update in Key Vault
az keyvault secret set \
  --vault-name mew-assistant-9240-kv \
  --name "google-client-secret" \
  --value "NEW_SECRET_VALUE"

# Next deployment automatically uses new secret
```

---

## Reference Scripts

### Quick Setup (automated)
```bash
bash scripts/setup-cd-environment.sh
```

### Verify All Credentials
```bash
VAULT_NAME="mew-assistant-9240-kv"
for secret in database-url jwt-secret secret-key google-client-id google-client-secret microsoft-client-id microsoft-client-secret; do
  if az keyvault secret show --vault-name "$VAULT_NAME" --name "$secret" &>/dev/null; then
    echo "✓ $secret"
  else
    echo "✗ MISSING: $secret"
  fi
done
```

### Test Deployment
```bash
# Staging test
git push origin develop

# Production test
git tag -a v1.0.test -m "Test"
git push origin v1.0.test
```

---

## See Also

- [CONTINUOUS_DEPLOYMENT_CREDENTIALS.md](./CONTINUOUS_DEPLOYMENT_CREDENTIALS.md) - Conceptual overview
- [CD_CREDENTIAL_QUICK_REFERENCE.md](./CD_CREDENTIAL_QUICK_REFERENCE.md) - Quick reference
- [.github/workflows/cd.yml](../.github/workflows/cd.yml) - Workflow definition
- [scripts/setup-cd-environment.sh](../scripts/setup-cd-environment.sh) - Automated setup
