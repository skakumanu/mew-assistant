# Mew Assistant

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Podman](https://img.shields.io/badge/Podman-ready-purple.svg)](https://podman.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Mew Assistant** is a FastAPI-based modular assistant designed for special needs families. It supports scheduling, tutoring coordination, and caregiver summaries with multi-channel ingestion (email, SMS, WhatsApp).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Mew Assistant System                         │
└─────────────────────────────────────────────────────────────────┘

                         ┌─────────────┐
                         │   Clients   │
                         │ (Email/SMS/ │
                         │  WhatsApp)  │
                         └──────┬──────┘
                                │
                    ┌───────────▼───────────┐
                    │   FastAPI REST API    │
                    │  (main.py + routers)  │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
      ┌───────▼────────┐ ┌─────▼──────┐ ┌───────▼────────┐
      │   Session      │ │  Message   │ │   Summary      │
      │   Service      │ │  Service   │ │   Service      │
      └───────┬────────┘ └─────┬──────┘ └───────┬────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Database Layer      │
                    │   (SQLAlchemy ORM)    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   PostgreSQL/SQLite   │
                    │   (Podman Container)  │
                    └───────────────────────┘

Key Components:
• Session Management: Cooldown logic, priority periods
• Message Ingestion: Multi-channel support
• Caregiver Summaries: Actionable insights generation
• Database: Persistent storage with relationship management
```

---

## 🌟 Features

### Core Features
- **Session Management**: Schedule and manage tutoring, scheduling, and caregiver sessions
- **Multi-Channel Ingestion**: Accept messages via email, SMS, WhatsApp, and web forms
- **🎤 Voice Commands**: Multilingual voice recognition supporting 20+ languages (English, Spanish, French, German, Chinese, Japanese, Korean, Arabic, Hindi, and more)
- **🔐 Federated Authentication**: Sign in with Google, Apple, Microsoft, or Facebook (OAuth 2.0/OIDC)
- **Cooldown Protection**: Prevent overwhelming families with intelligent request throttling
- **Priority Period Overrides**: Automatically escalate priority during peak times (7-9am, 3-6pm, 7-9pm)
- **Caregiver Summaries**: Generate actionable insights and recommendations
- **PostgreSQL/SQLite**: Flexible database support
- **RESTful API**: Clean, documented endpoints with OpenAPI/Swagger support
- **Podman Support**: Containerized PostgreSQL for easy deployment

### 🧒 Kid-Friendly Features
- **Kid Accounts**: Age-appropriate interface for children to interact with schedules
- **Simple Communication**: Emoji-based reactions and simple language
- **Voice in Schedule**: Kids can suggest activities and request changes

### 👨‍👩‍👧 Parental Controls (NEW!)
- **🚨 Parental Approval System**: ALL kid requests require parent approval before changes
- **Safety First**: No schedule modifications happen without explicit parent authorization
- **Complete Oversight**: Parents review, approve, or deny all kid-initiated requests
- **Audit Trail**: Full compliance logging for accountability and safety
- **Kind Communication**: System encourages thoughtful parent responses to kids

### 🔒 Privacy & Compliance
- **HIPAA Compliant**: Protected health information handling
- **FERPA Compliant**: Educational records protection  
- **COPPA Compliant**: Children's online privacy with parental controls
- **GDPR/CCPA Ready**: Data privacy and user rights support
- **Complete Audit Logging**: Track all actions for compliance

See [docs/SECURITY_PRIVACY_COMPLIANCE.md](docs/SECURITY_PRIVACY_COMPLIANCE.md) for detailed compliance and parental controls implementation.

---

## 📋 Documentation

### Core Documentation
- **[README.md](README.md)** (this file) - Quick start and overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

### Feature Documentation
- **[docs/FEATURES.md](docs/FEATURES.md)** - Complete features guide including:
  - Mobile & Calendar Integration
  - Voice Commands (100+ languages)
  - Voice Platform Integration (Siri, Alexa, Google Assistant, Tesla)
  - Kid-Friendly Features
  - Parental Approval System
- **[docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)** - Federated authentication setup:
  - Google, Apple, Microsoft, Facebook OAuth
  - Production configuration
  - Mobile integration
  - Security best practices

### Deployment Documentation
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Complete deployment guide including:
  - Azure Cloud Setup
  - CI/CD Pipeline
  - Deployment Guardrails
  - Infrastructure as Code
  - Monitoring & Alerts
  - Disaster Recovery
- **[docs/SECURE_CREDENTIALS.md](docs/SECURE_CREDENTIALS.md)** - **Secure credential management with Azure Key Vault**

### Security & Compliance
- **[docs/SECURITY_PRIVACY_COMPLIANCE.md](docs/SECURITY_PRIVACY_COMPLIANCE.md)** - Security, privacy, and compliance including:
  - Security Architecture
  - Privacy Protection (GDPR, CCPA)
  - Compliance Standards (COPPA, HIPAA, FERPA, SOC 2)
  - Security Audit Results

⚠️ **Before deploying to production, please review all documentation in the `docs/` directory.**

---

## 🚀 Quick Start

### Option 1: Podman + Local App (Recommended)

```bash
# 1. Clone and install dependencies
git clone https://github.com/your-org/mew-assistant.git
cd mew-assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start PostgreSQL in Podman
./podman-start.sh

# 3. Run the app
uvicorn app.main:app --reload

# 4. Open browser
open http://localhost:8000/docs
```

### Option 2: Full Stack in Podman

```bash
# Run everything in containers
./podman-full.sh

# Check status
podman ps

# Access API
open http://localhost:8000/docs
```

### Option 3: SQLite (No Podman Needed)

```bash
# Automated setup
./setup.sh

# Run the app
source .venv/bin/activate
uvicorn app.main:app --reload
```

---

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user account |
| POST | `/auth/login` | Login and get JWT tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |
| PUT | `/auth/me` | Update user profile |
| POST | `/auth/change-password` | Change password |
| POST | `/auth/api-keys` | Create API key |
| GET | `/auth/api-keys` | List user API keys |
| DELETE | `/auth/api-keys/{id}` | Delete API key |

### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mew/session` | Create new session (requires auth) |
| POST | `/mew/confirm` | Confirm session with cooldown (requires auth) |
| PATCH | `/mew/session/{id}` | Update session (requires auth) |
| GET | `/mew/session/{id}` | Get session details (requires auth) |
| GET | `/mew/sessions/user/{user_id}` | List user sessions (requires auth) |

### Message Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mew/ingest` | Ingest single message |
| POST | `/mew/ingest/batch` | Batch ingest (max 100) |
| GET | `/mew/messages/unprocessed` | Get pending messages |
| PATCH | `/mew/message/{id}/processed` | Mark as processed |

### Caregiver Summaries

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mew/summary` | Generate summary |
| GET | `/mew/summary/{id}` | Get summary |
| GET | `/mew/summaries/user/{user_id}` | List summaries |

### 🎤 Voice Commands (Multilingual)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/voice/command` | Process voice command (audio file) |
| GET | `/voice/languages` | Get supported languages (20+) |
| POST | `/voice/session/start` | Start continuous voice session |
| POST | `/voice/session/{id}/end` | End voice session |

**Supported Languages**: English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, Hindi, Russian, Dutch, Polish, Turkish, Vietnamese, Thai, and more!

**Full API Documentation**: http://localhost:8000/docs

---

## 🧪 API Examples

### Authentication Flow

#### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "role": "parent",
    "phone": "+1234567890"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "parent",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-11-15T10:00:00Z"
}
```

#### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "parent"
  }
}
```

