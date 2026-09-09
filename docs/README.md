# 📚 Mew Assistant Documentation

Welcome to the Mew Assistant documentation directory!

---

## 📖 Documentation Index

### For Developers
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - the whole-app reference: router
  layer map, data model, services layer, deployment topology, and the
  trigger-list for keeping it current
- **[OAUTH_SETUP.md](OAUTH_SETUP.md)** - WorkOS AuthKit sign-in setup, plus
  the separate Google Calendar-connect OAuth flow
- **[THREE_PERSONA_SCHEDULING.md](THREE_PERSONA_SCHEDULING.md)** - the
  parent/kid/provider request-and-approval loop, `POST /requests`, the
  rule engine
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - tracked, un-fixed bugs
- **[SECURITY.md](SECURITY.md)** - bot-protection reference
- **[integrations/SETUP_GUIDE.md](integrations/SETUP_GUIDE.md)** -
  Email/SMS/WhatsApp/AI/Calendar integration setup
- **[../CHANGELOG.md](../CHANGELOG.md)** - version history and changes
- **[WHATS_NEW.md](WHATS_NEW.md)** - the same history, written for a
  parent rather than a developer
- **[../CLAUDE.md](../CLAUDE.md)** - git flow, CI/CD gates, deployment

### Historical / superseded (kept for reference only)
- **[SIRI_SETUP.md](SIRI_SETUP.md)** and
  **[SIRI_SETUP_GUIDE.md](SIRI_SETUP_GUIDE.md)** - describe an earlier
  Siri/Shortcuts integration mechanism; see
  `app/routers/voice_platforms.py` for the current webhook-based one
- **[RBAC_SETUP_COMPLETE.md](RBAC_SETUP_COMPLETE.md)** - a point-in-time
  RBAC implementation note; see `app/database/models.py`'s `UserRole`
  enum for the roles that exist today

### API Documentation
- **Interactive API docs:** run the app and visit `/docs`
- **OpenAPI Spec:** `../openapi.json`

---

## 🗂️ Documentation Structure

```
/
├── README.md                # Project overview
├── CHANGELOG.md             # Version history
├── CLAUDE.md                # Git flow, CI/CD, deployment
└── docs/
    ├── README.md            # This file
    ├── ARCHITECTURE.md
    ├── WHATS_NEW.md
    ├── OAUTH_SETUP.md
    ├── THREE_PERSONA_SCHEDULING.md
    ├── KNOWN_ISSUES.md
    ├── SECURITY.md
    ├── RBAC_SETUP_COMPLETE.md   # historical/superseded
    ├── SIRI_SETUP.md            # historical/superseded
    ├── SIRI_SETUP_GUIDE.md      # historical/superseded
    ├── integrations/
    │   └── SETUP_GUIDE.md
    └── features/                # per-feature intent/spec/plan artifacts
```

---

## 🚀 Quick Links

### Development
- **Repository:** https://github.com/skakumanu/mew-assistant

---

## 📝 Contributing to Documentation

When updating documentation:
1. Keep guides focused and concise
2. Use clear headings and sections
3. Include code examples where helpful
4. Update `CHANGELOG.md` for significant changes
5. Confirm claims against the code, not against a filename's implication

---

## ❓ Need Help?

- Check the relevant guide above
- View API docs at `/docs` when the app is running
- Review `CHANGELOG.md` for recent changes
