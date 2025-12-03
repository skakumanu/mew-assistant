# 🐱 Mew Assistant

**AI-powered personal assistant with voice commands and calendar integration**

[![Status](https://img.shields.io/badge/status-live-success)](https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io)
[![Azure](https://img.shields.io/badge/azure-deployed-blue)](https://portal.azure.com)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)

---

## 🚀 Live Application

**URL:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io

- **Try it:** [Sign in with Google](https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login)
- **API Docs:** [Interactive API Documentation](https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/docs)
- **Calendar:** [View Your Calendar](https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/calendar)

---

## ✨ Features

### Currently Available
- ✅ **OAuth Sign-In** - Google (Microsoft & Apple coming soon)
- ✅ **Calendar Integration** - View Google Calendar events
- ✅ **Secure Authentication** - JWT tokens with 30-day expiry
- ✅ **Multi-Device** - Works on phone, tablet, computer
- ✅ **Real-Time Updates** - Calendar syncs automatically

### Coming Soon
- 🎙️ **Siri Integration** - "Hey Siri, what's on my schedule?"
- 📅 **Add Events** - Create calendar events via voice
- 🔔 **Smart Reminders** - AI-powered event reminders
- 🤖 **AI Assistant** - Natural language calendar management

---

## 📚 Documentation

### Quick Start
- **[User Guide](USER_GUIDE.md)** - How to use Mew Assistant (for end users)
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Azure deployment & infrastructure
- **[OAuth Setup](OAUTH_SETUP.md)** - Configure Google, Microsoft, and Apple sign-in

### Additional Resources
- **[Changelog](CHANGELOG.md)** - Version history and changes
- **[Siri Setup](SIRI_SETUP_GUIDE.md)** - Configure iOS Shortcuts (coming soon)
- **[API Documentation](https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/docs)** - Interactive API docs

---

## 🏗️ Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL (Azure Flexible Server)
- **ORM:** SQLAlchemy
- **Authentication:** OAuth 2.0 + JWT
- **API Integrations:** Google Calendar API

### Infrastructure
- **Cloud:** Azure Container Apps
- **Registry:** Azure Container Registry
- **Secrets:** Azure Key Vault
- **Identity:** Managed Identity
- **Scaling:** Auto-scale (1-3 replicas)

### Security
- HTTPS-only connections
- Secrets stored in Azure Key Vault
- Input validation & sanitization
- Rate limiting
- CORS configuration

---

## 🚀 Getting Started

### For End Users

**3-minute setup:**

1. **Sign In:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
2. **Click "Sign in with Google"**
3. **Grant calendar permission**
4. **Done!** View your calendar instantly

See [USER_GUIDE.md](USER_GUIDE.md) for detailed instructions.

### For Developers

**Local Development:**

```bash
# Clone repository
git clone https://github.com/skakumanu/mew-assistant.git
cd mew-assistant

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
python run_migration.py

# Start development server
uvicorn app.main:app --reload --port 8888
```

**Docker:**

```bash
# Build image
docker build -t mew-assistant .

# Run container
docker run -p 8888:8000 --env-file .env mew-assistant
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment.

---

## 🔐 OAuth Configuration

### Google OAuth (Working ✅)
- Configured in Google Cloud Console
- Calendar API enabled
- Credentials stored in Azure Key Vault

### Microsoft OAuth (Ready ⏳)
- Awaiting Azure AD app registration
- See [OAUTH_SETUP.md](OAUTH_SETUP.md) for setup instructions

### Apple Sign In (Ready ⏳)
- Awaiting Apple Developer configuration
- See [OAUTH_SETUP.md](OAUTH_SETUP.md) for setup instructions

---

## 📊 Project Status

### Current Version: 1.1.0

| Feature | Status | Notes |
|---------|--------|-------|
| Google OAuth | ✅ Live | Fully functional |
| Calendar Viewer | ✅ Live | Read-only access |
| Microsoft OAuth | ⏳ Ready | Needs setup (10 min) |
| Apple Sign In | ⏳ Ready | Needs setup (20 min) |
| Siri Shortcuts | 🔨 In Progress | 2-3 weeks |
| Add Calendar Events | 📋 Planned | 3-4 weeks |
| AI Assistant | 📋 Planned | Q1 2026 |

**Legend:** ✅ Live | ⏳ Ready | 🔨 In Progress | 📋 Planned

---

## 🧪 Testing

### Manual Testing

**Health Check:**
```bash
curl https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/health
```

**OAuth Flow:**
1. Visit: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
2. Click "Sign in with Google"
3. Verify successful login

**Calendar View:**
1. After login, go to: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/calendar
2. Click "Show My Events"
3. Verify events display

### Automated Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

---

## 🤝 Contributing

This is currently a private project for initial customer testing.

**If you're a test user:**
- Report bugs via the admin
- Request features
- Share feedback

**For developers:**
- Follow existing code style
- Write tests for new features
- Update documentation

---

## 📝 License

See [LICENSE](LICENSE) file for details.

---

## 📞 Support

### For Users
- See [USER_GUIDE.md](USER_GUIDE.md) troubleshooting section
- Check [CHANGELOG.md](CHANGELOG.md) for recent updates

### For Developers
- Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Check container logs in Azure Portal
- Verify environment variables and secrets

### Contact
- **GitHub:** https://github.com/skakumanu/mew-assistant
- **Email:** Contact admin for support

---

## 🎯 Roadmap

### Phase 1: Core Calendar (✅ Complete)
- [x] OAuth authentication (Google)
- [x] Calendar integration (read-only)
- [x] Web interface
- [x] Azure deployment

### Phase 2: Multi-Provider (⏳ Current)
- [x] Google OAuth ✅
- [ ] Microsoft OAuth (ready for setup)
- [ ] Apple Sign In (ready for setup)

### Phase 3: iOS Integration (🔨 In Progress)
- [ ] Siri Shortcuts
- [ ] Voice commands
- [ ] iOS app (optional)

### Phase 4: Advanced Features (📋 Planned)
- [ ] Calendar write access
- [ ] AI-powered scheduling
- [ ] Smart reminders
- [ ] Natural language processing

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Authlib](https://authlib.org/) - OAuth library
- [Azure](https://azure.microsoft.com/) - Cloud infrastructure
- [Google Calendar API](https://developers.google.com/calendar) - Calendar integration

---

**🐱 Mew Assistant - Your AI-powered personal assistant**

*Making calendar management simple, smart, and voice-activated*