#### 3. Create API Key (for programmatic access)

```bash
curl -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "My Integration",
    "expires_in_days": 90,
    "scopes": ["read", "write"]
  }'
```

**Response:**
```json
{
  "id": 1,
  "key_name": "My Integration",
  "api_key": "mew_abc123...",
  "key_prefix": "mew_abc123...",
  "expires_at": "2026-02-15T10:00:00Z"
}
```

⚠️ **Important**: The full API key is only shown once. Store it securely!

### Create a Session

```bash
# Using JWT Token
curl -X POST "http://localhost:8000/mew/session" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "tutoring",
    "title": "Math Homework Help",
    "priority": "normal",
    "scheduled_at": "2025-11-15T14:00:00Z"
  }'

# OR using API Key
curl -X POST "http://localhost:8000/mew/session" \
  -H "Authorization: Bearer mew_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "tutoring",
    "title": "Math Homework Help",
    "priority": "normal",
    "scheduled_at": "2025-11-15T14:00:00Z"
  }'
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "session_type": "tutoring",
  "status": "pending",
  "priority": "normal",
  "title": "Math Homework Help",
  "cooldown_until": null,
  "in_cooldown": false
}
```

**Note**: All protected endpoints require authentication via `Authorization: Bearer TOKEN` header.
Use either JWT access token or API key (starts with `mew_`).

