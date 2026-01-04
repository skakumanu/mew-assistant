# 📝 Mew Assistant - Changelog

All notable changes to the Mew Assistant project.

---

## [1.0.3] - January 3, 2026

### 🔐 Security & Infrastructure
- **BREAKING CHANGE**: CD workflow now requires credentials in Azure Key Vault
  - Implemented secure credential management for GitHub Actions continuous deployment
  - All application secrets (database, JWT, OAuth) now managed via Azure Key Vault
  - Container App uses Managed Identity for automatic vault authentication
  - Pre-deployment credential verification ensures all required secrets exist
  - Credentials never exposed in GitHub Actions logs or Container App configuration

### ✨ Features
- **Automated Deployment**: GitHub Actions automatically deploys on version tags
  - Staging deployment triggered by pushes to `develop` branch
  - Production deployment triggered by version tags (e.g., `v1.0.3`)
  - Security guardrails (tests, compliance checks) must pass before deployment
  - Pre-deployment validation checks all Key Vault secrets exist
  - Automatic database backups before production deployments
  - Health check verification with auto-rollback on failure

### 📚 Documentation
- **CD Setup Guide**: Comprehensive Azure Key Vault setup instructions ([docs/AZURE_KEYVAULT_CD_SETUP.md](docs/AZURE_KEYVAULT_CD_SETUP.md))
- **Architecture Guide**: Detailed credential flow documentation ([docs/CONTINUOUS_DEPLOYMENT_CREDENTIALS.md](docs/CONTINUOUS_DEPLOYMENT_CREDENTIALS.md))
- **Quick Reference**: Daily reference guide for credential management ([docs/CD_CREDENTIAL_QUICK_REFERENCE.md](docs/CD_CREDENTIAL_QUICK_REFERENCE.md))
- **Implementation Summary**: Complete git flow implementation documentation ([CD_CREDENTIAL_MANAGEMENT_IMPLEMENTATION.md](CD_CREDENTIAL_MANAGEMENT_IMPLEMENTATION.md))

### 🛠️ DevOps
- **Setup Automation**: One-command setup script ([scripts/setup-cd-environment.sh](scripts/setup-cd-environment.sh))
  - Validates all Key Vault secrets
  - Configures Container App Managed Identity
  - Grants proper RBAC roles
  - Reports configuration issues with solutions

### 🔒 Security Enhancements
- Credentials encrypted at rest in Azure Key Vault
- TLS encryption in transit for all secret access
- RBAC-based access control via Managed Identity (no shared passwords)
- Automatic audit logging of all vault access
- Credential rotation without code changes or redeployment
- Pre-deployment validation prevents deployments with missing secrets

### 📋 Requirements
To deploy using this release:
1. Azure Key Vault must contain all required secrets (see setup guide)
2. Container App Managed Identity must have "Key Vault Secrets User" role
3. GitHub Actions secrets must be configured (AZURE_CREDENTIALS, etc.)

---

## [1.0.2] - January 3, 2026

### 🔧 Hotfix
- **Database Connection**: Fixed production database connection issue
  - Removed hardcoded DATABASE_URL from `update-container-probes.ps1`
  - Added `SECRET_KEY` environment variable (required by Pydantic Settings)
  - Recreated Container App with correct PostgreSQL SSL configuration
  - All OAuth credentials properly configured from local .env

### 📚 Documentation
- **Production Recovery**: Added incident documentation ([PRODUCTION_RECOVERY.md](PRODUCTION_RECOVERY.md))
  - Root cause analysis
  - Recovery procedures
  - Prevention measures

---

## [1.0.1] - January 3, 2026

### 🔧 Infrastructure
- **Health Probes**: Added Container App health probe configuration
  - Liveness probe: `/health` endpoint, 30s initial delay, 10s period, 3 failure threshold
  - Readiness probe: `/health` endpoint, 10s initial delay, 5s period, 2 failure threshold
  - Created PowerShell script for automated health probe configuration
- **Database Configuration**: Updated PostgreSQL connection string for production environment

---

## [1.0.0] - January 4, 2026

### ✨ OAuth Authentication 
- **Microsoft OAuth**: Implemented PKCE (Proof Key for Code Exchange) flow for enhanced security
  - Handles both standard and Microsoft-specific field formats (givenname/familyname)
  - Fixed name extraction to support both OpenID Connect and Microsoft AD formats
  - Client registered as Web (confidential) client with proper PKCE integration
- **Google OAuth**: Verified working with full integration
- **Dashboard**: User information display fixed (name, email, role visible after sign-in)
- **Token Management**: Persistent token storage via localStorage with auto-refresh

### 🔧 Azure Container App Deployment
- **Fixed Container Initialization**: Resolved "invalid dsn" error in init-oauth-db.py
  - Script now gracefully skips migration for SQLite (development) databases
  - Added proper error handling for psycopg2 connection failures
  - Removed hardcoded .env.example from Dockerfile (uses Azure environment variables)
