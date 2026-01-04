# Continuous Deployment - Credential Management

This guide explains how credentials are automatically applied during GitHub Actions continuous deployment.

---

## Architecture Overview

```
GitHub Secrets (Encrypted)
         ↓
GitHub Actions Workflow (.github/workflows/cd.yml)
         ↓
Azure CLI Login (AZURE_CREDENTIALS)
         ↓
Azure Container App Update
         ↓
Azure Key Vault References (secretref:)
         ↓
Container Runtime Environment Variables
```

---

## Setup Requirements

### 1. GitHub Secrets Configuration

Store these secrets in your GitHub repository (Settings → Secrets and Variables → Actions):

```
AZURE_CREDENTIALS         # Service Principal credentials (JSON)
AZURE_SUBSCRIPTION_ID     # Azure subscription ID
RESOURCE_GROUP           # Azure resource group name
ACR_NAME                 # Azure Container Registry name
```

**How to create AZURE_CREDENTIALS:**

```bash
# Create a service principal with Container Apps contributor access
az ad sp create-for-rbac \
  --name "github-actions-mew" \
  --role "Contributor" \
  --scopes "/subscriptions/{SUBSCRIPTION_ID}"

# Copy the output JSON and add it as AZURE_CREDENTIALS secret
```

### 2. Azure Key Vault Setup

Store sensitive application credentials in Azure Key Vault:

```
Key Vault: mew-assistant-9240-kv
├── database-url
├── jwt-secret
├── google-client-id
├── google-client-secret
├── microsoft-client-id
└── microsoft-client-secret
```

**Create secrets in Key Vault:**

```bash
az keyvault secret set \
  --vault-name mew-assistant-9240-kv \
  --name "database-url" \
  --value "postgresql://user:pass@host/db?sslmode=require"

az keyvault secret set \
  --vault-name mew-assistant-9240-kv \
  --name "jwt-secret" \
  --value "your-long-secure-jwt-secret-key"

# ... repeat for other secrets
```

### 3. Container App Identity Configuration

Grant the Container App's Managed Identity access to Key Vault:

```bash
# Get the Container App's managed identity
IDENTITY_ID=$(az containerapp identity show \
  --resource-group mew-assistant-rg \
  --name mew-assistant-prod \
  --query "principalId" -o tsv)

# Grant Key Vault Secrets User role
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "$IDENTITY_ID" \
  --scope "/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.KeyVault/vaults/mew-assistant-9240-kv"
```

---

## GitHub Actions Workflow

### Deployment Steps

```yaml
# .github/workflows/cd.yml

deploy-production:
  name: Deploy to Production
  runs-on: ubuntu-latest
  needs: [guardrail-gates]  # Must pass security checks first
  if: startsWith(github.ref, 'refs/tags/v')  # Only on version tags
  
  steps:
  # 1. Authenticate with Azure
  - name: Login to Azure
    uses: azure/login@v2
    with:
      creds: ${{ secrets.AZURE_CREDENTIALS }}
  
  # 2. Build and push container image
  - name: Build and push to ACR
    run: |
      az acr build \
        --registry ${{ secrets.ACR_NAME }} \
        --image mew-assistant:${{ github.ref_name }} \
        --image mew-assistant:production-latest \
        .
  
  # 3. Create database backup
  - name: Create pre-deployment backup
    run: |
      az postgres flexible-server backup create \
        --resource-group ${{ secrets.RESOURCE_GROUP }} \
        --name mew-assistant-db \
        --backup-name pre-deploy-$(date +%Y%m%d-%H%M%S)
  
  # 4. Update Container App with credentials
  - name: Deploy to Container App
    run: |
      az containerapp update \
        --name mew-assistant-prod \
        --resource-group ${{ secrets.RESOURCE_GROUP }} \
        --image ${{ secrets.ACR_NAME }}.azurecr.io/mew-assistant:${{ github.ref_name }} \
        --set-env-vars \
          ENVIRONMENT=production \
          DATABASE_URL=secretref:database-url \
          JWT_SECRET_KEY=secretref:jwt-secret \
          GOOGLE_CLIENT_ID=secretref:google-client-id \
          GOOGLE_CLIENT_SECRET=secretref:google-client-secret \
          MICROSOFT_CLIENT_ID=secretref:microsoft-client-id \
          MICROSOFT_CLIENT_SECRET=secretref:microsoft-client-secret \
          BASE_URL=https://mew-assistant-prod.lemonpebble-22f4004c.westus2.azurecontainerapps.io
  
  # 5. Verify deployment
  - name: Health check
    run: |
      sleep 30
      curl -f https://mew-assistant-prod.lemonpebble-22f4004c.westus2.azurecontainerapps.io/health
```