### Confirm Session

```bash
curl -X POST "http://localhost:8000/mew/confirm" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "notes": "Confirmed via phone",
    "override_cooldown": false
  }'
```

**Cooldown Logic:**
- Normal priority: 24-hour cooldown
- High priority: 12-hour cooldown
- Urgent: No cooldown
- Use `override_cooldown: true` for emergencies

### Ingest a Message

```bash
curl -X POST "http://localhost:8000/mew/ingest" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "sender": "parent@example.com",
    "subject": "Need tutoring help",
    "body": "My child needs help with math homework.",
    "session_id": 1
  }'
```

**Supported Channels:** email, sms, whatsapp, web

### Generate Summary

```bash
curl -X POST "http://localhost:8000/mew/summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "period_start": "2025-11-01T00:00:00Z",
    "period_end": "2025-11-13T23:59:59Z",
    "include_recommendations": true
  }'
```

### Testing Authentication

Run the comprehensive test script:

```bash
./test_auth.sh
```

This will test:
- ✅ User registration
- ✅ Login and token generation
- ✅ JWT authentication
- ✅ API key creation
- ✅ API key authentication
- ✅ Token refresh
- ✅ Protected endpoints

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file (or use `.env.example` as template):

```bash
# Database - PostgreSQL with Podman
DATABASE_URL=postgresql://mew_user:mew_password@localhost:5432/mew_assistant

# Or SQLite for development
# DATABASE_URL=sqlite:///./mew_assistant.db

# Cooldown Settings (hours)
DEFAULT_COOLDOWN_HOURS=24
TUTORING_COOLDOWN_HOURS=24
SCHEDULING_COOLDOWN_HOURS=12
SUMMARY_COOLDOWN_HOURS=48

# Priority Periods (24-hour format)
MORNING_PREP_START=07:00
MORNING_PREP_END=09:00
AFTER_SCHOOL_START=15:00
AFTER_SCHOOL_END=18:00
EVENING_ROUTINE_START=19:00
EVENING_ROUTINE_END=21:00

# Authentication & Security
SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Optional: Multi-Channel Integration
EMAIL_ENABLED=false
SMS_ENABLED=false
WHATSAPP_ENABLED=false

# Voice Commands (Multilingual Support)
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=eastus
OPENAI_API_KEY=your-openai-api-key  # For Whisper fallback and NLU
```

### Authentication & Security

Mew Assistant uses **JWT (JSON Web Tokens)** for authentication with support for **API keys** for programmatic access.

**User Roles:**
- `admin` - Full system access
- `caregiver` - Caregiver and session management
- `parent` - Family member access
- `therapist` - Therapist access
- `educator` - Educator access

**Security Best Practices:**
1. **Change Secret Keys**: Generate secure keys using `openssl rand -hex 32`
2. **Use HTTPS**: Always use HTTPS in production
3. **Rotate API Keys**: Set expiration dates on API keys
4. **Token Expiration**: Access tokens expire in 30 minutes (configurable)
5. **Refresh Tokens**: Use refresh tokens to obtain new access tokens

