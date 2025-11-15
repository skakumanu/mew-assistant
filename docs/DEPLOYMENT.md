# 🚀 Deployment Guide

Complete deployment documentation for the Mew Assistant application.

## Table of Contents
- [Azure Cloud Setup](#azure-cloud-setup)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment Guardrails](#deployment-guardrails)
- [Infrastructure as Code](#infrastructure-as-code)

---

## Azure Cloud Setup

### Prerequisites
- Azure subscription
- Azure CLI installed
- Terraform installed
- kubectl installed

### Infrastructure Components

#### 1. Azure Kubernetes Service (AKS)
- **Purpose**: Container orchestration for scalable deployments
- **Configuration**: Multi-zone deployment for high availability
- **Auto-scaling**: Enabled for dynamic workload management

#### 2. Azure Database for PostgreSQL
- **Type**: Flexible Server
- **Features**:
  - Automated backups (7-day retention)
  - Point-in-time restore
  - Encryption at rest using customer-managed keys
  - Private endpoint connectivity

#### 3. Azure Key Vault
- **Purpose**: Secrets and certificate management
- **Stored Secrets**:
  - Database connection strings
  - API keys (OpenAI, Twilio, SendGrid)
  - JWT signing keys
  - OAuth credentials

#### 4. Azure Blob Storage
- **Purpose**: 
  - Voice recordings storage
  - Daily database backups
  - Log archives
- **Features**:
  - Lifecycle management (30-day retention)
  - Encryption at rest
  - Geo-redundant storage (GRS)

#### 5. Azure API Management
- **Purpose**: API gateway and rate limiting
- **Features**:
  - OAuth2 authentication
  - Rate limiting per user/plan
  - Request/response transformation
  - Analytics and monitoring

#### 6. Azure Application Insights
- **Purpose**: Application performance monitoring
- **Metrics**:
  - Request rates and latencies
  - Error rates and exceptions
  - Custom events and traces
  - User behavior analytics

### Quick Setup

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "Your-Subscription-ID"

# Create resource group
az group create --name mew-assistant-rg --location eastus

# Deploy infrastructure using Terraform
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### Environment Variables for Azure

```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Key Vault
AZURE_KEY_VAULT_NAME=mew-assistant-kv
AZURE_KEY_VAULT_URI=https://mew-assistant-kv.vault.azure.net/

# Storage
AZURE_STORAGE_ACCOUNT=mewassistantstorage
AZURE_STORAGE_CONTAINER=backups

# Database
AZURE_POSTGRES_SERVER=mew-assistant-db.postgres.database.azure.com
AZURE_POSTGRES_DATABASE=mewdb
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### 1. Main CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`

**Jobs:**

##### Security & Compliance Checks
```yaml
- Dependency vulnerability scan (Snyk)
- SAST with Bandit
- Secret scanning
- License compliance check
```

##### Code Quality
```yaml
- Linting (flake8, black)
- Type checking (mypy)
- Code complexity analysis
```

##### Testing
```yaml
- Unit tests (pytest)
- Integration tests
- API contract tests
- Code coverage (minimum 80%)
```

##### Privacy & Security Guardrails
```yaml
- PII detection tests
- COPPA compliance validation
- GDPR data protection checks
- Security headers validation
```

##### Build & Deploy
```yaml
- Build Docker image
- Push to Azure Container Registry
- Deploy to AKS (staging/production)
- Smoke tests
```

#### 2. Dependency Update Workflow

**Schedule:** Weekly on Monday
**Actions:**
- Check for dependency updates
- Create PRs for safe updates
- Run full test suite

#### 3. Backup Workflow

**Schedule:** Daily at 2 AM UTC
**Actions:**
- Database backup to Azure Blob Storage
- Verify backup integrity
- Clean old backups (30-day retention)

### Deployment Environments

#### Staging
- **Purpose**: Pre-production testing
- **URL**: `https://staging.mew-assistant.example.com`
- **Database**: Separate staging database
- **Deployment**: Automatic on merge to `develop`

#### Production
- **Purpose**: Live environment
- **URL**: `https://api.mew-assistant.example.com`
- **Database**: Production database with backups
- **Deployment**: Manual approval required
- **Rollback**: Automatic on failure

### Deployment Process

```bash
# 1. Code is pushed to branch
git push origin feature/new-feature

# 2. PR is created
gh pr create --title "Add new feature" --body "Description"

# 3. CI checks run automatically
# - Security scans
# - Tests
# - Guardrails

# 4. Code review and approval

# 5. Merge to develop
# - Deploys to staging automatically

# 6. Create release PR to main
gh pr create --base main --head develop

# 7. Approval required for production
# - Manual approval in GitHub Actions
# - Deploys to production

# 8. Monitor deployment
kubectl get pods -n mew-assistant
kubectl logs -f deployment/mew-assistant -n mew-assistant
```

---

## Deployment Guardrails

### Pre-Deployment Checks

All checks must pass before production deployment:

#### 1. Security Guardrails ✓
- No high/critical vulnerabilities
- All secrets in Azure Key Vault
- HTTPS enforced
- Security headers configured
- Rate limiting enabled

#### 2. Privacy Guardrails ✓
- PII encryption enabled
- Data retention policies configured
- User consent mechanisms in place
- Privacy policy up-to-date

#### 3. Compliance Guardrails ✓
- COPPA compliance validated
- GDPR requirements met
- Parental consent workflows active
- Audit logging enabled

#### 4. Code Quality Guardrails ✓
- Code coverage ≥ 80%
- All tests passing
- No critical code smells
- Documentation updated

#### 5. Performance Guardrails ✓
- API response time < 500ms (p95)
- Database query optimization
- Caching configured
- Auto-scaling enabled

### Deployment Gates

```yaml
# Example deployment gate in Azure DevOps
gates:
  - task: SecurityCheck
    timeout: 30m
    conditions:
      - vulnerabilities: none
      - secrets_exposed: false
  
  - task: ComplianceCheck
    timeout: 15m
    conditions:
      - coppa_compliant: true
      - gdpr_compliant: true
      - privacy_tests: passed
  
  - task: PerformanceTest
    timeout: 20m
    conditions:
      - response_time_p95: < 500ms
      - error_rate: < 0.1%
```

### Rollback Strategy

**Automatic Rollback Triggers:**
- Error rate > 5%
- Response time > 2s (p95)
- Health check failures
- Database connection issues

**Manual Rollback:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/mew-assistant -n mew-assistant

# Rollback to specific revision
kubectl rollout undo deployment/mew-assistant --to-revision=3 -n mew-assistant

# Check rollout status
kubectl rollout status deployment/mew-assistant -n mew-assistant
```

---

## Infrastructure as Code

### Terraform Structure

```
infrastructure/terraform/
├── main.tf              # Main configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── modules/
│   ├── aks/            # AKS cluster
│   ├── database/       # PostgreSQL
│   ├── storage/        # Blob storage
│   ├── keyvault/       # Key Vault
│   └── monitoring/     # Application Insights
└── environments/
    ├── staging.tfvars
    └── production.tfvars
```

### Kubernetes Manifests

```
infrastructure/k8s/
├── namespace.yaml
├── deployment.yaml
├── service.yaml
├── ingress.yaml
├── configmap.yaml
├── secrets.yaml (sealed)
├── hpa.yaml (Horizontal Pod Autoscaler)
└── networkpolicy.yaml
```

### Helm Charts

```bash
# Install using Helm
helm install mew-assistant ./infrastructure/helm/mew-assistant \
  --namespace mew-assistant \
  --values values-production.yaml
```

---

## Monitoring & Alerts

### Application Insights Dashboards

1. **Overview Dashboard**
   - Request rates
   - Response times
   - Error rates
   - Active users

2. **Performance Dashboard**
   - Database query performance
   - API endpoint latencies
   - Cache hit rates
   - Queue processing times

3. **Security Dashboard**
   - Failed authentication attempts
   - Rate limit violations
   - Suspicious activity patterns
   - PII access logs

### Alert Rules

```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 5%
    window: 5m
    severity: critical
    action: page_on_call
  
  - name: SlowResponseTime
    condition: response_time_p95 > 1s
    window: 10m
    severity: warning
    action: notify_team
  
  - name: DatabaseConnectionIssues
    condition: db_connection_errors > 10
    window: 5m
    severity: critical
    action: auto_scale_and_alert
```

---

## Disaster Recovery

### Backup Strategy

1. **Database Backups**
   - Automated daily backups
   - 7-day retention
   - Point-in-time restore available

2. **Configuration Backups**
   - Terraform state in Azure Storage
   - Kubernetes manifests in Git
   - Secrets in Key Vault

3. **Data Backups**
   - Voice recordings: Geo-redundant storage
   - User data: Daily exports to Blob Storage

### Recovery Procedures

```bash
# 1. Restore database from backup
az postgres flexible-server restore \
  --resource-group mew-assistant-rg \
  --name mew-assistant-db-restored \
  --source-server mew-assistant-db \
  --restore-time "2024-01-15T10:30:00Z"

# 2. Redeploy application
kubectl apply -f infrastructure/k8s/

# 3. Verify health
kubectl get pods -n mew-assistant
curl https://api.mew-assistant.example.com/health
```

---

## Scaling Strategy

### Horizontal Scaling
- Kubernetes HPA based on CPU/memory
- Scale from 2 to 10 pods
- Custom metrics: Request rate, queue depth

### Vertical Scaling
- Database: Resize as needed
- Storage: Auto-expand enabled

### Cost Optimization
- Reserved instances for baseline load
- Spot instances for burst capacity
- Auto-shutdown for non-prod environments

---

## Security Best Practices

1. **Network Security**
   - Private endpoints for database
   - Network policies in Kubernetes
   - WAF for public endpoints

2. **Identity & Access**
   - Managed identities for Azure resources
   - RBAC for Kubernetes
   - Least privilege principle

3. **Data Protection**
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Customer-managed keys in Key Vault

4. **Compliance**
   - Regular security audits
   - Penetration testing
   - Compliance reports (SOC 2, HIPAA-ready)

---

## Troubleshooting

### Common Issues

1. **Pod not starting**
   ```bash
   kubectl describe pod <pod-name> -n mew-assistant
   kubectl logs <pod-name> -n mew-assistant
   ```

2. **Database connection issues**
   ```bash
   # Test connection from pod
   kubectl exec -it <pod-name> -n mew-assistant -- psql $DATABASE_URL
   ```

3. **High latency**
   ```bash
   # Check Application Insights
   az monitor app-insights metrics show \
     --app mew-assistant-insights \
     --metrics requests/duration
   ```

---

## Support & Documentation

- **Azure Support**: https://portal.azure.com/#blade/Microsoft_Azure_Support
- **Kubernetes Docs**: https://kubernetes.io/docs/
- **Terraform Registry**: https://registry.terraform.io/providers/hashicorp/azurerm/latest

**Last Updated**: 2024-11-15
