# CD Credential Flow - Quick Reference

## How It Works (End-to-End)

```
Developer Action
  ↓
git push origin v1.0.2
  ↓
GitHub Actions Triggered (cd.yml workflow)
  ├─ Security guardrails check (tests, compliance)
  └─ If all pass → Deploy to Production
  
Azure Authentication
  ├─ Decrypt AZURE_CREDENTIALS secret
  ├─ Run: az login --service-principal
  └─ Authenticate to Azure subscription
  
Build & Push
  ├─ Build Docker image with source code
  ├─ Push to Azure Container Registry (ACR)
  └─ Tag with version: mew-assistant:v1.0.2
  
Update Container App
  ├─ Run: az containerapp update
  ├─ Set image reference: latest build
  └─ Set environment variables (using secretref:)
  
Secret Resolution
  ├─ Container starts with Managed Identity
  ├─ Azure Key Vault detects secretref: references
  ├─ Managed Identity authenticates to vault
  ├─ Secrets fetched and injected
  └─ Application receives environment variables
  
Verification
  ├─ Wait 30 seconds for startup
  ├─ Call /health endpoint
  └─ Success → Deployment complete
```

## Credentials in Each Stage

### Stage 1: GitHub Actions Runner
**Visible to:** GitHub Actions (encrypted)
```
AZURE_CREDENTIALS          (Service Principal JSON)
AZURE_SUBSCRIPTION_ID      (Subscription ID)
RESOURCE_GROUP            (Resource group name)
ACR_NAME                  (Container Registry)
```

**How used:**
```bash
az login --service-principal \
  --username "$AZURE_CLIENT_ID" \
  --password "$AZURE_CLIENT_SECRET" \
  --tenant "$AZURE_TENANT_ID" \
  -s "$SUBSCRIPTION_ID"
```

### Stage 2: Azure Container Registry
**Visible to:** Docker, ACR
```
Docker image source code (public repo)
Access token: Auto-managed by Service Principal
```

**How used:**
```bash
az acr build \
  --registry mewassistantacr \
  --image mew-assistant:v1.0.2 \
  .
```

### Stage 3: Azure Container Apps Environment
**Visible to:** Container App configuration
```
DATABASE_URL=secretref:database-url
JWT_SECRET_KEY=secretref:jwt-secret
SECRET_KEY=secretref:secret-key
GOOGLE_CLIENT_ID=secretref:google-client-id
GOOGLE_CLIENT_SECRET=secretref:google-client-secret
MICROSOFT_CLIENT_ID=secretref:microsoft-client-id
MICROSOFT_CLIENT_SECRET=secretref:microsoft-client-secret
```

**Why secretref?**
- Secrets NOT stored in Container App config
- References only → No sensitive data in Azure Portal
- Resolved at runtime by Managed Identity
- Can rotate secrets without redeploying

### Stage 4: Azure Key Vault
**Visible to:** Container App Managed Identity only
```
Vault: mew-assistant-9240-kv

Secrets:
  database-url
    → postgresql://user:pass@host/db?sslmode=require
  
  jwt-secret
    → long-secure-key-for-jwt-signing
  
  secret-key
    → fastapi-secret-for-sessions
  
  google-client-id
    → YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
  
  google-client-secret
    → YOUR_GOOGLE_CLIENT_SECRET
  
  microsoft-client-id
    → YOUR_MICROSOFT_CLIENT_ID
  
  microsoft-client-secret
    → YOUR_MICROSOFT_CLIENT_SECRET
```

**Accessed by:** Container App Managed Identity (automatic)

### Stage 5: Running Container
**Visible to:** Application code
```
Environment variables (fully resolved):
  DATABASE_URL = postgresql://user:pass@host/db?sslmode=require
  JWT_SECRET_KEY = long-secure-key-for-jwt-signing
  SECRET_KEY = fastapi-secret-for-sessions
  GOOGLE_CLIENT_ID = YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET = YOUR_GOOGLE_CLIENT_SECRET
  MICROSOFT_CLIENT_ID = YOUR_MICROSOFT_CLIENT_ID
  MICROSOFT_CLIENT_SECRET = YOUR_MICROSOFT_CLIENT_SECRET
```

**Accessed by:** Python application via `os.environ` and Pydantic Settings

---

## Security Barriers

```
Developer commits → GitHub repo (public, no secrets)
        ↓
        [No credentials exposed - only source code]
        ↓
GitHub Actions needs AZURE_CREDENTIALS to login
        [Encrypted in GitHub Secrets - protected]
        ↓
Service Principal limited to specific Azure scope
        [Cannot access other subscriptions]
        ↓
Container App needs Managed Identity for vault access
        [Cannot access without explicit role]
        ↓
Key Vault encrypts secrets at rest
        [Encrypted with Azure keys]
        ↓
Application receives secrets at runtime only
        [Not stored in config, logs, or code]
```

---

## Troubleshooting Flow

### Problem: Deployment fails with "KEY not found"