**Generating Secure Keys:**
```bash
# Generate JWT secret key
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Authentication Methods:**
1. **JWT Tokens** (recommended for web/mobile apps)
   - Short-lived access tokens (30 minutes)
   - Long-lived refresh tokens (7 days)
   - Automatic rotation on refresh

2. **API Keys** (for integrations & scripts)
   - Prefix: `mew_`
   - Optional expiration (up to 365 days)
   - Scoped permissions
   - Revocable anytime

### Session Types

- `tutoring` - Tutoring sessions
- `scheduling` - Scheduling coordination
- `caregiver_summary` - Caregiver summary generation

### Priority Levels

- `low` - Low priority (longer cooldown)
- `normal` - Standard priority
- `high` - High priority (shorter cooldown)
- `urgent` - Urgent (no cooldown)

### Priority Period Auto-Escalation

Automatically escalates priority during:
- **Morning Prep**: 7am-9am
- **After-School**: 3pm-6pm
- **Evening Routine**: 7pm-9pm

---

## 🐳 Using Podman

### Start PostgreSQL Only

```bash
./podman-start.sh
```

This creates:
- Pod: `mew-pod`
- Container: `mew-db` (PostgreSQL 15)
- Port: 5432 → localhost
- Volume: `mew-postgres-data` (persistent)

### Full Stack in Podman

```bash
./podman-full.sh
```

Runs both API and PostgreSQL in containers.

### Check Status

```bash
# List pods
podman pod ps

# List containers
podman ps

# View logs
podman logs mew-db
podman logs mew-api

# Connect to database
podman exec -it mew-db psql -U mew_user -d mew_assistant
```

### Stop Everything

```bash
./podman-stop.sh
```

### Using Podman Compose

```bash
pip install podman-compose
podman-compose up -d
podman-compose down
```

---

## 🏗️ Project Structure

```
mew-assistant/
├── app/
│   ├── database/         # SQLAlchemy models & connection
│   │   ├── connection.py # Database setup
│   │   └── models.py     # Session, Message, Summary models
│   ├── routers/          # FastAPI endpoints
│   │   ├── session.py    # Session management
│   │   ├── message.py    # Message ingestion
│   │   └── summary.py    # Summary generation
│   ├── schemas/          # Pydantic validation models
│   │   ├── session.py
│   │   ├── message.py
│   │   └── summary.py
│   ├── services/         # Business logic
│   │   ├── session_service.py
│   │   ├── message_service.py
│   │   └── summary_service.py
│   ├── utils/            # Utilities
│   │   ├── cooldown.py   # Cooldown logic
│   │   └── priority.py   # Priority handling
│   └── main.py           # FastAPI app
├── agent-cards/yaml/     # AGNTCY.org agent cards
│   ├── scheduling-agent.yaml
│   ├── tutoring-agent.yaml
│   └── caregiver-agent.yaml
├── podman-start.sh       # Start PostgreSQL
├── podman-stop.sh        # Stop containers
├── podman-full.sh        # Full stack
├── setup.sh              # Automated setup
├── docker-compose.yml    # Compose file
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

---

## 🤝 Contributing

### Prerequisites

- Python 3.9+
- Git
- Podman (optional, for PostgreSQL)

### Development Setup

1. **Fork and clone**:
```bash
git clone https://github.com/your-username/mew-assistant.git
cd mew-assistant
```

2. **Install dependencies**:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: Development tools
pip install pytest pytest-asyncio black flake8 mypy
```

3. **Start database**:
```bash
# Option A: Podman
./podman-start.sh