---

## Credential Flow

### What Happens Automatically

1. **Developer pushes tag** (e.g., `git tag -a v1.0.2`)
   ```bash
   git tag -a v1.0.2 -m "Release message"
   git push origin v1.0.2
   ```

2. **GitHub Actions triggers** based on tag pattern `refs/tags/v*`

3. **Security guardrails run** (tests, compliance checks)
   - If any fail → Deployment blocked
   - If all pass → Proceed to deployment

4. **Azure authentication** using AZURE_CREDENTIALS secret
   - Service Principal credentials decrypted
   - CLI authenticated to Azure subscription

5. **Container image built and pushed** to Azure Container Registry

6. **Container App updated** with:
   - New image reference
   - Environment variables using `secretref:` syntax

7. **Key Vault references resolved**
   - Container App's Managed Identity used to access vault
   - Secrets fetched at runtime (not at deployment time)
   - Secrets injected into container environment

8. **Health endpoint verified**
   - Container App startup checked
   - Deployment confirmed healthy

---

## Security Best Practices

### ✅ DO

- ✅ Store secrets in Azure Key Vault (encrypted at rest)
- ✅ Use Managed Identity for container-to-vault authentication
- ✅ Use `secretref:` syntax for vault references (not inline values)
- ✅ Require security guardrails to pass before deployment
- ✅ Create database backups before production deployments
- ✅ Use different credentials per environment (staging vs production)
- ✅ Rotate credentials regularly
- ✅ Log deployment events and monitor access

### ❌ DON'T

- ❌ Store credentials in code or `.env` files in git
- ❌ Use inline credential values in deployment scripts
- ❌ Commit GitHub Secrets to repository
- ❌ Hardcode connection strings in infrastructure scripts
- ❌ Log secret values in workflow output
- ❌ Share credentials across environments
- ❌ Use personal access tokens (use service principals)
- ❌ Skip security checks to speed up deployment

---

## Troubleshooting

### Deployment Fails: "SECRET_KEY not found"

**Problem:** Container App environment is missing required variable.

**Solution:**
```bash
# Verify secret exists in Key Vault
az keyvault secret show \
  --vault-name mew-assistant-9240-kv \
  --name "jwt-secret"

# Verify Container App references it
az containerapp show \
  --name mew-assistant-prod \
  --resource-group mew-assistant-rg \
  --query "properties.template.containers[0].env" -o json
```

### Deployment Fails: "Access denied to Key Vault"

**Problem:** Container App's Managed Identity lacks vault permissions.

**Solution:**
```bash
# Check current role assignments
az role assignment list \
  --resource-group mew-assistant-rg \
  --query "[?principal.displayName=='mew-assistant-prod'].{role:roleDefinitionName, scope:scope}"

# Add missing role
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "$IDENTITY_ID" \
  --scope "/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.KeyVault/vaults/mew-assistant-9240-kv"
```

### Deployment Fails: "Invalid image reference"

**Problem:** Container Registry credentials incorrect.

**Solution:**
```bash
# Verify ACR login
az acr login --name ${{ secrets.ACR_NAME }}

# Check image exists
az acr repository show \
  --name ${{ secrets.ACR_NAME }} \
  --image mew-assistant:production-latest
```

---

## Environment-Specific Configuration

