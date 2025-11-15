# Mew Assistant - Complete System Architecture

## 🏗️ High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        External Services Layer                      │
├────────────────────────────────────────────────────────────────────┤
│  📧 Email        📱 SMS         💬 WhatsApp    🤖 AI      📅 Calendar│
│  (Gmail)      (Twilio)       (Twilio)    (OpenAI/   (Google)       │
│                                            Claude)                   │
└─────────────┬──────────────────────────────┬───────────────────────┘
              │                               │
              ▼                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Integration Layer                              │
├────────────────────────────────────────────────────────────────────┤
│  EmailIntegration  │  SMSIntegration  │  WhatsAppIntegration       │
│  AIIntegration     │  CalendarIntegration                          │
└─────────────┬──────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Service Layer                                  │
├────────────────────────────────────────────────────────────────────┤
│  SessionService  │  MessageService  │  SummaryService              │
│  AuthService     │  ScheduleService                                │
└─────────────┬──────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      API Router Layer                               │
├────────────────────────────────────────────────────────────────────┤
│  /auth/*     │  /mew/*      │  /webhooks/*                         │
│  Authentication│ Core APIs  │  External Webhooks                   │
└─────────────┬──────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Middleware Layer                               │
├────────────────────────────────────────────────────────────────────┤
│  CORS  │  Request ID  │  Exception Handler  │  Logging             │
└─────────────┬──────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                            │
└────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Database Layer                                 │
├────────────────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM  │  Models  │  Session Management                  │
└─────────────┬──────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL / SQLite                            │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Structure

```
mew-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   │
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── session.py          # Session management
│   │   ├── message.py          # Message ingestion
│   │   ├── summary.py          # Summary generation
│   │   └── webhooks.py         # External webhooks
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── session_service.py
│   │   ├── message_service.py
│   │   └── summary_service.py
│   │
│   ├── integrations/           # External services
│   │   ├── __init__.py
│   │   ├── email_integration.py
│   │   ├── sms_integration.py
│   │   ├── whatsapp_integration.py
│   │   ├── ai_integration.py
│   │   └── calendar_integration.py
│   │
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── session.py
│   │
│   ├── schemas/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── session.py
│   │   └── message.py
│   │
│   ├── utils/                  # Utilities
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   ├── cooldown.py
│   │   └── priority.py
│   │
│   └── middleware/             # Custom middleware
│       ├── __init__.py
│       └── exception_handler.py
│
├── tests/                      # Test suite
│   ├── test_auth.py
│   ├── test_sessions.py
│   └── test_integrations.py
│
├── docs/                       # Documentation
│   ├── API.md
│   └── integrations/
│       └── SETUP_GUIDE.md
│
├── agent-cards/                # AGNTCY agent cards
│   ├── scheduler.yaml
│   ├── tutor.yaml
│   └── caregiver.yaml
│
├── .env.example                # Environment template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── podman-start.sh
├── podman-stop.sh
├── podman-full.sh
├── test_integrations.sh
└── README.md
```

---

## 🔄 Request Flow

### 1. Incoming Webhook (SMS/WhatsApp)

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
┌────────────────────────────────────┐
│  1. HTTPS/TLS (Transport Layer)    │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│  2. CORS (Cross-Origin Protection) │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│  3. JWT Authentication             │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│  4. Input Validation (Pydantic)    │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│  5. Rate Limiting                  │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│  6. Database Access Control        │
└────────────────────────────────────┘
```

---

## 💾 Database Schema

```
┌─────────────────┐      ┌──────────────────┐
│     Users       │      │   Sessions       │
├─────────────────┤      ├──────────────────┤
│ id (PK)         │◄────┐│ id (PK)          │
│ email           │     ││ user_id (FK)     │
│ hashed_password │     ││ session_type     │
│ full_name       │     ││ status           │
│ created_at      │     ││ scheduled_at     │
│ is_active       │     ││ completed_at     │
└─────────────────┘     │└──────────────────┘
                        │
                        │┌──────────────────┐
                        ││   Messages       │
                        │├──────────────────┤
                        └┤ id (PK)          │
                         │ user_id (FK)     │
                         │ channel          │
                         │ content          │
                         │ direction        │
                         │ created_at       │
                         └──────────────────┘
```

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

## 🔄 CI/CD Pipeline (Recommended)

```
git push
    ↓
GitHub Actions
    ↓
├─ Linting (flake8, black)
├─ Type checking (mypy)
├─ Unit tests (pytest)
├─ Security scan (bandit)
└─ Integration tests
    ↓
Build Docker image
    ↓
Push to registry
    ↓
Deploy to environment
    ↓
Health check
    ↓
Rollback on failure
```

---

## 🎯 Key Design Principles

1. **Modularity**: Clear separation of concerns
2. **Extensibility**: Easy to add new integrations
3. **Reliability**: Graceful degradation
4. **Security**: Defense in depth
5. **Observability**: Comprehensive logging
6. **Performance**: Async operations
7. **Maintainability**: Clean code, documentation

---

**Last Updated**: Phase 5 Complete
**Version**: 1.0.0
