# 🐱 Mew Assistant

> *An AI-powered family assistant for special needs families, designed to reduce overwhelm through intelligent scheduling, tutoring support, and caregiver summaries.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Azure](https://img.shields.io/badge/Azure-Deployed-0078D4.svg)](https://azure.microsoft.com)

---

## 🌟 What is Mew Assistant?

Mew is a **modular AI assistant** built specifically for families with special needs children. It helps parents manage:

✅ **Smart Scheduling** - Conflict detection, priority periods, cooldown logic  
✅ **Educational Tutoring** - Progress tracking, session summaries  
✅ **Caregiver Communication** - Daily summaries across multiple channels  
✅ **Multi-Channel Ingestion** - Email, SMS, WhatsApp support  
✅ **Voice Commands** - Siri, Alexa, Google Assistant, Tesla Grok integration  
✅ **Intelligent Auto-Approval** - Reduce parent notification fatigue  

## 🚀 Quick Start

### For Users (Customer Zero)

```bash
# 1. Visit the web app
https://mew-assistant-app.azurewebsites.net

# 2. Register via API or web interface
curl -X POST https://mew-assistant-app.azurewebsites.net/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "secure_password", "full_name": "Your Name", "role": "parent"}'

# 3. Follow the Customer Zero setup guide
```

📱 **Mobile Access**: [Complete Setup Guide](docs/GUIDE.md#customer-zero-setup)

### For Developers

```bash
# Clone the repository
git clone https://github.com/skakumanu/mew-assistant.git
cd mew-assistant

# Install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8888

# Or use Podman
./podman-start.sh
```

📖 **Full Developer Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [📖 User Guide](docs/GUIDE.md) | Quick start, features, API usage, voice commands |
| [💻 Development Guide](docs/DEVELOPMENT.md) | Architecture, contributing, testing, security |
| [☁️ Deployment & Operations](docs/DEPLOYMENT_OPERATIONS.md) | Azure setup, infrastructure, cost analysis |
| [🏢 Project Management](docs/PROJECT_MANAGEMENT.md) | Governance, non-profit transition, roadmap |
| [📝 Changelog](docs/CHANGELOG_HISTORY.md) | Version history and session summaries |

## 🎯 Key Features

### 🗓️ Intelligent Scheduling
- **Conflict Detection**: Automatically identifies scheduling conflicts
- **Priority Periods**: Override cooldowns during critical times (therapy, medical appointments)
- **Cooldown Logic**: Prevents notification fatigue with smart timing
- **Multi-Timezone Support**: Works across different time zones

### 🎤 Voice Integration
- **Multi-Platform**: Siri Shortcuts, Alexa Skills, Google Assistant, Tesla Grok
- **100+ Languages**: Automatic language detection and translation
- **Voice Onboarding**: Register and authenticate using voice commands
- **Natural Language**: "Schedule speech therapy tomorrow at 3pm"

### 👨‍👩‍👧‍👦 Family-Friendly
- **Kid Mode**: Children can suggest schedule changes
- **Smart Approval**: Auto-approve routine requests, batch non-urgent items
- **Parental Controls**: Granular permissions and approval workflows
- **Safety First**: COPPA compliant, encrypted data, privacy by design

### 🔌 Multi-Channel Communication
- Email (Gmail, Outlook)
- SMS (Twilio, bandwidth.com)
- WhatsApp Business
- Voice Assistants
- Mobile Apps (iOS/Android)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Voice Platforms                     │
│         (Siri, Alexa, Google, Tesla Grok)           │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              FastAPI Application                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  Routers: Auth | Session | Message | Voice  │   │
│  ├─────────────────────────────────────────────┤   │
│  │  Services: AI | Schedule | Calendar         │   │
│  ├─────────────────────────────────────────────┤   │
│  │  Integrations: Email | SMS | WhatsApp       │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         Azure Infrastructure                         │
│  • Container Apps (auto-scaling)                    │
│  • PostgreSQL (encrypted at rest)                   │
│  • Key Vault (secrets management)                   │
│  • Storage Blob (backups)                           │
│  • Application Insights (monitoring)                │
└─────────────────────────────────────────────────────┘
```

## 💡 Use Cases

1. **Therapy Scheduling**: "Schedule OT tomorrow at 2pm"
2. **Medication Reminders**: "Remind me about medication at 8am daily"
3. **School Coordination**: "Email teacher about IEP meeting next week"
4. **Caregiver Updates**: "Send daily summary to grandma at 7pm"
5. **Emergency Overrides**: "Cancel all non-urgent appointments today"

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL (Azure Flexible Server)
- **AI/ML**: OpenAI GPT, Azure Cognitive Services
- **Cloud**: Azure (Container Apps, Key Vault, Storage, Application Insights)
- **Voice**: Siri Shortcuts, Alexa Skills Kit, Google Actions, xAI API
- **Calendar**: Google Calendar API, Apple Calendar (CalDAV)
- **Communication**: Twilio, SendGrid, WhatsApp Business API
- **Infrastructure**: Bicep, GitHub Actions CI/CD

## 🤝 Contributing

We welcome contributions! See [DEVELOPMENT.md](docs/DEVELOPMENT.md#contributing-guidelines) for details.

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/mew-assistant.git

# Create feature branch
git flow feature start my-new-feature

# Make changes, commit, and push
git flow feature finish my-new-feature

# Submit Pull Request
```

## 🔒 Security & Privacy

- **HIPAA-Ready**: Encrypted data at rest and in transit
- **COPPA Compliant**: Parental consent for children under 13
- **FERPA Aligned**: Educational record protection
- **GDPR Ready**: Data portability and right to deletion
- **SOC 2 Controls**: Audit logging and access controls

See [SECURITY_PRIVACY_COMPLIANCE.md](docs/DEVELOPMENT.md#security--compliance) for details.

## 📊 Cost Estimation

**Customer Zero (Single Family)**:
- Azure Container Apps: $0 (Free tier - 180k vCPU-seconds/month)
- PostgreSQL Burstable B1ms: ~$12/month
- Storage & Backups: ~$1/month
- **Total**: ~$13/month

**Scale (100 families)**: ~$50-75/month  
**Scale (1000 families)**: ~$200-300/month

See [COST_ANALYSIS.md](docs/DEPLOYMENT_OPERATIONS.md#cost-analysis) for detailed breakdown.

## 🗺️ Roadmap

- [x] Core FastAPI application
- [x] PostgreSQL with encryption
- [x] Azure deployment
- [x] Voice assistant integration
- [x] Calendar integration (Apple/Google)
- [ ] Mobile apps (iOS/Android)
- [ ] Enhanced AI training
- [ ] Community features
- [ ] Non-profit transition

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/skakumanu/mew-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/skakumanu/mew-assistant/discussions)
- **Email**: Coming soon after non-profit setup

## 🙏 Acknowledgments

Built with ❤️ for special needs families by the community.

Special thanks to:
- AGNTCY.org framework contributors
- Open source community
- Early adopters and testers

---

**Ready to get started?** → [Quick Start Guide](docs/GUIDE.md#quick-start)

**Want to contribute?** → [Development Guide](docs/DEVELOPMENT.md)

**Need help?** → [User Guide](docs/GUIDE.md) | [GitHub Issues](https://github.com/skakumanu/mew-assistant/issues)