# Option B: SQLite (auto-configured)
```

4. **Run the app**:
```bash
uvicorn app.main:app --reload
```

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings with examples
- Maximum line length: 100 characters

**Example:**
```python
def create_session(self, session_data: SessionCreate) -> SessionModel:
    """
    Create a new session with cooldown and priority logic.
    
    Args:
        session_data: Session creation data
        
    Returns:
        Created session object
        
    Example:
        >>> service = SessionService(db)
        >>> session = service.create_session(session_data)
    """
    # Implementation
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

---

## 🐛 Troubleshooting

### Database Connection Error

**Podman:**
```bash
# Check status
podman ps

# Restart
./podman-stop.sh
./podman-start.sh
```

**SQLite:**
```bash
# Delete and recreate
rm mew_assistant.db
python -c "from app.database import engine, Base; Base.metadata.create_all(engine)"
```

### Port Already in Use

```bash
# Use different port
uvicorn app.main:app --reload --port 8001

# Or check what's using port 8000
lsof -i :8000
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Podman Issues

```bash
# Check Podman installation
podman --version

# Reset everything
./podman-stop.sh
podman volume rm mew-postgres-data
./podman-start.sh
```

---

## 📖 Database Schema

### Tables

**sessions**
- `id` - Primary key
- `user_id` - User identifier
- `session_type` - tutoring, scheduling, caregiver_summary
- `status` - pending, confirmed, active, completed, cancelled
- `priority` - low, normal, high, urgent
- `cooldown_until` - Cooldown expiration timestamp
- `scheduled_at` - Scheduled time
- `created_at`, `confirmed_at`, `completed_at` - Timestamps

**messages**
- `id` - Primary key
- `session_id` - Foreign key to sessions
- `channel` - email, sms, whatsapp, web
- `sender` - Email address or phone number
- `subject` - Message subject (email only)
- `body` - Message content
- `processed` - Processing status
- `received_at`, `processed_at` - Timestamps

**caregiver_summaries**
- `id` - Primary key
- `session_id` - Foreign key to sessions
- `user_id` - User identifier
- `summary_text` - Generated summary
- `key_points` - JSON array of highlights
- `recommendations` - JSON array of suggestions
- `period_start`, `period_end` - Summary time range
- `generated_at` - Generation timestamp

---

## 🎴 AGNTCY.org Agent Cards

Three specialized agent cards are included in `agent-cards/yaml/`:

1. **Scheduling Agent** - Priority management, conflict detection
2. **Tutoring Agent** - Session coordination, progress tracking
3. **Caregiver Agent** - Summary generation, insights

---

## 🚀 Deployment

### Production with Podman

```bash
# 1. Clone repository
git clone https://github.com/your-org/mew-assistant.git
cd mew-assistant

# 2. Configure environment
cp .env.example .env
# Edit .env with production settings

# 3. Start services
./podman-full.sh

