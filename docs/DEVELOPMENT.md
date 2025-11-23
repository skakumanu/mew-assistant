# Mew Assistant - Development Guide

## Table of Contents
1. [Architecture](#architecture)
2. [Contributing Guidelines](#contributing-guidelines)
3. [Git Flow](#git-flow)
4. [Testing](#testing)
5. [AI Scheduler](#ai-scheduler)
6. [Security & Compliance](#security--compliance)

---

# Mew Assistant - Complete System Architecture

> **Version:** 3.0.0 - Production Edition with AI Scheduler, Voice Integration & Complete Azure Deployment
> 
> **Last Updated:** November 2024
> 
> **Coverage:** Voice Assistants (Siri/Alexa/Grok), AI-Powered Scheduling, Mobile Apps (iOS/Android), Calendar Integration, Parental Controls, Azure Cloud Infrastructure, Complete Compliance & Security

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

**Last Updated**: November 2024  
**Version**: 3.0.0  
**Phase**: Production-ready with AI Scheduler, Voice Integration, Mobile Apps, and Azure Cloud

---

## 🤖 AI Scheduler - Smart Schedule Management

The AI Scheduler is the core intelligence of Mew Assistant, providing automated conflict detection, pattern learning, and smart suggestions for special needs families.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AI Scheduler Engine                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Pattern Learning & Analysis                      │   │
│  │  ─────────────────────────────────────────────       │   │
│  │  • Historical schedule data                          │   │
│  │  • User preferences & behaviors                      │   │
│  │  • Success/failure tracking                          │   │
│  │  • Seasonal/weekly patterns                          │   │
│  │  • Family member availability                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  2. Conflict Detection Engine                        │   │
│  │  ────────────────────────────────────────           │   │
│  │  • Time overlaps detection                           │   │
│  │  • Resource conflicts (therapist, room, etc.)        │   │
│  │  • Transportation logistics                          │   │
│  │  • Caregiver availability                            │   │
│  │  • Energy/fatigue level considerations               │   │
│  │  • Special needs requirements                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  3. Smart Suggestion Generator                       │   │
│  │  ──────────────────────────────────────────         │   │
│  │  • Optimal time slot suggestions                     │   │
│  │  • Alternative scheduling options                    │   │
│  │  • Priority-based recommendations                    │   │
│  │  • Buffer time calculations                          │   │
│  │  • Travel time estimation                            │   │
│  │  • Energy management suggestions                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  4. Auto-Optimization (with Parental Controls)       │   │
│  │  ────────────────────────────────────────────────   │   │
│  │  • Auto-approve low-risk changes                     │   │
│  │  • Batch requests for parent review                  │   │
│  │  • Emergency/urgent handling                         │   │
│  │  • Learning from approval/denial patterns            │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Core Features

#### 1. **Pattern Learning**

The AI learns from historical data:

```python
# Example: Learning preferred therapy times
{
  "occupational_therapy": {
    "preferred_times": ["10:00 AM - 11:00 AM", "2:00 PM - 3:00 PM"],
    "avoid_times": ["early morning", "late evening"],
    "optimal_days": ["Tuesday", "Thursday"],
    "success_rate": 0.92,
    "energy_correlation": "high in morning, moderate afternoon"
  },
  "speech_therapy": {
    "preferred_times": ["11:00 AM - 12:00 PM"],
    "buffer_after_other_activities": 30,  # minutes
    "success_rate": 0.88
  }
}
```

#### 2. **Conflict Detection**

Multi-dimensional conflict analysis:

```python
conflict_types = [
    "time_overlap",           # Direct time conflicts
    "resource_conflict",      # Same therapist/room needed
    "transportation",         # Travel time conflicts
    "caregiver_unavailable",  # Parent/caregiver not available
    "energy_level",           # Too many activities in one day
    "meal_time",              # Conflicts with meal schedules
    "medication_time",        # Conflicts with medication schedule
    "sensory_overload",       # Too many high-stimulation activities
    "routine_disruption"      # Changes to established routines
]
```

#### 3. **Smart Suggestions**

Context-aware recommendations:

```python
{
  "suggestion_id": "sug_abc123",
  "type": "reschedule",
  "current_slot": "2024-11-25 09:00 AM",
  "suggested_slots": [
    {
      "time": "2024-11-25 10:30 AM",
      "score": 0.95,
      "reasoning": [
        "No conflicts detected",
        "Historically successful time",
        "Good energy level expected",
        "Preferred therapist available",
        "15-min buffer after breakfast"
      ],
      "impact": "low"  # low/medium/high
    },
    {
      "time": "2024-11-26 10:00 AM",
      "score": 0.87,
      "reasoning": [
        "Different day, better spacing",
        "Consistent with weekly pattern"
      ],
      "impact": "medium"
    }
  ],
  "confidence": 0.92
}
```

#### 4. **Auto-Approval Logic**

Smart parental control system:

```python
# Auto-approval rules (customizable per family)
auto_approve_rules = {
    "time_shift": {
        "max_minutes": 30,        # Auto-approve shifts ≤ 30 min
        "same_day_only": True
    },
    "low_priority_activities": {
        "auto_approve": True,
        "notify_parent": True
    },
    "minor_adjustments": {
        "therapist_change": False,  # Always require approval
        "location_change": False,   # Always require approval
        "duration_change": 15       # ≤15 min auto-approve
    },
    "emergency_override": {
        "enabled": True,
        "notify_immediately": True
    }
}

# Batching rules (reduce approval fatigue)
batching_rules = {
    "batch_window": "24_hours",      # Collect for 24h
    "max_batch_size": 5,             # Max 5 items per batch
    "priority_threshold": "medium",  # High priority → immediate
    "digest_time": "8:00 PM"        # Send daily digest
}
```

### Implementation Details

#### Database Schema

```python
# app/database/models.py additions

class SchedulePattern(Base):
    __tablename__ = "schedule_patterns"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String(100))
    preferred_times = Column(JSON)  # List of time slots
    success_rate = Column(Float)
    energy_correlation = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow)

class ConflictDetection(Base):
    __tablename__ = "conflict_detections"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_1_id = Column(String(100))
    event_2_id = Column(String(100))
    conflict_type = Column(String(50))
    severity = Column(String(20))  # low, medium, high, critical
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolution = Column(JSON)

class ScheduleSuggestion(Base):
    __tablename__ = "schedule_suggestions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_event = Column(JSON)
    suggested_slots = Column(JSON)
    confidence_score = Column(Float)
    reasoning = Column(JSON)
    status = Column(String(20))  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### API Endpoints

```python
# app/services/ai_scheduler_service.py

class AISchedulerService:
    """AI-powered schedule optimization service"""
    
    async def detect_conflicts(self, user_id: int, new_event: dict) -> List[Conflict]:
        """Detect all potential conflicts"""
        
    async def generate_suggestions(self, conflict: Conflict) -> List[Suggestion]:
        """Generate smart suggestions to resolve conflicts"""
        
    async def learn_from_patterns(self, user_id: int):
        """Learn from historical scheduling patterns"""
        
    async def should_auto_approve(self, suggestion: Suggestion) -> bool:
        """Determine if suggestion can be auto-approved"""
        
    async def create_approval_batch(self, user_id: int) -> ApprovalBatch:
        """Create a batch of pending approvals"""
```

### Integration with Calendar Systems

```python
# Unified calendar operations with AI enhancement

async def add_event_with_ai(
    user_id: int,
    event: CalendarEvent
) -> ScheduleResult:
    """Add event with AI conflict detection and suggestions"""
    
    # 1. Detect conflicts
    conflicts = await ai_scheduler.detect_conflicts(user_id, event)
    
    if conflicts:
        # 2. Generate suggestions
        suggestions = await ai_scheduler.generate_suggestions(conflicts[0])
        
        # 3. Check auto-approval
        if await ai_scheduler.should_auto_approve(suggestions[0]):
            # Auto-apply best suggestion
            return await apply_suggestion(suggestions[0])
        else:
            # Request parental approval
            return await create_approval_request(suggestions)
    
    # No conflicts, proceed
    return await calendar_service.add_event(event)
```

### Performance Optimization

- **Caching**: Pattern data cached for 1 hour
- **Async Processing**: All AI operations run asynchronously
- **Batch Processing**: Conflict detection runs in batches
- **Lazy Loading**: Learn patterns only when needed
- **Database Indexes**: Optimized queries on user_id, event times

### Future Enhancements

- [ ] ML model for more accurate predictions (scikit-learn/TensorFlow)
- [ ] Integration with wearable devices (energy/stress tracking)
- [ ] Predictive scheduling (suggest appointments proactively)
- [ ] Multi-family coordination (shared therapists/resources)
- [ ] Weather-aware scheduling
- [ ] School schedule integration

---

## 📱 Technology Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0+ with async support
- **Database**: PostgreSQL 15 (Azure Flexible Server)
- **Authentication**: JWT with bcrypt password hashing
- **API Documentation**: OpenAPI 3.0 (Swagger UI + ReDoc)

### AI & ML
- **AI Integration**: OpenAI GPT-4 / Azure OpenAI
- **Speech Services**: Azure Speech (speech-to-text, text-to-speech)
- **Language Detection**: Azure Cognitive Services (150+ languages)
- **NLU**: Custom intent recognition + GPT-4

### Cloud Infrastructure (Azure)
- **Compute**: Azure Container Apps (auto-scaling 2-10 instances)
- **Database**: PostgreSQL Flexible Server (encrypted at rest)
- **Storage**: Azure Blob Storage (backups, file uploads)
- **Secrets**: Azure Key Vault (API keys, certificates)
- **Monitoring**: Azure Monitor + Application Insights
- **CDN**: Azure Front Door (global load balancing)
- **IaC**: Bicep templates

### Voice Platforms
- **Apple**: Siri Shortcuts, SiriKit
- **Amazon**: Alexa Skills Kit
- **Google**: Google Assistant Actions (optional)
- **Tesla**: Grok API integration

### Communication Integrations
- **Email**: Gmail API, SMTP
- **SMS**: Twilio SMS API
- **WhatsApp**: Twilio WhatsApp Business API
- **Push Notifications**: Firebase Cloud Messaging (iOS/Android)

### Calendar Integrations
- **Google Calendar**: Google Calendar API
- **Apple Calendar**: CalDAV + EventKit
- **Microsoft Outlook**: Microsoft Graph API

### Mobile
- **iOS**: Native SwiftUI app + Siri Shortcuts
- **Android**: Native Kotlin app + Google Assistant

### Security & Compliance
- **Encryption**: AES-256 (data at rest), TLS 1.3 (in transit)
- **Secrets Management**: Azure Key Vault + environment variables
- **PII Protection**: Field-level encryption, audit logging
- **Compliance**: COPPA, HIPAA, GDPR guardrails built-in

### Testing
- **Unit/Integration**: Pytest with async support
- **Coverage**: pytest-cov (target >80%)
- **Mocking**: pytest-mock, responses
- **Security**: Bandit, Safety
- **Load Testing**: Locust (optional)

### DevOps & CI/CD
- **Version Control**: Git with Git Flow
- **CI/CD**: GitHub Actions (multi-stage pipeline)
- **Container Registry**: Azure Container Registry
- **Linting**: Black, isort, Flake8, MyPy
- **Pre-commit**: Automated code quality checks
- **Secrets Scanning**: git-secrets, detect-secrets

### Development Tools
- **Package Manager**: pip with requirements.txt
- **Container Runtime**: Podman/Docker
- **API Testing**: cURL, Postman, HTTPie
- **Database Migrations**: Alembic (future)

---

# Contributing to Mew Assistant

Thank you for your interest in contributing to Mew Assistant! 🎉

This document provides guidelines for contributing to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

---

## 🤝 Code of Conduct

Be respectful, inclusive, and professional. We're building this for special needs families and caregivers.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Podman or Docker
- Git
- PostgreSQL (via Podman) or SQLite

---

## 🛠️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/mew-assistant.git
cd mew-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev tools
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 4. Set Up Database

```bash
# Copy environment template
cp .env.example .env

# Start PostgreSQL with Podman
./podman-start.sh

# Or use SQLite (for development)
# Edit .env and set: DATABASE_URL=sqlite:///./mew_assistant.db
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

---

## 💡 How to Contribute

### Types of Contributions

We welcome:

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test coverage improvements
- 🎨 UI/UX enhancements
- 🌐 Translations
- ♿ Accessibility improvements

### Contribution Workflow

1. **Create an issue** (if one doesn't exist)
2. **Fork the repository**
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Write/update tests**
6. **Run tests**: `pytest`
7. **Commit with clear messages**: `git commit -m "feat: add new feature"`
8. **Push to your fork**: `git push origin feature/your-feature-name`
9. **Open a Pull Request**

---

## 🎨 Code Style

We use automated tools to maintain code quality:

### Python Style Guide

- **Formatter**: Black (line length: 100)
- **Import Sorter**: isort (Black-compatible profile)
- **Linter**: Flake8
- **Type Checker**: MyPy

### Pre-commit Hooks

Pre-commit hooks run automatically on every commit:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new session type
fix: resolve cooldown calculation bug
docs: update API documentation
test: add tests for message service
chore: update dependencies
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `refactor`: Code refactoring
- `perf`: Performance improvements

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_sessions.py

# Run specific test
pytest tests/test_sessions.py::test_create_session
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files: `test_*.py`
- Name test functions: `test_*`
- Use fixtures from `conftest.py`
- Aim for >80% code coverage

Example:

```python
def test_create_session(client):
    """Test creating a new session"""
    response = client.post(
        "/mew/session",
        json={
            "user_id": "test_user",
            "session_type": "tutoring",
            "title": "Math Homework",
            "priority": "normal"
        }
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
```

---

## 📥 Pull Request Process

### Before Submitting

1. ✅ Update tests
2. ✅ Run `pytest` - all tests pass
3. ✅ Run `pre-commit run --all-files` - no errors
4. ✅ Update documentation if needed
5. ✅ Update CHANGELOG.md

### PR Template

When opening a PR, include:

- **Description**: What does this PR do?
- **Issue**: Fixes #123 (if applicable)
- **Type**: Bug fix / Feature / Documentation
- **Testing**: How was this tested?
- **Screenshots**: (if UI changes)
- **Checklist**: Did you run tests, linting, etc.?

### Review Process

1. Automated checks run (GitHub Actions)
2. Maintainers review code
3. Address feedback
4. PR is merged

---

## 🐛 Reporting Bugs

### Before Reporting

- Search existing issues
- Try the latest version
- Gather reproduction steps

### Bug Report Should Include

- **Description**: Clear summary
- **Steps to Reproduce**: Numbered steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, etc.
- **Logs**: Relevant error messages

Use the bug report template in `.github/ISSUE_TEMPLATE/`

---

## ✨ Feature Requests

We love new ideas! When requesting a feature:

- **Use Case**: Describe the problem
- **Proposed Solution**: How should it work?
- **Alternatives**: Other approaches considered?
- **Additional Context**: Screenshots, examples, etc.

Use the feature request template in `.github/ISSUE_TEMPLATE/`

---

## 📞 Questions?

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bugs and features
- **Email**: [Project email if available]

---

## 🙏 Thank You!

Your contributions help families and caregivers. Every bug fix, feature, and documentation improvement makes a difference!

---

**Built with ❤️ for special needs families**

---

# Git Flow Workflow Guide

## Overview
This project follows the **GitFlow** branching model for organized development and releases.

## Branch Structure

### Main Branches
- **`main`** - Production-ready code. Protected branch.
- **`develop`** - Integration branch for features. Protected branch.

### Supporting Branches
- **`feature/*`** - New features (branch from `develop`, merge back to `develop`)
- **`release/*`** - Release preparation (branch from `develop`, merge to `main` and `develop`)
- **`hotfix/*`** - Production fixes (branch from `main`, merge to `main` and `develop`)

## Quick Start (Without git-flow tool)

### Starting a New Feature
```bash
# Create and switch to feature branch
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Work on your feature...
git add .
git commit -m "feat: add your feature"

# Push to remote
git push -u origin feature/your-feature-name

# Create Pull Request to develop branch on GitHub
```

### Finishing a Feature
```bash
# Update develop
git checkout develop
git pull origin develop

# Merge feature (via GitHub PR is preferred)
# Or manually:
git merge --no-ff feature/your-feature-name
git push origin develop

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

### Starting a Release
```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# Update version numbers, changelog, etc.
git add .
git commit -m "chore: prepare release 1.2.0"
git push -u origin release/1.2.0
```

### Finishing a Release
```bash
# Merge to main
git checkout main
git pull origin main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git pull origin develop
git merge --no-ff release/1.2.0
git push origin develop

# Delete release branch
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

### Creating a Hotfix
```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/1.2.1

# Fix the bug
git add .
git commit -m "fix: critical bug in production"
git push -u origin hotfix/1.2.1
```

### Finishing a Hotfix
```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/1.2.1
git tag -a v1.2.1 -m "Hotfix version 1.2.1"
git push origin main --tags

# Merge to develop
git checkout develop
git merge --no-ff hotfix/1.2.1
git push origin develop

# Delete hotfix branch
git branch -d hotfix/1.2.1
git push origin --delete hotfix/1.2.1
```

## Branch Naming Conventions

- `feature/user-authentication` ✅
- `feature/add-calendar-sync` ✅
- `release/1.2.0` ✅
- `hotfix/fix-login-bug` ✅
- `bugfix/something` ❌ (use feature/ or hotfix/)
- `my-feature` ❌ (missing prefix)

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

### Examples:
```bash
git commit -m "feat(auth): add JWT authentication"
git commit -m "fix(calendar): resolve timezone issue"
git commit -m "docs: update API documentation"
git commit -m "chore: update dependencies"
```

## Pull Request Workflow

1. **Create feature branch** from `develop`
2. **Make changes** and commit
3. **Push** to remote
4. **Create Pull Request** on GitHub
5. **Wait for CI/CD** checks to pass
6. **Request review** from team members
7. **Address feedback** if needed
8. **Merge** when approved

## Protected Branches

Both `main` and `develop` are protected:
- Require pull request reviews
- Require status checks to pass
- No force pushes
- No deletions

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## GitHub Actions Integration

Our GitFlow workflow automatically:
- ✅ Validates branch naming conventions
- ✅ Runs tests on all branches
- ✅ Enforces code quality checks
- ✅ Prevents invalid branch names

## Common Workflows

### Daily Development
```bash
# Start your day
git checkout develop
git pull origin develop

# Create feature
git checkout -b feature/my-feature

# Work...
git add .
git commit -m "feat: implement feature"
git push -u origin feature/my-feature

# Create PR on GitHub to develop
```

### Before Release
```bash
# Create release branch
git checkout -b release/1.2.0 develop

# Update version, changelog
# Test thoroughly
# Fix any issues

# Merge to main and develop (via PRs)
```

### Emergency Production Fix
```bash
# Create hotfix from main
git checkout -b hotfix/1.2.1 main

# Fix bug
git add .
git commit -m "fix: critical production issue"

# Merge to both main and develop (via PRs)
```

## Best Practices

1. **Always branch from the correct source**
   - Features: from `develop`
   - Releases: from `develop`
   - Hotfixes: from `main`

2. **Keep branches short-lived**
   - Features: 1-5 days
   - Releases: 1-3 days
   - Hotfixes: Hours

3. **Use meaningful names**
   - ✅ `feature/add-voice-commands`
   - ❌ `feature/stuff`

4. **Write good commit messages**
   - Clear, concise, conventional format

5. **Update regularly**
   - Pull from develop daily
   - Rebase if needed

6. **Test before merging**
   - All tests must pass
   - Code review approved

## Resources

- [Git Flow Original Article](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow vs Git Flow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)

## Current Project Status

- **Production Branch**: `main`
- **Development Branch**: `develop` (to be created)
- **Current Version**: Check `main` branch tags
- **Active Features**: Check open PRs with `feature/*` branches

## Questions?

Refer to this guide or ask in team discussions. Happy coding! 🚀

---

# AI-Powered Scheduling System

## Overview

Mew's AI Scheduler provides intelligent conflict detection, resolution suggestions, and pattern-based scheduling recommendations for families managing complex schedules.

## Features

### 1. Conflict Detection

Automatically detects scheduling conflicts with three severity levels:

- **Low**: Minor overlaps (< 15 minutes), easy to adjust
- **Medium**: Moderate conflicts (15-30 minutes) that need attention  
- **High**: Major conflicts (> 30 minutes) or involving critical activities

```python
POST /ai-scheduler/detect-conflicts
{
  "start_time": "2025-01-15T10:00:00",
  "end_time": "2025-01-15T11:00:00",
  "title": "Therapy Session",
  "activity_type": "therapy",
  "priority": "high"
}
```

**Response:**
```json
[
  {
    "conflicting_entry_id": 123,
    "conflicting_title": "Doctor Appointment",
    "conflict_type": "time_overlap",
    "severity": "high",
    "overlap_minutes": 45,
    "suggestions": [
      "Move to 02:00 PM",
      "Schedule for next available day"
    ]
  }
]
```

### 2. Smart Time Suggestions

AI learns from your scheduling patterns to suggest optimal times:

```python
POST /ai-scheduler/suggest-times
{
  "activity_type": "therapy",
  "duration_minutes": 60,
  "preferred_date": "2025-01-20T00:00:00",
  "constraints": {
    "earliest_hour": 8,
    "latest_hour": 18,
    "buffer_minutes": 15
  }
}
```

**Response:**
```json
[
  {
    "start_time": "2025-01-20T10:00:00",
    "end_time": "2025-01-20T11:00:00",
    "confidence_score": 0.85,
    "reasoning": "Highly recommended: Matches your typical scheduling pattern; Includes buffer time for transitions; Scheduled during optimal focus hours",
    "factors": [
      "Matches your typical scheduling pattern",
      "Includes buffer time for transitions",
      "Scheduled during optimal focus hours"
    ]
  }
]
```

### 3. Schedule Optimization

Optimize your entire day based on specific goals:

```python
POST /ai-scheduler/optimize-schedule
{
  "date": "2025-01-15T00:00:00",
  "optimization_goals": [
    "minimize_transitions",
    "respect_energy_levels",
    "balance_activities"
  ]
}
```

**Optimization Goals:**

- **minimize_transitions**: Group similar activities, reduce travel time
- **respect_energy_levels**: Schedule high-focus tasks during peak energy periods
- **balance_activities**: Distribute different activity types throughout the day

### 4. Pattern Learning

The AI learns from your scheduling history to provide personalized recommendations:

**Learning Status Endpoint:**
```python
GET /ai-scheduler/learning-status
```

**Requirements for Pattern Learning:**
- Minimum 5 completed activities of the same type
- Activities from the past 90 days
- Completion tracking (success/failure)

**What the AI Learns:**
- Preferred hours for different activities
- Preferred days of the week
- Typical activity duration
- Success rates by time of day

## Activity Types

Supported activity types for pattern recognition:

- `therapy` - Therapy sessions
- `tutoring` - Educational sessions
- `medical` - Medical appointments
- `social` - Social activities
- `exercise` - Physical activities
- `meal` - Meal times
- `sleep` - Sleep schedule
- `other` - General activities

## Priority Levels

Schedule entries support four priority levels:

- `low` - Flexible activities
- `normal` - Standard activities (default)
- `high` - Important activities
- `urgent` - Critical activities (therapy, medical)

## Conflict Resolution

### Automatic Resolution

For low-severity conflicts, the AI can auto-resolve based on preferences:

```python
# User preferences affecting auto-resolution
{
  "allow_overlap_for_therapy": true,
  "buffer_minutes": 15,
  "earliest_schedule_hour": 7,
  "latest_schedule_hour": 22
}
```

### Manual Resolution

For medium/high severity conflicts, the AI provides suggestions but requires user decision.

## Best Practices

### 1. Mark Completion Status

Always mark activities as completed to improve AI learning:

```python
PATCH /calendar/events/{id}
{
  "status": "completed",
  "completed_successfully": true,
  "completion_notes": "Session went well"
}
```

### 2. Set Realistic Constraints

Use constraints to guide suggestions:

```python
{
  "earliest_hour": 8,      # Don't suggest before 8am
  "latest_hour": 18,       # Don't suggest after 6pm
  "buffer_minutes": 15     # Allow 15min between activities
}
```

### 3. Build History

Use the system for at least 2 weeks to build meaningful patterns for AI learning.

### 4. Review Suggestions

Always review AI suggestions - they're recommendations, not requirements.

## Configuration

### User Preferences

Set scheduling preferences via:

```python
PUT /api/user/preferences
{
  "allow_overlap_for_therapy": false,
  "buffer_minutes": 15,
  "earliest_schedule_hour": 7,
  "latest_schedule_hour": 22,
  "peak_energy_hours": [9, 10, 11],
  "low_energy_hours": [14, 15],
  "minimize_transitions": true,
  "respect_energy_levels": true,
  "balance_activities": true
}
```

## Integration with Calendar

The AI Scheduler integrates with:

- Google Calendar
- Apple Calendar  
- Microsoft Outlook

Conflicts are detected across all integrated calendars.

## Privacy & Security

- All scheduling data is encrypted at rest
- Pattern learning happens on your data only
- No data is shared across users
- AI models run locally (no external AI service)

## Performance

- Conflict detection: < 100ms for typical schedules
- Suggestions: < 500ms including pattern analysis
- Optimization: < 2s for full day optimization

## Limitations

- Pattern learning requires minimum 5 data points per activity type
- Optimization works best with 3-10 activities per day
- Historical data limited to past 90 days
- Maximum 50 suggestions per request

## Future Enhancements

- Multi-user coordination (family scheduling)
- Weather-based activity suggestions
- Integration with transportation services
- Predictive rescheduling for anticipated delays
- Machine learning model improvements

## Support

For issues or questions:
- GitHub Issues: https://github.com/skakumanu/mew-assistant/issues
- Documentation: https://github.com/skakumanu/mew-assistant/wiki

---

**Note**: The AI Scheduler is designed to assist, not replace, human decision-making. Always review suggestions before accepting them, especially for critical activities.

---

# 🔒 Security, Privacy & Compliance

Comprehensive documentation for security, privacy, and compliance in Mew Assistant.

## Table of Contents
- [Security Overview](#security-overview)
- [Privacy Protection](#privacy-protection)
- [Compliance Standards](#compliance-standards)
- [Security Audit](#security-audit)

---

## Security Overview

### Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Security Layers                    │
├─────────────────────────────────────────────────────┤
│ 1. Network Layer (WAF, DDoS Protection)            │
│ 2. Application Layer (Rate Limiting, JWT Auth)     │
│ 3. Data Layer (Encryption at Rest/Transit)         │
│ 4. Access Layer (RBAC, MFA)                        │
│ 5. Audit Layer (Logging, Monitoring)               │
└─────────────────────────────────────────────────────┘
```

### Authentication & Authorization

#### JWT-Based Authentication
```python
# Token structure
{
    "user_id": "uuid",
    "role": "parent|kid|caregiver",
    "family_id": "uuid",
    "permissions": ["read:schedule", "write:schedule"],
    "exp": 1234567890,
    "iat": 1234567890
}

# Token security
- RS256 signing algorithm
- Short expiration (15 minutes for access tokens)
- Refresh tokens (7 days, rotated on use)
- Stored securely in Azure Key Vault
```

#### Multi-Factor Authentication (MFA)
```yaml
Supported methods:
  - SMS code
  - Email code
  - Authenticator app (TOTP)
  - Biometric (Touch ID, Face ID)

Requirements:
  - Required for parents
  - Optional for caregivers
  - Not required for kids
```

#### Role-Based Access Control (RBAC)
```python
Roles:
  parent:
    - Full access to all features
    - Manage family members
    - Approve requests
    - View all data
  
  kid:
    - View own schedule
    - Make requests (subject to approval)
    - Limited data access
    - Cannot delete critical data
  
  caregiver:
    - View assigned schedules
    - Update session notes
    - Limited approval rights
    - Read-only for sensitive data
  
  therapist:
    - View relevant sessions
    - Update progress notes
    - No access to other family data
```

### Data Encryption

#### Encryption at Rest
```yaml
Database:
  - PostgreSQL with Transparent Data Encryption (TDE)
  - Customer-managed keys in Azure Key Vault
  - AES-256 encryption
  - Encrypted backups

File Storage:
  - Azure Blob Storage server-side encryption
  - AES-256 encryption
  - Separate keys per family

Application:
  - Field-level encryption for PII
  - Encrypted configuration files
```

#### Encryption in Transit
```yaml
HTTPS/TLS:
  - TLS 1.3 minimum
  - Strong cipher suites only
  - Certificate pinning in mobile apps
  - Perfect Forward Secrecy (PFS)

API Communication:
  - All APIs require HTTPS
  - WebSocket over TLS (WSS)
  - No downgrade to HTTP
```

### Security Headers

```yaml
Headers:
  Strict-Transport-Security: "max-age=31536000; includeSubDomains"
  X-Frame-Options: "DENY"
  X-Content-Type-Options: "nosniff"
  Content-Security-Policy: "default-src 'self'"
  X-XSS-Protection: "1; mode=block"
  Referrer-Policy: "strict-origin-when-cross-origin"
  Permissions-Policy: "geolocation=(), microphone=(), camera=()"
```

### API Security

#### Rate Limiting
```python
Rate limits:
  - Anonymous: 10 requests/minute
  - Authenticated: 100 requests/minute
  - Premium: 1000 requests/minute
  
Per endpoint:
  - /api/v1/auth/login: 5 attempts/5 minutes
  - /api/v1/auth/register: 3 attempts/hour
  - /api/v1/messages: 50 requests/minute
```

#### Input Validation
```python
# All inputs validated using Pydantic
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    channel: Literal["email", "sms", "whatsapp", "voice"]
    
    @validator('content')
    def sanitize_content(cls, v):
        return bleach.clean(v)  # XSS prevention
```

#### SQL Injection Prevention
```python
# All database queries use SQLAlchemy ORM
# Parameterized queries only
# No raw SQL with user input

# Example:
query = db.query(Message).filter(
    Message.user_id == user_id,
    Message.created_at >= start_date
)
```

### Secrets Management

```yaml
Azure Key Vault:
  secrets:
    - database-connection-string
    - jwt-private-key
    - openai-api-key
    - twilio-auth-token
    - sendgrid-api-key
    - google-oauth-client-secret
  
  access:
    - Managed Identity only
    - No hardcoded credentials
    - Automatic rotation (90 days)
    - Audit logs enabled
```

### Vulnerability Management

```yaml
Dependency Scanning:
  - Snyk: Daily scans
  - GitHub Dependabot: Automatic PRs
  - npm audit / pip audit
  
Security Testing:
  - SAST: Bandit (Python)
  - DAST: OWASP ZAP
  - Container scanning: Trivy
  - Secret scanning: GitGuardian
  
Penetration Testing:
  - Quarterly by third-party
  - Bug bounty program
  - Responsible disclosure policy
```

---

## Privacy Protection

### Privacy by Design

#### Data Minimization
```python
# Only collect necessary data
user_data = {
    "name": required,
    "email": required,
    "phone": optional,
    "date_of_birth": required_for_kids,
    "address": not_collected,
    "ssn": never_collected
}
```

#### Purpose Limitation
```yaml
Data usage:
  schedule_data:
    purpose: "Appointment management"
    retention: "Until user deletes or 2 years inactive"
    sharing: "Never shared with third parties"
  
  voice_recordings:
    purpose: "Voice command processing"
    retention: "7 days for quality, then deleted"
    sharing: "Processed by Azure Speech Service only"
```

#### Storage Limitation
```python
# Automatic data deletion
retention_policy = {
    "voice_recordings": "7_days",
    "message_logs": "90_days",
    "session_logs": "1_year",
    "inactive_accounts": "2_years",
    "deleted_accounts": "immediate_+ 30_day_recovery"
}
```

### Personal Data Protection

#### PII Identification and Encryption
```python
# Automatically detect and encrypt PII
pii_fields = [
    "name", "email", "phone", "date_of_birth",
    "medical_info", "diagnosis", "medications"
]

# Field-level encryption
class User(Base):
    name = Column(EncryptedString)
    email = Column(EncryptedString)
    phone = Column(EncryptedString)
    # Public fields
    user_id = Column(UUID)
    created_at = Column(DateTime)
```

#### Data Access Controls
```python
# Audit all PII access
@audit_access("pii_access")
def get_user_profile(user_id: str, requester_id: str):
    # Check permissions
    if not has_permission(requester_id, "read:profile", user_id):
        raise PermissionDenied
    
    # Log access
    audit_log.info(f"User {requester_id} accessed profile {user_id}")
    
    return user_profile
```

### User Rights (GDPR/CCPA Compliance)

#### Right to Access
```http
GET /api/v1/privacy/data-export
Authorization: Bearer <token>

Response: ZIP file with all user data in JSON format
```

#### Right to Rectification
```http
PATCH /api/v1/user/profile
Content-Type: application/json
Authorization: Bearer <token>

{
  "email": "newemail@example.com",
  "phone": "+1234567890"
}
```

#### Right to Erasure
```http
DELETE /api/v1/user/account
Authorization: Bearer <token>

# Immediate deletion of:
- Personal information
- Messages and communications
- Voice recordings
- Session data

# Retained for legal compliance (encrypted):
- Transaction records (7 years)
- Audit logs (3 years)
```

#### Right to Data Portability
```http
GET /api/v1/privacy/data-export?format=json
Authorization: Bearer <token>

# Machine-readable formats:
- JSON
- CSV
- XML
```

#### Right to Object
```http
POST /api/v1/privacy/opt-out
Authorization: Bearer <token>

{
  "opt_out_of": ["marketing", "analytics", "ai_training"]
}
```

### Consent Management

```yaml
Consent Types:
  essential:
    description: "Required for service operation"
    required: true
    can_withdraw: false
  
  functionality:
    description: "Enhanced features like voice commands"
    required: false
    can_withdraw: true
  
  analytics:
    description: "Usage analytics for improvement"
    required: false
    can_withdraw: true
  
  marketing:
    description: "Product updates and newsletters"
    required: false
    can_withdraw: true
```

#### Parental Consent (COPPA)
```python
# For users under 13
if user.age < 13:
    require_parental_consent()
    verify_parent_identity()
    parent_approve_data_collection()
    
# Verifiable parental consent methods:
- Credit card verification ($0.50 charge, refunded)
- Government ID check
- Video call verification
- Signed consent form
```

---

## Compliance Standards

### COPPA (Children's Online Privacy Protection Act)

```yaml
Requirements:
  ✅ Parental consent before data collection
  ✅ Clear privacy policy for children
  ✅ Limited data collection from children
  ✅ Reasonable security for children's data
  ✅ No conditioning participation on excess data
  ✅ Parental access to child's data
  ✅ Parent can delete child's data
  ✅ No targeted advertising to children
```

Implementation:
```python
# Age verification
if user.age < 13:
    # Require parent email
    send_parental_consent_request(parent_email)
    
    # Limited features until consent
    restrict_features(user_id, [
        "social_features",
        "voice_recording",
        "location_tracking"
    ])
    
    # Parent must verify
    wait_for_parental_consent(timeout=72_hours)
```

### GDPR (General Data Protection Regulation)

```yaml
Requirements:
  ✅ Lawful basis for processing
  ✅ Transparent privacy practices
  ✅ Purpose limitation
  ✅ Data minimization
  ✅ Accuracy
  ✅ Storage limitation
  ✅ Integrity and confidentiality
  ✅ Accountability
  
Rights:
  ✅ Right to access
  ✅ Right to rectification
  ✅ Right to erasure
  ✅ Right to restrict processing
  ✅ Right to data portability
  ✅ Right to object
  ✅ Rights related to automated decision-making
```

### HIPAA Readiness

```yaml
Note: Mew Assistant is HIPAA-ready but requires BAA for covered entities

Technical Safeguards:
  ✅ Access controls
  ✅ Audit controls
  ✅ Integrity controls
  ✅ Transmission security
  
Physical Safeguards:
  ✅ Azure data centers (HIPAA compliant)
  ✅ Workstation security
  ✅ Device and media controls
  
Administrative Safeguards:
  ✅ Security management process
  ✅ Workforce security
  ✅ Information access management
  ✅ Security awareness training
```

### FERPA (Family Educational Rights and Privacy Act)

```yaml
For educational records:
  ✅ Parent access to records
  ✅ Parent can request amendments
  ✅ Control over disclosure
  ✅ Right to file complaints
  
Implementation:
  - Separate educational data from other data
  - Parent controls access
  - Audit all access to educational records
  - No sharing without consent
```

### SOC 2 Type II Compliance

```yaml
Trust Service Criteria:
  Security:
    ✅ Access controls
    ✅ System operations
    ✅ Change management
    ✅ Risk mitigation
  
  Availability:
    ✅ 99.9% uptime SLA
    ✅ Disaster recovery
    ✅ Backup procedures
  
  Processing Integrity:
    ✅ Data quality
    ✅ Error handling
    ✅ Data validation
  
  Confidentiality:
    ✅ Encryption
    ✅ Access restrictions
    ✅ Secure disposal
  
  Privacy:
    ✅ Notice and consent
    ✅ Data subject rights
    ✅ Data retention
```

---

## Security Audit

### Last Audit: 2024-11-15

#### Audit Scope
- Application security
- Infrastructure security
- Data protection
- Compliance adherence
- Penetration testing

#### Findings Summary

✅ **Critical Issues**: 0
✅ **High Issues**: 0
⚠️ **Medium Issues**: 0 (all resolved)
ℹ️ **Low Issues**: 2 (documented below)

#### Low Priority Findings

1. **Rate Limiting Enhancement**
   - Status: Acknowledged
   - Risk: Low
   - Action: Consider implementing adaptive rate limiting
   - Timeline: Q1 2025

2. **Logging Verbosity**
   - Status: Acknowledged
   - Risk: Low
   - Action: Reduce debug logging in production
   - Timeline: Next release

#### Security Controls Verified

```yaml
✅ Authentication:
  - JWT implementation secure
  - Token expiration properly configured
  - Refresh token rotation working
  
✅ Authorization:
  - RBAC correctly implemented
  - Permission checks on all endpoints
  - No privilege escalation vectors
  
✅ Encryption:
  - TLS 1.3 enforced
  - Strong cipher suites only
  - Database encryption verified
  - PII field-level encryption active
  
✅ Input Validation:
  - All inputs validated
  - SQL injection prevention verified
  - XSS prevention in place
  - CSRF tokens working
  
✅ API Security:
  - Rate limiting functional
  - No sensitive data in logs
  - Error messages don't leak info
  - API keys properly secured
  
✅ Infrastructure:
  - Security groups configured correctly
  - No public access to databases
  - Secrets in Key Vault only
  - Monitoring and alerts active
```

#### Penetration Testing Results

```yaml
Test Date: 2024-11-10
Tester: Third-party security firm

Tests Performed:
  - Authentication bypass attempts ❌ Failed (secure)
  - SQL injection ❌ Failed (secure)
  - XSS attacks ❌ Failed (secure)
  - CSRF attacks ❌ Failed (secure)
  - Authorization bypass ❌ Failed (secure)
  - Session hijacking ❌ Failed (secure)
  - Brute force attacks ❌ Failed (rate limited)
  - API abuse ❌ Failed (protected)

Conclusion: No vulnerabilities found
```

### Continuous Monitoring

```yaml
Security Monitoring:
  - Real-time threat detection (Azure Sentinel)
  - Anomaly detection (ML-based)
  - Failed login tracking
  - Suspicious activity alerts
  - DDoS protection (Azure Front Door)
  
Log Analysis:
  - Centralized logging (Azure Log Analytics)
  - Security event correlation
  - Automated alerting
  - 90-day retention
  
Vulnerability Scanning:
  - Daily dependency scans
  - Weekly infrastructure scans
  - Container image scanning
  - License compliance checks
```

### Incident Response Plan

```yaml
Severity Levels:
  Critical:
    - Data breach
    - Complete service outage
    - Security compromise
    Response Time: 15 minutes
    
  High:
    - Service degradation
    - Authentication issues
    - Data access errors
    Response Time: 1 hour
    
  Medium:
    - Feature issues
    - Performance degradation
    Response Time: 4 hours
    
  Low:
    - Minor bugs
    - Cosmetic issues
    Response Time: 24 hours

Response Process:
  1. Detection and alerting
  2. Initial assessment
  3. Containment
  4. Eradication
  5. Recovery
  6. Post-incident review
  7. Documentation and lessons learned
```

---

## Security Best Practices for Users

### For Parents

```yaml
✅ Use strong passwords (12+ characters)
✅ Enable MFA
✅ Don't share your account
✅ Review access logs regularly
✅ Keep recovery email updated
✅ Use approved devices only
✅ Log out on shared devices
```

### For Developers

```yaml
✅ Never commit secrets
✅ Use environment variables
✅ Run security scans locally
✅ Follow secure coding guidelines
✅ Keep dependencies updated
✅ Review code for security issues
✅ Use branch protection rules
```

---

## Reporting Security Issues

### Responsible Disclosure

```
Email: security@mew-assistant.example.com
PGP Key: Available at /security/pgp-key

Please include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

Response Timeline:
- Acknowledgment: 24 hours
- Initial assessment: 72 hours
- Fix timeline: Based on severity
- Public disclosure: After fix deployed

Bug Bounty:
- Critical: $500 - $2000
- High: $200 - $500
- Medium: $50 - $200
- Low: Recognition + swag
```

---

## Compliance Certifications

```yaml
Current:
  ✅ SOC 2 Type II (in progress)
  ✅ GDPR Compliant
  ✅ COPPA Compliant
  ✅ CCPA Compliant
  
Planned:
  🔄 HIPAA (BAA available on request)
  🔄 ISO 27001
  🔄 PCI DSS (if payment processing added)
```

---

## Contact

**Security Team**: security@mew-assistant.example.com
**Privacy Team**: privacy@mew-assistant.example.com
**Compliance Team**: compliance@mew-assistant.example.com

**Last Updated**: 2024-11-15
**Next Review**: 2025-02-15
