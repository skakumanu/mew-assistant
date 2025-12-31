# 📝 Mew Assistant - Changelog

All notable changes to the Mew Assistant project.

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

