# Azure Cloud Infrastructure Setup

This document provides a comprehensive guide for setting up Azure cloud infrastructure for Mew Assistant, including secure secret storage, encrypted backups, and scalability features.

## 🚀 Features Implemented

### 1. Azure Key Vault Integration
- Secure storage for API keys, tokens, and credentials
- Automatic fallback to local `.env` if Key Vault unavailable
- Zero secrets in code or version control

### 2. Azure Blob Storage
- Encrypted database backups with AES-128
- Geo-redundant storage for disaster recovery
- Automatic backup retention and cleanup
- User data export for GDPR compliance

### 3. Encryption at Rest
- All data encrypted before upload to cloud
- Fernet symmetric encryption (AES-128)
- Encryption keys stored securely in Key Vault

### 4. Scalability
- Terraform Infrastructure as Code
- Container-based deployment
- Auto-scaling ready architecture
- PostgreSQL Flexible Server for managed database

## 📋 Prerequisites

1. **Azure Account**: Active Azure subscription
2. **Azure CLI**: Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
3. **Terraform**: Install from https://www.terraform.io/downloads
4. **Podman/Docker**: For container management

## 🔧 Installation Steps

### Step 1: Install Azure SDK Dependencies

```bash
pip install -r requirements.txt
```

This includes:
- `azure-identity`: Authentication
- `azure-keyvault-secrets`: Secret management
- `azure-storage-blob`: Backup storage
- `cryptography`: Encryption

### Step 2: Azure Login

```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### Step 3: Generate Encryption Key

```bash
# Generate a new encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save this key securely - you'll need it for the next steps.

### Step 4: Deploy Infrastructure (Optional)

If you want to deploy to Azure Cloud:

```bash
# Initialize and deploy
cd infrastructure/azure
./scripts/deploy.sh dev

# Get outputs
cd terraform
terraform output
```

### Step 5: Configure Environment

Update your `.env` file:

```bash
# Azure Key Vault
AZURE_KEY_VAULT_URL=https://mew-assistant-dev-kv.vault.azure.net/

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=mewassistantdevst;AccountKey=...
AZURE_STORAGE_CONTAINER=mew-backups

# Encryption Key (from Step 3)
ENCRYPTION_KEY=your_generated_key_here
```

## 🔐 Security Features

### 1. Secret Management

Secrets are retrieved in this priority order:
1. Azure Key Vault (production)
2. Environment variables (development)
3. `.env` file (local development)

```python
from app.cloud.azure_key_vault import key_vault_client

# Get secret
api_key = key_vault_client.get_secret("OPENAI_API_KEY")

# Set secret (admin only)
key_vault_client.set_secret("NEW_API_KEY", "value")
```

### 2. Data Encryption

All data is encrypted before being stored:

```python
from app.cloud.encryption import encryption_service

# Encrypt sensitive data
encrypted = encryption_service.encrypt_string("sensitive data")

# Decrypt when needed
decrypted = encryption_service.decrypt_string(encrypted)
```

### 3. Secure Backups

Backups are automatically encrypted and stored in geo-redundant Azure Storage:

```python
from app.cloud.azure_storage import azure_storage

# Create encrypted backup
azure_storage.backup_database("mew_assistant.db")

# List all backups
backups = azure_storage.list_backups()

# Restore from backup
azure_storage.restore_database("backup_20240101.db.enc", "restored.db")
```

## 📡 API Endpoints

### Create Backup