```
1. Check GitHub Actions logs
   → Did deployment reach Azure Container App update step?
   
2. Check Container App environment
   az containerapp show \
     --name mew-assistant-prod \
     --resource-group mew-assistant-rg \
     --query "properties.template.containers[0].env" -o json
   
3. Check Key Vault secret exists
   az keyvault secret show \
     --vault-name mew-assistant-9240-kv \
     --name "jwt-secret"
   
4. Check Managed Identity role assignment
   az role assignment list \
     --resource-group mew-assistant-rg \
     --query "[?contains(principal.displayName, 'mew-assistant-prod')]"
   
5. Check Container App logs
   az containerapp logs show \
     --name mew-assistant-prod \
     --resource-group mew-assistant-rg \
     --tail 50
```

### Problem: "Access denied to Key Vault"

```
1. Verify Managed Identity is enabled
   az containerapp identity show \
     --name mew-assistant-prod \
     --resource-group mew-assistant-rg
   
2. Grant "Key Vault Secrets User" role
   IDENTITY_ID=$(az containerapp identity show \
     --name mew-assistant-prod \
     --resource-group mew-assistant-rg \
     --query "principalId" -o tsv)
   
   az role assignment create \
     --role "Key Vault Secrets User" \
     --assignee "$IDENTITY_ID" \
     --scope "/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.KeyVault/vaults/mew-assistant-9240-kv"
```

### Problem: GitHub Actions secrets not set

```
1. Verify AZURE_CREDENTIALS format
   - Must be valid JSON from service principal
   - Check: Settings → Secrets and Variables → Actions
   
2. Create service principal if missing
   az ad sp create-for-rbac \
     --name "github-actions-mew" \
     --role "Contributor" \
     --scopes "/subscriptions/{SUBSCRIPTION_ID}"
   
3. Copy output to GitHub as AZURE_CREDENTIALS
```

---

## Local Testing vs CD

### Local Development
```
Developer runs locally:
  1. Copy .env file with credentials
  2. Run: python -m uvicorn app.main:app
  3. Access via localhost:8000
  
Credentials: From .env (gitignored)
Security: Developer's machine only
```

### CI/CD Deployment
```
GitHub Actions runs deployment:
  1. Authenticate with Service Principal (AZURE_CREDENTIALS)
  2. Update Container App with secretref: references
  3. Container Managed Identity fetches from Key Vault
  4. Application runs with vault credentials
  
Credentials: From Azure Key Vault (encrypted)
Security: Never stored in code or runner logs
```

### Key Difference
- **Local:** Direct access to credentials via `.env`
- **CD:** Indirect access via Key Vault references (safer)

---

## Rotation Workflow

### When to Rotate
- Google OAuth credentials expire (check expiration)
- Microsoft OAuth credentials expire
- Suspected credential compromise
- Regular schedule (monthly/quarterly)
- Employee leaves team

### How to Rotate

1. **Generate new credential** (e.g., in Google Cloud Console)

2. **Update Key Vault**
   ```bash
   az keyvault secret set \
     --vault-name mew-assistant-9240-kv \
     --name "google-client-secret" \
     --value "NEW_SECRET_VALUE"
   ```

3. **Test in staging** (don't skip this)
   ```bash
   # Push to develop branch
   git push origin develop
   # GitHub Actions deploys to staging with new secret
   # Verify /health endpoint works
   # Verify OAuth login works
   ```

4. **Deploy to production**
   ```bash
   # Create version tag
   git tag -a v1.0.3 -m "Updated OAuth credentials"
   git push origin v1.0.3
   # GitHub Actions deploys to production
   ```

5. **Verify** (check logs, OAuth flow works)

6. **Document** (log rotation in security audit)

---

## Checklists

### First-Time Setup
- [ ] Service Principal created
- [ ] AZURE_CREDENTIALS added to GitHub Secrets
- [ ] Key Vault created with all secrets
- [ ] Container App has Managed Identity enabled
- [ ] Container App has "Key Vault Secrets User" role
- [ ] GitHub workflow references secretref: for all credentials
- [ ] Test deployment to staging first
- [ ] Health endpoint verified working

### Before Each Production Deployment
- [ ] All security guardrails passing (tests, compliance)
- [ ] Version tag created: `git tag -a v1.0.3`
- [ ] Key Vault secrets validated (spot check)
- [ ] Database backup created automatically
- [ ] Health check endpoint will be tested post-deploy
- [ ] Team notified of planned deployment

### After Credential Rotation
- [ ] New secret successfully stored in Key Vault
- [ ] Staging deployment tested and verified
- [ ] Production deployment completed
- [ ] Old secret documented (for rollback if needed)
- [ ] Audit log entry created
- [ ] Team notification sent
- [ ] Calendar updated for next rotation

---

## See Also
- [CONTINUOUS_DEPLOYMENT_CREDENTIALS.md](../docs/CONTINUOUS_DEPLOYMENT_CREDENTIALS.md) - Full guide
- [.github/workflows/cd.yml](../.github/workflows/cd.yml) - Workflow definition
- [scripts/setup-cd-environment.sh](../scripts/setup-cd-environment.sh) - Setup automation
