# Mew Assistant

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Podman](https://img.shields.io/badge/Podman-ready-purple.svg)](https://podman.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Mew Assistant** is a FastAPI-based modular assistant designed for special needs families. It supports scheduling, tutoring coordination, and caregiver summaries with multi-channel ingestion (email, SMS, WhatsApp).

---

## 🌟 Features

- **Session Management**: Schedule and manage tutoring, scheduling, and caregiver sessions
- **Multi-Channel Ingestion**: Accept messages via email, SMS, WhatsApp, and web forms
- **Cooldown Protection**: Prevent overwhelming families with intelligent request throttling
- **Priority Period Overrides**: Automatically escalate priority during peak times (7-9am, 3-6pm, 7-9pm)
- **Caregiver Summaries**: Generate actionable insights and recommendations
- **PostgreSQL/SQLite**: Flexible database support
- **RESTful API**: Clean, documented endpoints with OpenAPI/Swagger support
- **Podman Support**: Containerized PostgreSQL for easy deployment

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

### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mew/session` | Create new session |
| POST | `/mew/confirm` | Confirm session with cooldown |
| PATCH | `/mew/session/{id}` | Update session |
| GET | `/mew/session/{id}` | Get session details |
| GET | `/mew/sessions/user/{user_id}` | List user sessions |

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

**Full API Documentation**: http://localhost:8000/docs

---

## 🧪 API Examples

### Create a Session

```bash
curl -X POST "http://localhost:8000/mew/session" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "family_001",
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
  "user_id": "family_001",
  "session_type": "tutoring",
  "status": "pending",
  "priority": "normal",
  "title": "Math Homework Help",
  "cooldown_until": null,
  "in_cooldown": false
}
```

### Confirm Session

```bash
curl -X POST "http://localhost:8000/mew/confirm" \
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
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "family_001",
    "period_start": "2025-11-01T00:00:00Z",
    "period_end": "2025-11-13T23:59:59Z",
    "include_recommendations": true
  }'
```

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

# Optional: Multi-Channel Integration
EMAIL_ENABLED=false
SMS_ENABLED=false
WHATSAPP_ENABLED=false
```

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
