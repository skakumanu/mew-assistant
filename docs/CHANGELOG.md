# Changelog

All notable changes to Mew Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-13

### Added
- Initial release of Mew Assistant
- FastAPI-based REST API with OpenAPI documentation
- Session management with cooldown protection
- Multi-channel message ingestion (email, SMS, WhatsApp)
- Caregiver summary generation
- Priority period auto-escalation (morning prep, after-school, evening routine)
- PostgreSQL database support with SQLAlchemy ORM
- SQLite fallback for development
- Podman containerization support
- AGNTCY.org agent card specifications (3 agents)
- Comprehensive API documentation
- MIT License
- GitHub Actions CI/CD pipeline
- Unit test suite with pytest
- Code quality badges

### Features
- **Session Types**: tutoring, scheduling, caregiver_summary
- **Priority Levels**: low, normal, high, urgent
- **Channels**: email, sms, whatsapp, web
- **Database**: Flexible PostgreSQL/SQLite support
- **Containerization**: Podman scripts for easy deployment

### Documentation
- Complete README with examples
- API reference with curl commands
- Podman deployment guide
- Contributing guidelines
- Architecture overview

## [Unreleased]

### Planned
- Authentication and authorization (JWT)
- Real-time notifications (WebSockets)
- Email/SMS integration (Twilio, SendGrid)
- Admin dashboard
- Calendar integrations
- AI/LLM enhancements for summaries
- Mobile app support
- Analytics and reporting

---

For more details, see the [GitHub repository](https://github.com/skakumanu/mew-assistant)
