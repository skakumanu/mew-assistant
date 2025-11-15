# Mew Assistant - Complete System Architecture

> **Version:** 2.0.0 - Enhanced Edition with Compliance, Security & Multi-Platform Support
> 
> **Last Updated:** December 2024
> 
> **Coverage:** Authentication, Privacy Guardrails, Mobile Support, Voice Platforms, Azure Cloud, Parental Controls

## 🏗️ High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          Voice & Mobile Entry Points                                │
├────────────────────────────────────────────────────────────────────────────────────┤
│  🎤 Siri    │  🔊 Alexa   │  🤖 Grok    │  📱 iOS App  │  🤖 Android  │  🌐 Web     │
│  (Shortcuts)│  (Skills)   │  (Commands) │  (Native)    │  (Native)    │  (PWA)      │
└─────────────┬──────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          Voice Processing Layer                                     │
├────────────────────────────────────────────────────────────────────────────────────┤
│  🗣️ Speech Recognition  │  🌍 Auto Language Detection  │  💬 NLU Processing        │
│  (Azure Speech)         │  (150+ Languages)            │  (Intent Recognition)     │
└─────────────┬──────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          External Services Layer                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│  📧 Email    │ 📱 SMS      │ 💬 WhatsApp │ 🤖 AI       │ 📅 Calendars              │
│  (Gmail)     │ (Twilio)    │ (Twilio)    │ (OpenAI/    │ (Google, Apple, Outlook)  │
│              │             │             │  Azure)     │                           │
└─────────────┬───────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          Integration Layer                                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│  EmailIntegration      │  SMSIntegration      │  WhatsAppIntegration               │
│  AIIntegration         │  CalendarIntegration │  VoiceIntegration                  │
│  MobileIntegration     │  SiriIntegration     │  AlexaIntegration                  │
└─────────────┬───────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                        🛡️ Guardrails & Compliance Layer                             │
├────────────────────────────────────────────────────────────────────────────────────┤
│  🔒 Security  │  🛡️ Privacy   │  ⚖️ COPPA    │  🏥 HIPAA    │  🌍 GDPR             │
│  Guardrails   │  Protection  │  Compliance  │  Compliance  │  Compliance          │
│               │              │  (<13 years) │  (Health)    │  (EU Privacy)        │
└─────────────┬───────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          Service Layer                                              │
├────────────────────────────────────────────────────────────────────────────────────┤
│  SessionService       │  MessageService      │  SummaryService                     │
│  AuthService          │  ScheduleService     │  ParentalApprovalService            │
│  VoiceService         │  LanguageService     │  MobileCalendarService              │
└─────────────┬───────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          API Router Layer                                           │
├────────────────────────────────────────────────────────────────────────────────────┤
│  /auth/*          │  /mew/*         │  /webhooks/*      │  /voice/*                │
│  Authentication   │  Core APIs      │  External         │  Voice Commands          │
│                   │                 │  Webhooks         │                          │
│  /mobile/*        │  /approval/*    │  /calendar/*      │  /kids/*                 │
│  Mobile Sync      │  Parental       │  Calendar         │  Kid Requests            │
│                   │  Approval       │  Integration      │                          │
└─────────────┬───────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          Middleware Layer                                           │
├────────────────────────────────────────────────────────────────────────────────────┤
│  CORS         │  Request ID    │  Exception Handler  │  Structured Logging         │
│  Compliance   │  Rate Limiting │  Audit Trail        │  Privacy Filters            │
└─────────────┬───────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Application                                        │
└────────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          Database Layer (Encrypted at Rest)                         │
├────────────────────────────────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM  │  Models  │  Audit Logs  │  Encrypted Fields  │  Backups         │
└─────────────┬───────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          Azure Cloud Infrastructure                                 │
├────────────────────────────────────────────────────────────────────────────────────┤
│  🗄️ PostgreSQL      │  🔐 Key Vault       │  💾 Blob Storage    │  📊 Monitoring    │
│  (Flexible Server)  │  (Secrets Mgmt)     │  (Backups/Files)    │  (App Insights)   │
│                     │                     │                     │                   │
│  🌐 Container Apps  │  🔒 Private Network │  🚀 Auto-Scaling    │  🔄 Load Balancer │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Structure

```
mew-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   │
│   ├── routers/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication & registration
│   │   ├── session.py              # Session management
│   │   ├── message.py              # Message ingestion
│   │   ├── summary.py              # Summary generation
│   │   ├── webhooks.py             # External webhooks
│   │   ├── voice.py                # Voice command endpoints
│   │   ├── mobile.py               # Mobile calendar sync
│   │   ├── approval.py             # Parental approval workflow
│   │   └── kids.py                 # Kid-friendly interface
│   │
│   ├── services/                   # Business logic
│   │   ├── __init__.py
│   │   ├── session_service.py
│   │   ├── message_service.py
│   │   ├── summary_service.py
│   │   ├── parental_approval_service.py
│   │   ├── voice_service.py
│   │   └── mobile_calendar_service.py
│   │
│   ├── integrations/               # External services
│   │   ├── __init__.py
│   │   ├── email_integration.py
│   │   ├── sms_integration.py
│   │   ├── whatsapp_integration.py
│   │   ├── ai_integration.py
│   │   ├── calendar_integration.py
│   │   ├── voice_integration.py
│   │   ├── siri_integration.py
│   │   ├── alexa_integration.py
│   │   └── mobile_integration.py
│   │
│   ├── database/                   # Database layer
│   │   ├── __init__.py
│   │   ├── models.py               # All database models
│   │   └── session.py              # DB session management
│   │
│   ├── schemas/                    # Pydantic models
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── approval.py
│   │   ├── voice.py
│   │   └── mobile.py
│   │
│   ├── utils/                      # Utilities
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration management
│   │   ├── logger.py               # Structured logging
│   │   ├── cooldown.py             # Cooldown detection
│   │   ├── priority.py             # Priority period logic
│   │   ├── privacy.py              # Privacy utilities (PII masking)
│   │   └── security.py             # Security helpers
│   │
│   └── middleware/                 # Custom middleware
│       ├── __init__.py
│       ├── exception_handler.py    # Global exception handling
│       ├── compliance.py           # Compliance checks (COPPA/HIPAA/GDPR)
│       └── audit.py                # Audit logging
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── test_auth.py
│   ├── test_sessions.py
│   ├── test_integrations.py
│   ├── test_privacy_guardrails.py
│   ├── test_parental_approval.py
│   ├── test_voice_commands.py
│   │
│   ├── security/                   # Security tests
│   │   ├── test_authentication.py
│   │   ├── test_authorization.py
│   │   └── test_input_validation.py
│   │
│   └── compliance/                 # Compliance tests
│       ├── test_coppa_compliance.py
│       ├── test_hipaa_compliance.py
│       └── test_gdpr_compliance.py
│
├── infrastructure/                 # Cloud infrastructure
│   ├── azure/
│   │   ├── main.bicep              # Azure infrastructure as code
│   │   ├── app.bicep
│   │   ├── database.bicep
│   │   ├── storage.bicep
│   │   └── keyvault.bicep
│   └── scripts/
│       ├── deploy.sh
│       └── backup.sh
│
├── docs/                           # Documentation
│   └── integrations/
│       └── SETUP_GUIDE.md
│
├── agent-cards/                    # AGNTCY agent cards
│   ├── scheduler.yaml
│   ├── tutor.yaml
│   └── caregiver.yaml
│
├── .github/                        # CI/CD
│   └── workflows/
│       ├── ci.yml                  # Continuous Integration
│       ├── cd.yml                  # Continuous Deployment (with guardrails)
│       ├── security-scan.yml
│       ├── tests.yml
│       └── dependency-update.yml
│
├── .env.example                    # Environment template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── podman-start.sh
├── podman-stop.sh
├── podman-full.sh
├── test_integrations.sh
├── ARCHITECTURE.md                 # This file
├── PRIVACY.md                      # Privacy policy
├── SECURITY.md                     # Security documentation
├── COMPLIANCE.md                   # Compliance details
└── README.md                       # Main documentation
```

---

## 🔄 Request Flow

### 1. Voice Command Flow (Multi-Platform)

```
User speaks to device (Siri/Alexa/Grok)
    ↓
Platform captures audio
    ↓
Platform webhook → /voice/siri|alexa|grok
    ↓
VoiceService.process_command()
    ↓
Azure Speech API (speech-to-text)
    ↓
Auto language detection (150+ languages)
    ↓
AIIntegration.analyze_intent()
    ↓
Route to handler:
    - Schedule request
    - Question/Query
    - Calendar lookup
    - Kid request (→ parental approval)
    ↓
Generate response
    ↓
Text-to-speech (if voice response)
    ↓
Send back to platform
    ↓
User hears response
```

### 2. Kid Request with Parental Approval Flow

```
Kid makes request (voice/mobile/SMS)
    ↓
KidsRouter validates request
    ↓
Check if kid profile exists
    ↓
Create ParentalApprovalRequest
    - Status: pending
    - Priority: determined by rules
    ↓
Notify parent:
    - Push notification (mobile)
    - SMS (urgent)
    - Email (digest)
    ↓
Parent reviews request:
    - Approve/Deny/Modify
    - Set future auto-approval rule (optional)
    ↓
Update request status
    ↓
If approved:
    ↓
    Execute original request
    ↓
    Notify kid of approval
Else:
    ↓
    Notify kid with reason
```

### 3. Intelligent Auto-Approval Flow

```
New kid request arrives
    ↓
Check auto-approval rules:
    - Time-based rules (homework time, bedtime)
    - Category rules (educational content)
    - Recurring patterns (weekly tutoring)
    - Trust level (earned privileges)
    ↓
Match found?
    ↓
YES:
    Auto-approve request
    Send parent notification (FYI)
    Execute request
    ↓
NO:
    Route to manual approval
    Add to parent's review queue
    Apply batching if non-urgent
```

### 4. Mobile Calendar Sync Flow

```
Mobile app (iOS/Android)
    ↓
Authenticate with OAuth2
    ↓
GET /mobile/calendar/sync
    ↓
MobileCalendarService.sync()
    ↓
Fetch from:
    - Apple Calendar (iOS)
    - Google Calendar (Android)
    - Outlook Calendar (both)
    ↓
Merge with Mew's schedule
    ↓
Detect conflicts
    ↓
Apply smart resolution:
    - Priority-based
    - User preferences
    - Conflict notifications
    ↓
Push updates to device
    ↓
Background sync (every 15 min)
```

```
User sends SMS/WhatsApp
    ↓
Twilio receives message
    ↓
Twilio webhook → /webhooks/sms/incoming
    ↓
Webhook router parses request
    ↓
MessageService.process_incoming_message()
    ↓
AIIntegration.analyze_message() (intent detection)
    ↓
Route to appropriate handler:
    - Schedule request
    - Reminder request
    - Question
    - Report request
    ↓
Generate response
    ↓
Return TwiML response
    ↓
Twilio sends reply to user
```

### 2. API Request Flow

```
Client → POST /mew/ingest
    ↓
CORS Middleware
    ↓
Request ID Middleware
    ↓
JWT Authentication (if required)
    ↓
Router validates request (Pydantic)
    ↓
Service layer processes
    ↓
Database operations (if needed)
    ↓
Integration calls (if needed)
    ↓
Response serialization
    ↓
Exception handling
    ↓
JSON response to client
```

### 3. Summary Generation Flow

```
Scheduled task / API call
    ↓
GET /mew/summary?user_id=123
    ↓
SummaryService.generate_summary()
    ↓
Fetch activities from database
    ↓
AIIntegration.generate_summary()
    ↓
Format and structure summary
    ↓
Store in database
    ↓
Send notifications:
    - EmailIntegration.send_notification()
    - SMSIntegration.send_summary()
    - WhatsAppIntegration.send_summary()
    ↓
Return summary to client
```

---

## 🔐 Security Layers

```
┌────────────────────────────────────────┐
│  1. HTTPS/TLS (Transport Layer)        │
│     - End-to-end encryption            │
│     - Certificate pinning (mobile)     │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  2. CORS (Cross-Origin Protection)     │
│     - Whitelist approved domains       │
│     - Credentials handling             │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  3. JWT Authentication                 │
│     - Token rotation                   │
│     - Refresh token mechanism          │
│     - Device fingerprinting            │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  4. Input Validation (Pydantic)        │
│     - Schema validation                │
│     - XSS prevention                   │
│     - SQL injection protection         │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  5. Rate Limiting                      │
│     - Per-user limits                  │
│     - IP-based limits                  │
│     - Endpoint-specific limits         │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  6. Database Access Control            │
│     - Role-based access (RBAC)         │
│     - Row-level security               │
│     - Encrypted at rest                │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  7. Privacy Guardrails                 │
│     - PII detection & masking          │
│     - Auto-redaction in logs           │
│     - Data minimization                │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  8. Compliance Middleware              │
│     - COPPA age verification           │
│     - HIPAA audit trails               │
│     - GDPR consent management          │
└────────────────────────────────────────┘
```

## 🛡️ Guardrails & Compliance Framework

### Security Guardrails

```python
# Enforced on every request
✅ Authentication validation
✅ Authorization checks (RBAC)
✅ Input sanitization
✅ Output encoding
✅ SQL injection prevention
✅ XSS protection
✅ CSRF tokens
```

### Privacy Guardrails

```python
# Automatic PII protection
✅ Email masking (u***@example.com)
✅ Phone number masking (***-***-1234)
✅ SSN detection & blocking
✅ Credit card pattern detection
✅ Address redaction in logs
✅ Name anonymization (optional)
```

### Compliance Checks

#### COPPA (Children's Online Privacy Protection Act)
- ✅ Age verification (<13 years)
- ✅ Parental consent required
- ✅ No targeted advertising
- ✅ Data minimization
- ✅ Secure data deletion on request
- ✅ Transparent privacy practices

#### HIPAA (Health Insurance Portability and Accountability Act)
- ✅ Audit logging (all health data access)
- ✅ Encryption in transit and at rest
- ✅ Access controls and authentication
- ✅ Breach notification procedures
- ✅ Business associate agreements
- ✅ Minimum necessary access

#### GDPR (General Data Protection Regulation)
- ✅ Right to access (data export)
- ✅ Right to be forgotten (deletion)
- ✅ Right to rectification
- ✅ Data portability
- ✅ Consent management
- ✅ Privacy by design

---

## 💾 Database Schema (Enhanced)

```
┌─────────────────────┐        ┌──────────────────────┐
│       Users         │        │   ParentalApproval   │
├─────────────────────┤        ├──────────────────────┤
│ id (PK)             │◄──────┐│ id (PK)              │
│ email (encrypted)   │       ││ parent_id (FK)       │
│ hashed_password     │       ││ kid_id (FK)          │
│ full_name           │       ││ request_type         │
│ phone (encrypted)   │       ││ request_data (JSON)  │
│ role (parent/kid)   │       ││ status               │
│ parent_id (FK/null) │       ││ priority             │
│ age (encrypted)     │       ││ auto_approved        │
│ created_at          │       ││ approved_at          │
│ is_active           │       ││ expires_at           │
│ consent_given       │       │└──────────────────────┘
│ last_login          │       │
└─────────────────────┘       │┌──────────────────────┐
           │                  ││  AutoApprovalRules   │
           │                  │├──────────────────────┤
           │                  └┤ id (PK)              │
           │                   │ parent_id (FK)       │
           ▼                   │ kid_id (FK)          │
┌─────────────────────┐        │ rule_type            │
│     Sessions        │        │ conditions (JSON)    │
├─────────────────────┤        │ is_active            │
│ id (PK)             │        │ created_at           │
│ user_id (FK)        │        └──────────────────────┘
│ session_type        │
│ status              │        ┌──────────────────────┐
│ scheduled_at        │        │   VoiceCommands      │
│ completed_at        │        ├──────────────────────┤
│ metadata (JSON)     │        │ id (PK)              │
└─────────────────────┘        │ user_id (FK)         │
           │                   │ platform             │
           │                   │ original_audio_url   │
           ▼                   │ transcription        │
┌─────────────────────┐        │ detected_language    │
│      Messages       │        │ intent               │
├─────────────────────┤        │ confidence_score     │
│ id (PK)             │        │ processed_at         │
│ user_id (FK)        │        └──────────────────────┘
│ session_id (FK)     │
│ channel             │        ┌──────────────────────┐
│ content (encrypted) │        │  MobileCalendarSync  │
│ direction           │        ├──────────────────────┤
│ pii_detected        │        │ id (PK)              │
│ created_at          │        │ user_id (FK)         │
└─────────────────────┘        │ device_id            │
                               │ platform             │
┌─────────────────────┐        │ calendar_provider    │
│    AuditLogs        │        │ last_sync_at         │
├─────────────────────┤        │ sync_token           │
│ id (PK)             │        │ status               │
│ user_id (FK)        │        └──────────────────────┘
│ action              │
│ resource_type       │        ┌──────────────────────┐
│ resource_id         │        │   ConsentRecords     │
│ ip_address          │        ├──────────────────────┤
│ user_agent          │        │ id (PK)              │
│ success             │        │ user_id (FK)         │
│ error_message       │        │ consent_type         │
│ created_at          │        │ granted              │
└─────────────────────┘        │ version              │
                               │ ip_address           │
                               │ granted_at           │
                               │ revoked_at           │
                               └──────────────────────┘
```

### Key Schema Features

- 🔐 **Encrypted Fields**: Email, phone, age, message content
- 🔍 **PII Detection**: Auto-flagging in messages
- 📊 **Audit Trails**: Complete HIPAA-compliant logging
- 👨‍👩‍👧‍👦 **Family Relationships**: Parent-kid linkage
- ✅ **Consent Management**: GDPR-compliant consent tracking
- 🗣️ **Voice Integration**: Platform-specific command tracking
- 📱 **Mobile Sync**: Cross-platform calendar state

---

## 🚀 Deployment Options

### Option 1: Local Development

```bash
# PostgreSQL in Podman
./podman-start.sh

# App locally
uvicorn app.main:app --reload
```

### Option 2: Full Podman Stack

```bash
# Everything in containers
./podman-full.sh
```

### Option 3: Cloud Deployment

```bash
# Deploy to cloud with managed PostgreSQL
# Set environment variables
# Run: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 📊 Performance Characteristics

| Component           | Latency      | Scalability         |
|---------------------|--------------|---------------------|
| Auth endpoints      | < 100ms      | Horizontal          |
| Session CRUD        | < 50ms       | Horizontal          |
| Message ingestion   | < 200ms      | Horizontal          |
| AI summary          | 2-5s         | Queue-based         |
| Webhook processing  | < 500ms      | Async workers       |
| Database queries    | < 50ms       | Connection pooling  |

---

## 🔧 Configuration Management

```
Environment Variables (.env)
    ↓
app/utils/config.py (Settings)
    ↓
Injected into services/integrations
    ↓
Runtime configuration
```

**Priority:**
1. Environment variables
2. .env file
3. Default values in code

---

## 📈 Monitoring & Observability

```
Application
    ↓
Structured Logging (logger.py)
    ↓
stdout/stderr
    ↓
Log Aggregation (optional: ELK, Datadog)
    ↓
Dashboards & Alerts
```

**Logged Events:**
- HTTP requests/responses
- Database operations
- Integration API calls
- Error stack traces
- Performance metrics

---

## 🧪 Testing Strategy

```
Unit Tests
    ↓
Integration Tests
    ↓
API Tests
    ↓
End-to-End Tests
```

**Coverage:**
- Routers: Request/response validation
- Services: Business logic
- Integrations: External API mocking
- Database: Model operations

---

## 🔄 CI/CD Pipeline with Guardrail Gates

```
git push (to main/master)
    ↓
┌─────────────────────────────────────────┐
│  🛡️ MANDATORY GUARDRAIL GATES           │
│  (MUST PASS to proceed)                 │
├─────────────────────────────────────────┤
│  ✅ Security Guardrails                 │
│  ✅ Privacy Guardrails                  │
│  ✅ COPPA Compliance                    │
│  ✅ HIPAA Compliance                    │
│  ✅ GDPR Compliance                     │
│  ✅ Secrets Detection                   │
│  ✅ Parental Approval Logic             │
└─────────────┬───────────────────────────┘
              │
              ▼ (All guardrails passed)
┌─────────────────────────────────────────┐
│  CI Checks                              │
├─────────────────────────────────────────┤
│  ├─ Linting (flake8, black, isort)     │
│  ├─ Type checking (mypy)               │
│  ├─ Unit tests (pytest)                │
│  ├─ Integration tests                  │
│  ├─ Security scan (bandit, safety)     │
│  └─ Code coverage (>80%)               │
└─────────────┬───────────────────────────┘
              │
              ▼
Build container image
    ↓
Push to Azure Container Registry
    ↓
┌─────────────────────────────────────────┐
│  Deploy to Staging                      │
├─────────────────────────────────────────┤
│  - Azure Container Apps                 │
│  - Auto-scaling enabled                 │
│  - Health checks                        │
└─────────────┬───────────────────────────┘
              │
              ▼
Smoke tests on staging
    ↓
Manual approval for production
    ↓
┌─────────────────────────────────────────┐
│  Deploy to Production                   │
├─────────────────────────────────────────┤
│  - Database backup first                │
│  - Blue-green deployment                │
│  - Health checks                        │
│  - Rollback on failure                  │
└─────────────────────────────────────────┘
```

### Deployment Blocking Criteria

**❌ Deployment BLOCKED if:**
- Any security guardrail fails
- Any privacy guardrail fails
- COPPA compliance check fails
- HIPAA compliance check fails
- GDPR compliance check fails
- High-severity security issues found
- Parental approval logic broken
- Code coverage < 80%
- Critical tests failing

**⚠️ Deployment WARNED but proceeds if:**
- Low-severity dependency vulnerabilities
- Linting warnings (not errors)
- Documentation outdated

---

## 🌐 Azure Cloud Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Azure Front Door (CDN)                     │
│  - Global load balancing                                     │
│  - SSL termination                                           │
│  - WAF (Web Application Firewall)                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│            Azure Container Apps (Auto-scaling)               │
│  - Min instances: 2                                          │
│  - Max instances: 10                                         │
│  - Scale trigger: CPU > 70% or Memory > 80%                  │
└─┬──────────────────────┬──────────────────────────┬──────────┘
  │                      │                          │
  ▼                      ▼                          ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐
│  PostgreSQL  │  │  Key Vault   │  │   Blob Storage          │
│  Flexible    │  │  - Secrets   │  │   - Backups             │
│  Server      │  │  - API keys  │  │   - Encrypted files     │
│  - Encrypted │  │  - Certs     │  │   - Audit logs          │
└──────────────┘  └──────────────┘  └─────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│           Azure Monitor & Application Insights                │
│  - Performance metrics                                        │
│  - Error tracking                                             │
│  - Usage analytics                                            │
│  - Alerts & notifications                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Design Principles (Updated)

1. **Security First**: Defense in depth with multiple layers
2. **Privacy by Design**: PII protection built into every layer
3. **Compliance by Default**: COPPA, HIPAA, GDPR enforced automatically
4. **Modularity**: Clear separation of concerns
5. **Extensibility**: Easy to add new integrations & platforms
6. **Reliability**: Graceful degradation, auto-recovery
7. **Observability**: Comprehensive logging & monitoring
8. **Performance**: Async operations, caching, auto-scaling
9. **Maintainability**: Clean code, extensive documentation
10. **Kid-Friendly**: Designed for special needs families

---

## 📊 Performance & Scalability

| Component               | Latency      | Throughput    | Scalability         |
|-------------------------|--------------|---------------|---------------------|
| Auth endpoints          | < 100ms      | 1000 req/s    | Horizontal          |
| Voice commands          | < 500ms      | 500 req/s     | Horizontal          |
| Session CRUD            | < 50ms       | 2000 req/s    | Horizontal          |
| Message ingestion       | < 200ms      | 1500 req/s    | Horizontal          |
| AI summary              | 2-5s         | 100 req/s     | Queue-based         |
| Mobile calendar sync    | < 300ms      | 800 req/s     | Horizontal          |
| Parental approval       | < 100ms      | 500 req/s     | Horizontal          |
| Webhook processing      | < 500ms      | 1000 req/s    | Async workers       |
| Database queries        | < 50ms       | 5000 req/s    | Connection pooling  |
| Azure auto-scaling      | 30-60s       | N/A           | 2-10 instances      |

---

## 🌍 Multi-Language Support

**Supported Languages**: 150+ languages with auto-detection

### Top-Tier Languages (Optimized):
- English (US, UK, AU, CA)
- Spanish (ES, MX, AR)
- French (FR, CA)
- German
- Mandarin Chinese
- Japanese
- Korean
- Portuguese (BR, PT)
- Italian
- Russian
- Arabic
- Hindi

### Voice Platform Compatibility:
- ✅ Siri: 40+ languages
- ✅ Alexa: 30+ languages
- ✅ Grok: Auto-detection (all supported)
- ✅ Google Assistant: 40+ languages

---

**Last Updated**: December 2024  
**Version**: 2.0.0  
**Phase**: All guardrails, compliance, voice platforms, and Azure cloud complete