# 4. Set up auto-restart
podman generate systemd --new --name mew-pod > mew-assistant.service
sudo mv mew-assistant.service /etc/systemd/system/
sudo systemctl enable mew-assistant
sudo systemctl start mew-assistant
```

### Using Reverse Proxy

**Nginx:**
```nginx
server {
    listen 80;
    server_name mew-assistant.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔒 Security

- Never commit `.env` files
- Use environment variables for secrets
- Configure CORS appropriately for production
- Enable HTTPS in production
- Regularly update dependencies
- Use strong database passwords
- Implement rate limiting for production

---

## 📊 Performance

### Database Optimization

- Connection pooling enabled (PostgreSQL)
- Indexes on frequently queried fields
- Async operations for I/O
- Query optimization with SQLAlchemy

### Caching (Optional)

Add Redis for improved performance:
```bash
# Start Redis in Podman
podman run -d --name mew-redis -p 6379:6379 redis:7-alpine

# Update .env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

---

## 📄 License

MIT License - Free and open source

---

## 🙏 Acknowledgments

Built with ❤️ for special needs families and caregivers.

**Technologies:**
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Podman](https://podman.io/) - Container engine
- [PostgreSQL](https://www.postgresql.org/) - Database
- [AGNTCY.org](https://agntcy.org/) - Agent card specifications

---

## 📞 Support

- **Issues**: https://github.com/your-org/mew-assistant/issues
- **Discussions**: https://github.com/your-org/mew-assistant/discussions
- **Email**: support@mew-assistant.org

---

## 🎉 Ready to Start!

Visit http://localhost:8000/docs to explore the interactive API documentation and start building features for special needs families!

---

## 🔌 Phase 5: External Integrations

Mew Assistant integrates with multiple external services for enhanced functionality:

### Email Integration (SMTP/IMAP)
- **Send notifications**: Reminders, summaries, alerts
- **Receive messages**: Process incoming emails automatically
- **Configuration**:
  ```bash
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  ```

### SMS Integration (Twilio)
- **Send SMS**: Quick reminders and alerts
- **Receive SMS**: Process incoming text messages via webhooks
- **Configuration**:
  ```bash
  TWILIO_ACCOUNT_SID=your-account-sid
  TWILIO_AUTH_TOKEN=your-auth-token
  TWILIO_PHONE_NUMBER=+1234567890
  ```
- **Webhook Setup**: Configure in Twilio Console → Phone Numbers → Messaging
  ```
  Webhook URL: https://your-domain.com/webhooks/sms/incoming
  HTTP Method: POST
  ```

### WhatsApp Integration (Twilio)
- **Rich messaging**: Formatted messages with emojis
- **Media support**: Send images and documents
- **Configuration**:
  ```bash
  TWILIO_WHATSAPP_NUMBER=+1234567890
  ```
- **Webhook Setup**: Twilio Console → Programmable Messaging → WhatsApp
  ```
  Webhook URL: https://your-domain.com/webhooks/whatsapp/incoming
  ```

### AI Integration (OpenAI/Anthropic)
- **Smart summaries**: Auto-generate caregiver reports
- **Intent analysis**: Understand incoming messages
- **Conversational responses**: Natural language interactions
- **Configuration**:
  ```bash
  OPENAI_API_KEY=sk-your-key
  ANTHROPIC_API_KEY=sk-ant-your-key
  AI_MODEL=gpt-4
  ```

### Google Calendar Integration
- **Event creation**: Auto-schedule appointments
- **Reminders**: Sync with Google Calendar notifications
- **Configuration**:
  ```bash
  GOOGLE_CREDENTIALS_FILE=path/to/credentials.json
  GOOGLE_CALENDAR_ID=primary
  ```
- **Setup**: Create service account in Google Cloud Console

### Integration Usage Examples

**Send Email Reminder:**
```python
from app.integrations import EmailIntegration

email_integration = EmailIntegration()
await email_integration.send_notification(
    to_email="caregiver@example.com",
    notification_type="reminder",
    data={
        "title": "Tutoring Session",
        "time": "3:00 PM",
        "details": "Math homework help"
    }
)
```

**Send WhatsApp Summary:**
```python
from app.integrations import WhatsAppIntegration

whatsapp = WhatsAppIntegration()
await whatsapp.send_summary(
    to_number="+1234567890",
    summary_data={
        "date": "2024-01-15",
        "content": "Completed 3 activities today..."
    }
)
```

**Generate AI Summary:**
```python
from app.integrations import AIIntegration

ai = AIIntegration()
result = await ai.generate_summary(
    content="Activity logs for the day...",
    summary_type="daily"
)
```

### Webhook Endpoints

All webhook endpoints are available at `/webhooks/*`:

- **POST** `/webhooks/sms/incoming` - Receive incoming SMS
- **POST** `/webhooks/whatsapp/incoming` - Receive incoming WhatsApp messages
- **GET** `/webhooks/sms/status` - SMS delivery status updates
- **GET** `/webhooks/health` - Webhook health check

### Testing Webhooks Locally

Use ngrok or similar tool to expose localhost for webhook testing:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start your app
uvicorn app.main:app --reload

# In another terminal, expose port 8000
ngrok http 8000

# Use the ngrok URL in Twilio webhook configuration
# Example: https://abc123.ngrok.io/webhooks/sms/incoming
```

---


---

## 📅 Calendar Integration

Mew Assistant supports multiple calendar providers for managing appointments and schedules.

### Supported Providers

- **Google Calendar**: OAuth2-based integration
- **Apple iCloud Calendar**: CalDAV protocol support
- **Microsoft Outlook Calendar**: Microsoft Graph API integration

### Calendar API Endpoints

#### 1. Connect Calendar Provider

```bash
# Google Calendar
curl -X POST "http://localhost:8000/calendar/connect/google" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "token": "your_oauth2_token"
    }
  }'

# Apple iCloud Calendar
curl -X POST "http://localhost:8000/calendar/connect/apple" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "username": "your@icloud.com",
      "app_specific_password": "xxxx-xxxx-xxxx-xxxx",
      "server": "https://caldav.icloud.com"
    }
  }'
```

#### 2. Create Calendar Event

```bash
curl -X POST "http://localhost:8000/calendar/events" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "title": "Therapy Session with Emma",
    "start_time": "2024-01-15T14:00:00Z",
    "end_time": "2024-01-15T15:00:00Z",
    "description": "Weekly therapy session",
    "location": "123 Main St, Suite 200",
    "attendees": ["therapist@example.com"],
    "reminder_minutes": 30
  }'
```

#### 3. Get Upcoming Events

```bash
curl -X POST "http://localhost:8000/calendar/events/upcoming" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "days_ahead": 7
  }'
```

---

## 📱 Mobile Device Integration

Support for iOS and Android mobile devices with push notifications and deep linking.

### Supported Platforms

- **iOS**: Apple Push Notification Service (APNs)
- **Android**: Firebase Cloud Messaging (FCM)

### Mobile API Endpoints

#### 1. Register Device

```bash
curl -X POST "http://localhost:8000/mobile/register" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "device_token": "your_device_token_here",
    "device_info": {
      "model": "iPhone 14 Pro",
      "os_version": "17.1",
      "app_version": "1.0.0"
    }
  }'
```

#### 2. Send Push Notification

```bash
curl -X POST "http://localhost:8000/mobile/notifications/send" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "device_token": "your_device_token_here",
    "title": "Upcoming Therapy Session",
    "body": "Your therapy session starts in 30 minutes",
    "data": {
      "session_id": "12345",
      "type": "reminder"
    },
    "badge": 1,
    "sound": "default"
  }'
```

#### 3. Generate Deep Link

```bash
curl -X POST "http://localhost:8000/mobile/deeplink" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "screen": "session/details",
    "params": {
      "session_id": "12345"
    }
  }'
```

**Response:**
```json
{
  "ios_link": "mewassistant://session/details?session_id=12345",
  "android_link": "mewassistant://session/details?session_id=12345",
  "universal_link": "https://app.mewassistant.com/session/details?session_id=12345",
  "success": true
}
```

#### 4. Schedule Reminder

```bash
curl -X POST "http://localhost:8000/mobile/reminders/schedule" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "device_token": "your_device_token_here",
    "title": "Daily Medication Reminder",
    "body": "Time to take your morning medication",
    "scheduled_time": "2024-01-15T08:00:00Z",
    "data": {
      "medication_id": "med_123"
    }
  }'
```

### Mobile Setup Requirements

#### iOS (APNs)
1. Apple Developer Account
2. APNs Authentication Key (.p8 file)
3. Key ID, Team ID, and Bundle ID

**Configuration:**
```bash
export APNS_KEY_PATH="/path/to/AuthKey_KEYID.p8"
export APNS_KEY_ID="YOUR_KEY_ID"
export APNS_TEAM_ID="YOUR_TEAM_ID"
export APNS_TOPIC="com.mewassistant.app"
```

#### Android (FCM)
1. Firebase project with Cloud Messaging enabled
2. Service account JSON file

**Configuration:**
```bash
export FCM_SERVICE_ACCOUNT="/path/to/firebase-service-account.json"
```

