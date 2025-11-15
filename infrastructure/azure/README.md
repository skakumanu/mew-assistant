# Azure Cloud Infrastructure

Infrastructure as Code for deploying Mew Assistant to Azure.

## Features

- **Azure Key Vault**: Secure secret management
- **Azure Blob Storage**: Encrypted backups with geo-redundancy
- **Encryption at Rest**: All data encrypted using AES-128

## Quick Start

### 1. Azure Login
```bash
az login
```

### 2. Deploy Infrastructure
```bash
./infrastructure/azure/scripts/deploy.sh dev
```

### 3. Configure Application
Add to `.env`:
```bash
AZURE_KEY_VAULT_URL=<from terraform output>
AZURE_STORAGE_CONNECTION_STRING=<from terraform output>
ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
```

## Backup API

### Create Backup
```bash
curl -X POST http://localhost:8000/api/backup/create \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Backups
```bash
curl http://localhost:8000/api/backup/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Restore Backup
```bash
curl -X POST http://localhost:8000/api/backup/restore \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_name": "backup_20240101_120000.db.enc"}'
```

## Security

- All backups encrypted before upload
- Secrets stored in Azure Key Vault
- Geo-redundant storage for disaster recovery
- Automatic cleanup of old backups
