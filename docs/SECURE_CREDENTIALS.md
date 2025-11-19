# Secure Credentials Management

All sensitive credentials for the Mew Assistant application are securely stored in **Azure Key Vault**.

## Azure Key Vault Details

- **Vault Name**: `mew-assistant-kv-dev`
- **Vault URI**: `https://mew-assistant-kv-dev.vault.azure.net/`
- **Resource Group**: `mew-assistant-dev-rg`
- **Location**: `westus2`

## Stored Secrets

The following secrets are stored in the Key Vault:

### Database Credentials
- `db-host`: PostgreSQL server hostname
- `db-name`: Database name
- `db-username`: Database username
- `db-password`: Database password

### Application Secrets
- `jwt-secret`: JWT token signing secret

### Container Registry Credentials
- `acr-username`: Azure Container Registry username
- `acr-password`: Azure Container Registry password

## Retrieving Credentials

### Prerequisites
1. Install Azure CLI: `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`
2. Login to Azure: `az login`

### Get a Specific Secret

```bash
# Retrieve database password
az keyvault secret show \
  --vault-name mew-assistant-kv-dev \
  --name db-password \
  --query value -o tsv

# Retrieve JWT secret
az keyvault secret show \
  --vault-name mew-assistant-kv-dev \
  --name jwt-secret \
  --query value -o tsv
```

### List All Secrets

```bash
az keyvault secret list \
  --vault-name mew-assistant-kv-dev \
  --query "[].name" -o table
```

### Retrieve All Credentials (for deployment)

```bash
#!/bin/bash
# retrieve-credentials.sh

echo "Retrieving credentials from Azure Key Vault..."

DB_HOST=$(az keyvault secret show --vault-name mew-assistant-kv-dev --name db-host --query value -o tsv)
DB_NAME=$(az keyvault secret show --vault-name mew-assistant-kv-dev --name db-name --query value -o tsv)
DB_USER=$(az keyvault secret show --vault-name mew-assistant-kv-dev --name db-username --query value -o tsv)
DB_PASS=$(az keyvault secret show --vault-name mew-assistant-kv-dev --name db-password --query value -o tsv)
JWT_SECRET=$(az keyvault secret show --vault-name mew-assistant-kv-dev --name jwt-secret --query value -o tsv)

echo "Database Host: $DB_HOST"
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo "JWT Secret: [HIDDEN]"
```

## Application Access to Key Vault

The Container App uses **Managed Identity** to access Key Vault secrets without storing credentials in code:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
vault_url = "https://mew-assistant-kv-dev.vault.azure.net/"
client = SecretClient(vault_url=vault_url, credential=credential)

# Retrieve a secret
db_password = client.get_secret("db-password").value
```

## Security Best Practices

### ✅ DO
- Use Managed Identity for application access
- Rotate secrets regularly
- Enable audit logging on Key Vault
- Use separate Key Vaults for dev/staging/prod
- Grant least-privilege access

### ❌ DON'T
- Store secrets in code or configuration files
- Commit secrets to version control
- Share secrets via email or chat
- Use the same secrets across environments
- Grant unnecessary Key Vault permissions

## Access Control

### Grant Access to a User

```bash
# Grant read access to secrets
az keyvault set-policy \
  --name mew-assistant-kv-dev \
  --upn user@example.com \
  --secret-permissions get list
```

### Grant Access to Container App (Managed Identity)

```bash
# Get the Container App's managed identity
IDENTITY_ID=$(az containerapp show \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --query identity.principalId -o tsv)

# Grant access
az keyvault set-policy \
  --name mew-assistant-kv-dev \
  --object-id $IDENTITY_ID \
  --secret-permissions get list
```

## Updating Secrets

```bash
# Update a secret (creates a new version)
az keyvault secret set \
  --vault-name mew-assistant-kv-dev \
  --name db-password \
  --value "new-secure-password"

# The application will automatically use the latest version
```

## Backup and Recovery

### Backup a Secret

```bash
az keyvault secret backup \
  --vault-name mew-assistant-kv-dev \
  --name db-password \
  --file db-password-backup.blob
```

### Restore a Secret

```bash
az keyvault secret restore \
  --vault-name mew-assistant-kv-dev \
  --file db-password-backup.blob
```

## Monitoring

### Enable Diagnostic Logging

```bash
az monitor diagnostic-settings create \
  --name KeyVaultDiagnostics \
  --resource /subscriptions/YOUR_SUBSCRIPTION/resourceGroups/mew-assistant-dev-rg/providers/Microsoft.KeyVault/vaults/mew-assistant-kv-dev \
  --logs '[{"category": "AuditEvent","enabled": true}]' \
  --workspace YOUR_LOG_ANALYTICS_WORKSPACE_ID
```

## Emergency Access

If you lose access to the Key Vault:

1. **Verify Azure Login**: `az login` and select correct subscription
2. **Check Permissions**: Ensure you have appropriate access policies
3. **Contact Administrator**: Request access if permissions are missing
4. **Recovery**: Use soft-delete recovery if vault was deleted (90-day retention)

## Support

For credential-related issues:
- **Azure Support**: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade
- **Key Vault Documentation**: https://docs.microsoft.com/azure/key-vault/
