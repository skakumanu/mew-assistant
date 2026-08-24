# 📝 Mew Assistant - Changelog

All notable changes to the Mew Assistant project.

---

## [Unreleased]

### ✨ Features
- **Three-persona scheduling**: one schedule shared by a caregiver, a kid and a service provider
  - Deterministic rule engine ([app/services/rule_engine.py](app/services/rule_engine.py)) evaluates every change request before it can reach a caregiver — a request that fits the declared rules is applied immediately, never queued behind a confidence score
  - A rule failure is a stable reason code, never a sentence, so one parked request reads correctly in any language
  - `POST /requests` is the only write path for kid and provider; no client decides what is allowed
  - A parked request arrives as one card with three compliant alternatives attached, approved in one tap via `POST /parent/approvals/{id}/choose`
  - Auto-applied changes land in a quiet log ("Handled for you") instead of a notification
- **Service provider persona**: `ProviderOrg` / `ProviderPerson`, with `GET /provider/sessions` scoped to the caller's own organisation
- **Caregiver screens**: `/app/parent`, `/app/kid` and `/app/provider`, built from the design's tokens
- **Parent and guardian are interchangeable**: both route prefixes, both accepted values, one permission check, and a per-family choice of which word is shown
- **Voice**: `POST /voice/requests` reads a spoken request back before sending it, and can never approve

### ♻️ Changed
- `/kid/change-request` applies a compliant request instead of always creating a pending approval; cancellations still reach the caregiver when `cancellation_needs_approval` is on
- `/parent/approvals/pending` gained `reason_codes` and `alternatives` (existing fields unchanged)
- Kid-facing copy replaced with plain sentences and 56px targets; the sticker collection maps onto a "calm days in a row" streak

### 🔌 Integrations
- **Calendars are real**: sessions are mirrored in from Google (per-user OAuth) or any ICS feed — which is how Apple, Calendly and most clinic and school booking tools publish — and approved changes are written back as invite updates
  - Idempotent pull matched on `external_event_id`; Mew stays authoritative, and an unreachable or read-only calendar never undoes an applied change
  - Dependency-free ICS parser: folded lines, escaped text, `DURATION` without `DTEND`, `STATUS:CANCELLED`
- **Notifications reach people**: stored as a locale key plus parameters, then delivered by email/SMS best effort, so a kid's outcome survives the session moving off today and every channel says the same sentence ([GET /notifications](app/routers/notifications.py))
- **Setup in one call**: `POST /onboarding/setup` creates the child, the rules, the provider organisations and their therapists, and pulls their calendars — idempotent, so a half-finished setup can be re-sent
- **Sign-in on the screens**: an HttpOnly session cookie replaces the pasted bearer token; `get_current_user` accepts either, and an API `Authorization` header still wins

### 🔧 Fixed
- **`SmartApprovalService` was entirely dead** — it imported a module that does not exist and referenced ten attributes absent from the models, so every method would have raised. Rewritten against the real schema and sequenced *behind* the deterministic engine: it advises on already-parked requests and batches what is waiting, and can never override a declared rule

### 🌍 Internationalisation
- UI locale resolves from `Accept-Language` or an explicit per-user choice, never from the content of a message
- One file per locale with `en.json` as the contract, enforced by tests; ships en/es/hi/ar
- **`hi` and `ar` are unreviewed machine-quality translations and need a native speaker before shipping** ([app/locales/README.md](app/locales/README.md))

### ♿ Accessibility
- No information in a single channel: every banner also reaches the live region as the same sentence
- Status is never colour alone; touch targets never shrink responsively; 200% text without horizontal scroll
- `prefers-reduced-motion` disables all motion
- AAC symbols are plain glyphs — real symbol sets (PCS, ARASAAC, Bliss) need licensed artwork

### 🗄️ Database
- New tables: `provider_orgs`, `provider_people`, `scheduled_sessions`, `rule_sets`, `protected_blocks`, `weekly_caps`, `change_log_entries`, `user_locales`
- `approval_requests` gained `requested_by`, `provider_org_id`, `change_kind`, `scheduled_session_id`, `new_start_utc`, `new_provider_person_id`, `reason_codes`, `alternatives`, `auto_applied`, `chosen_alternative_index`
- Idempotent migration ([scripts/migrate_three_persona_scheduling.py](scripts/migrate_three_persona_scheduling.py)) seeds a `RuleSet` per caregiver from existing `ApprovalRule` rows

### 📚 Documentation
- **Implementation guide**: the loop, the API surface, the locked reason codes and what was reused versus changed ([docs/THREE_PERSONA_SCHEDULING.md](docs/THREE_PERSONA_SCHEDULING.md))

### 🧪 Tests
- 178 new tests across the rule engine (100% covered), the loop end to end, the locale contract, rule-set backfill, caregiver-term interchangeability, calendar ingest and write-back, notification delivery, the smart-approval boundary, onboarding and sign-in

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