### Staging Deployment
```yaml
deploy-staging:
  if: github.ref == 'refs/heads/develop'
  environment:
    name: staging
    url: https://staging.mew-assistant.com
  
  # Same steps but:
  # - Different container app name: mew-assistant-staging
  # - Different environment: ENVIRONMENT=staging
  # - Optional: Use Key Vault or GitHub Secrets for staging
```

### Production Deployment
```yaml
deploy-production:
  if: startsWith(github.ref, 'refs/tags/v')
  environment:
    name: production
    url: https://mew-assistant.com
  
  # Full steps with:
  # - Database backups (required)
  # - All credentials from Key Vault
  # - Health checks (required)
  # - Rollback capability
```

---

## Rotation Schedule

### Credentials Rotation Timeline

- **JWT Secret:** Every 3 months or when role changes
- **OAuth Credentials:** When tokens expire or on suspected compromise
- **Database Password:** Every 6 months
- **Service Principal:** Every 1 year

**Rotation Process:**
1. Update secret in Azure Key Vault
2. Test in staging environment
3. Deploy to production
4. Verify no alerts in logs
5. Document rotation date

---

## Monitoring & Auditing

### GitHub Actions Logs
- Accessible in repository → Actions → Workflow runs
- Shows deployment steps (but NOT secret values)
- Automatically rotated for 90 days

### Azure Audit Logs
```bash
# View Key Vault access logs
az monitor activity-log list \
  --resource-group mew-assistant-rg \
  --resource-provider Microsoft.KeyVault

# View Container App deployment history
az containerapp revision list \
  --name mew-assistant-prod \
  --resource-group mew-assistant-rg \
  --query "[].{date:properties.createdTime, status:properties.provisioningState}"
```

---

## Reference: Secrets Checklist

When setting up CD for a new environment:

- [ ] Service Principal created with appropriate scopes
- [ ] AZURE_CREDENTIALS added to GitHub Secrets
- [ ] Azure subscription ID stored (AZURE_SUBSCRIPTION_ID)
- [ ] Resource group name known (RESOURCE_GROUP)
- [ ] Container Registry name configured (ACR_NAME)
- [ ] Key Vault created and secrets populated
- [ ] Container App Managed Identity has Key Vault access
- [ ] GitHub Actions workflow uses `secretref:` for vault references
- [ ] Staging environment tested before production
- [ ] Database backup process configured
- [ ] Health check endpoint verified
- [ ] Monitoring and alerts configured
- [ ] Documentation updated with environment details

---

## Quick Start: Enable CD for New Environment

```bash
#!/bin/bash
set -e

VAULT_NAME="mew-assistant-9240-kv"
ENV_NAME="production"
CONTAINER_APP="mew-assistant-prod"
RESOURCE_GROUP="mew-assistant-rg"

# 1. Ensure secrets exist in Key Vault
echo "Checking Key Vault secrets..."
for secret in database-url jwt-secret google-client-id google-client-secret microsoft-client-id microsoft-client-secret; do
  if ! az keyvault secret show --vault-name $VAULT_NAME --name "$secret" &>/dev/null; then
    echo "⚠️  Missing secret: $secret"
  else
    echo "✓ Found: $secret"
  fi
done

# 2. Get Container App identity
IDENTITY_ID=$(az containerapp identity show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query "principalId" -o tsv)

# 3. Grant Key Vault access
echo "Granting Key Vault access to Container App..."
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "$IDENTITY_ID" \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$VAULT_NAME" \
  || echo "Role already assigned"

# 4. Verify Container App environment
echo "Verifying Container App configuration..."
az containerapp show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query "properties.template.containers[0].env[].name" -o tsv

echo "✅ Environment ready for CD deployment"
```

Save as `setup-cd-environment.sh` and run:
```bash
chmod +x setup-cd-environment.sh
./setup-cd-environment.sh
```

---

## See Also

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Key Vault Integration](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/using-secrets-in-github-actions)
- [Azure Container Apps Secrets](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets)
- [Service Principal in Azure](https://learn.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