```bash
curl -X POST http://localhost:8000/api/backup/create \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Response:
```json
{
  "success": true,
  "message": "Backup initiated",
  "backup_name": "backup_20240115_143000.db.enc",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### List Backups

```bash
curl http://localhost:8000/api/backup/list \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Response:
```json
{
  "success": true,
  "count": 5,
  "backups": [
    {
      "name": "backup_20240115_143000.db.enc",
      "size": 2048576,
      "created": "2024-01-15T14:30:00Z",
      "modified": "2024-01-15T14:30:00Z",
      "metadata": {
        "original_size": "1048576",
        "encrypted_size": "2048576"
      }
    }
  ]
}
```

### Restore Backup

```bash
curl -X POST http://localhost:8000/api/backup/restore \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_name": "backup_20240115_143000.db.enc"}'
```

### Export User Data (GDPR Compliance)

```bash
curl -X POST http://localhost:8000/api/backup/export-user-data \
  -H "Authorization: Bearer YOUR_USER_TOKEN"
```

### Cleanup Old Backups

```bash
curl -X DELETE http://localhost:8000/api/backup/cleanup?days=30 \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Cloud                          │
│                                                          │
│  ┌──────────────┐      ┌──────────────┐               │
│  │  Key Vault   │      │   Storage    │               │
│  │   Secrets    │      │   Backups    │               │
│  │              │      │ (Geo-redundant)               │
│  └──────┬───────┘      └──────┬───────┘               │
│         │                     │                        │
│         │   ┌─────────────────┘                        │
│         │   │                                          │
│  ┌──────▼───▼───────────────────────┐                 │
│  │     Mew Assistant App            │                 │
│  │  - FastAPI                        │                 │
│  │  - Encryption Service             │                 │
│  │  - Backup Service                 │                 │
│  └──────────┬───────────────────────┘                 │
│             │                                          │
│  ┌──────────▼───────────┐                             │
│  │  PostgreSQL          │                             │
│  │  (Managed)           │                             │
│  └──────────────────────┘                             │
└──────────────────────────────────────────────────────────┘
```

## 📊 Monitoring and Maintenance

### Automatic Backup Schedule

Set up a cron job or Azure Function to create regular backups:

```bash
# Daily backup at 2 AM
0 2 * * * curl -X POST http://localhost:8000/api/backup/create -H "Authorization: Bearer TOKEN"
```

### Backup Retention Policy

Automatically delete backups older than 30 days:

```bash
# Weekly cleanup
0 0 * * 0 curl -X DELETE http://localhost:8000/api/backup/cleanup?days=30 -H "Authorization: Bearer TOKEN"
```

### Monitor Backup Status

Check application logs:

```bash
tail -f logs/mew_assistant.log | grep -i backup
```

## 🔍 Troubleshooting

### Issue: Key Vault Connection Failed

**Symptoms**: `AZURE_KEY_VAULT_URL not set, using local .env fallback`

**Solution**:
1. Verify Azure CLI is logged in: `az account show`
2. Check `.env` has correct `AZURE_KEY_VAULT_URL`
3. Ensure your Azure identity has Key Vault access permissions

### Issue: Storage Upload Failed

**Symptoms**: `Failed to backup database: connection refused`

**Solution**:
1. Verify connection string: `az storage account show-connection-string`
2. Check firewall rules allow your IP
3. Ensure container exists

### Issue: Encryption Key Not Found

**Symptoms**: `No encryption key found, generating new key`

**Solution**:
1. Generate key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Add to `.env`: `ENCRYPTION_KEY=your_key`
3. OR store in Key Vault: Use Azure Portal

## 💰 Cost Optimization

### Development Environment
- Use Basic tier resources
- Single region deployment
- Smaller storage redundancy (LRS instead of GRS)
- **Estimated cost**: $20-50/month

### Production Environment
- Use Standard tier resources
- Geo-redundant storage
- Enable auto-scaling
- **Estimated cost**: $100-300/month

## 🔒 Security Best Practices

1. **Never commit secrets to Git**
   - Use `.gitignore` for `.env` files
   - Store secrets in Azure Key Vault

2. **Rotate encryption keys regularly**
   - Generate new key every 90 days
   - Re-encrypt existing backups

3. **Enable Azure AD authentication**
   - Use managed identities for production
   - Disable password authentication

4. **Regular security audits**
   - Review access policies monthly
   - Monitor Key Vault access logs

5. **Backup testing**
   - Test restore procedure monthly
   - Verify backup encryption

## 📚 Additional Resources

- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Cryptography Library](https://cryptography.io/en/latest/)

## 🆘 Support

For issues or questions:
- **GitHub Issues**: https://github.com/skakumanu/mew-assistant/issues
- **Documentation**: See main README.md
- **Security Issues**: See SECURITY.md

## ✅ Verification Checklist

Before going to production:

- [ ] Azure CLI installed and logged in
- [ ] Encryption key generated and stored securely
- [ ] Azure Key Vault created and accessible
- [ ] Azure Storage account created
- [ ] Environment variables configured
- [ ] Test backup created successfully
- [ ] Test restore verified
- [ ] Automatic backup schedule configured
- [ ] Backup retention policy configured
- [ ] Monitoring and alerts set up
- [ ] Security audit completed
- [ ] Documentation reviewed and updated

## 🎯 Next Steps

1. **Set up automatic backups** (see Monitoring section)
2. **Configure disaster recovery** (see infrastructure/azure/README.md)
3. **Enable Application Insights** for monitoring
4. **Set up alerts** for failed backups
5. **Test restore procedure** regularly

---

**Note**: This implementation is production-ready with graceful fallbacks. If Azure services are not configured, the app will continue to work using local storage and environment variables.