- **Database Configuration**: Updated production environment to use PostgreSQL Flexible Server
  - Proper connection pooling and SSL configuration for Azure PostgreSQL
  - Advisory locking to prevent schema creation race conditions
- **Docker Image**: Built and pushed to Azure Container Registry (mewassistantacr)
  - Multi-stage build for optimized image size
  - Proper dependency caching and layer optimization

### 🧪 Testing & Validation
- All 261 tests passing
- OAuth flows tested (Google and Microsoft sign-in)
- Production endpoints responding (/health, /auth/oauth/login)
- Local development verified working with uvicorn

### 🔒 Security & Code Quality
- Removed hardcoded secrets from repository
- GitHub push protection validated (no secrets in commits)
- All environment variables properly externalized for Container Apps

---

## [0.3.0] - December 31, 2025

### 🔒 Security Fixes
- **CRITICAL**: Fixed 6 error-level CodeQL security vulnerabilities
  - 4 log injection vulnerabilities (mobile_integration.py, message.py)
  - 1 clear-text password logging issue (create_superuser.py)
  - 1 XSS vulnerability (onboarding.py)
- All user-controlled data now sanitized before logging
- HTML output properly escaped to prevent XSS attacks

### 🔧 CI/CD Improvements
- Fixed missing environment variables in CI/CD workflows
- Added DATABASE_URL and SECRET_KEY to security guardrails
- Resolved Pydantic Settings validation errors

### 📦 Maintenance
- Applied code formatting fixes across codebase
- Cleaned up 510+ generated artifacts (.coverage, __pycache__, DBs)
- Established git flow workflow (master/develop branches)

---

## [1.1.0] - December 3, 2025

### 📚 Documentation
- Consolidated all deployment docs into `DEPLOYMENT_GUIDE.md`
- Created comprehensive `OAUTH_SETUP.md` for all providers
- Created user-friendly `USER_GUIDE.md` for end users
- Removed outdated/duplicate markdown files

### 🔧 Maintenance
- Cleaned up 15+ redundant documentation files
- Organized guides by audience (developers, admins, users)

---

## [1.0.0] - December 1, 2025

### 🎉 Customer Zero Launch - COMPLETE

### ✅ Features Shipped
- Google OAuth sign-in working end-to-end
- Calendar viewer with read-only access to Google Calendar
- 30-day JWT sessions with automatic refresh
- Browser-based interface (works on all devices)

### 🐛 Critical Bugs Fixed

#### 1. JWT Token Lookup Bug (401 Error)
**Problem:** Token had user ID in `sub` field, but lookup was by email  
**Fix:** Changed to lookup by user ID  
**Files:** `app/utils/auth.py`

#### 2. Missing OAuth Token Columns (500 Error)
**Problem:** Database missing `access_token`, `refresh_token`, `token_expires_at`  
**Fix:** Auto-migration on startup  
**Files:** `app/database/models.py`, `init-oauth-db.py`, `Dockerfile`

#### 3. Calendar API Not Enabled (403 Error)
**Problem:** Google Calendar API not enabled in GCP project  
**Solution:** User enabled API in Google Cloud Console

#### 4. Invalid API Parameters (400 Error)
**Problem:** Sending `timeMin: None` to Calendar API  
**Fix:** Changed to `timeMin: datetime.now(timezone.utc).isoformat()`  
**Files:** `app/integrations/calendar_integration.py`

---

## [0.9.0] - November 23, 2025

### 🚀 Initial Azure Deployment

### Infrastructure
- Deployed to Azure Container Apps
- PostgreSQL Flexible Server provisioned
- Azure Key Vault for secrets management
- Managed identity configured
- Auto-scaling enabled (1-3 replicas)

### Authentication
- Federated authentication system implemented
- Google OAuth configured and stored in Key Vault
- Microsoft OAuth prepared (not yet deployed)
- Apple Sign In prepared (not yet deployed)
- JWT token generation and validation

### Security
- HTTPS-only connections
- Secrets in Azure Key Vault (never in code)
- Rate limiting implemented
- Input validation and sanitization
- CORS properly configured

### Database
- PostgreSQL with all tables created
- User management with RBAC
- OAuth provider linking
- Token storage with encryption

### API Endpoints
- `/health` - Health check
- `/docs` - Interactive API documentation
- `/auth/oauth/login` - OAuth login page
- `/auth/oauth/login/{provider}` - Provider-specific login
- `/auth/oauth/callback/{provider}` - OAuth callback handler
- `/calendar` - Calendar viewer interface

---

## [0.8.0] - November 20, 2025

### Initial Development
- FastAPI application structure
- SQLAlchemy ORM models
- Alembic migrations setup
- Docker containerization
- Basic authentication system
- Calendar integration framework

---

## Legend

- 🎉 Major feature
- ✅ Feature complete
- 🐛 Bug fix
- 🔧 Maintenance
- 🚀 Deployment
- 📚 Documentation
- ⏳ In progress

