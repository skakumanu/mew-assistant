# 📚 Documentation Index

**Last Updated:** September 7, 2026

---

## 📖 All Documentation Files

### 🎯 Start Here

| Document | Audience | Purpose |
|----------|----------|---------|
| **[README.md](README.md)** | Everyone | Project overview, sign-in/deploy summary, feature status |
| **[CLAUDE.md](CLAUDE.md)** | Developers | Git flow, CI/CD gates, deployment conventions |

---

### 🔐 Authentication & Calendar OAuth

| Document | Purpose |
|----------|---------|
| **[docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)** | WorkOS AuthKit sign-in setup, plus the separate Google Calendar-connect OAuth flow |

---

### 📅 Scheduling

| Document | Purpose |
|----------|---------|
| **[docs/THREE_PERSONA_SCHEDULING.md](docs/THREE_PERSONA_SCHEDULING.md)** | The parent/kid/provider request-and-approval loop, `POST /requests`, the rule engine |

---

### 🏗️ Architecture

| Document | Purpose |
|----------|---------|
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Whole-app reference: router layer map, data model, services layer, deployment topology, and the trigger-list for keeping it current |

---

### 📱 Mobile & Voice

| Document | Purpose | Status |
|----------|---------|--------|
| **[docs/SIRI_SETUP.md](docs/SIRI_SETUP.md)** | Siri/Shortcuts integration | Historical/superseded — see banner |
| **[docs/SIRI_SETUP_GUIDE.md](docs/SIRI_SETUP_GUIDE.md)** | Siri/Shortcuts integration | Historical/superseded — see banner |

---

### 🔒 Security & Access Control

| Document | Purpose |
|----------|---------|
| **[docs/SECURITY.md](docs/SECURITY.md)** | Bot-protection reference |
| **[docs/RBAC_SETUP_COMPLETE.md](docs/RBAC_SETUP_COMPLETE.md)** | Historical RBAC implementation note — see banner; current roles live in `app/database/models.py`'s `UserRole` enum |

---

### 🔌 Integrations

| Document | Purpose |
|----------|---------|
| **[docs/integrations/SETUP_GUIDE.md](docs/integrations/SETUP_GUIDE.md)** | Email/SMS/WhatsApp/AI/Calendar integration setup |

---

### 🐛 Known Issues

| Document | Purpose |
|----------|---------|
| **[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)** | Tracked, un-fixed bugs (currently: the voice command pipeline) |

---

### 📝 Project Information

| Document | Purpose |
|----------|---------|
| **[CHANGELOG.md](CHANGELOG.md)** | Version history & bug fixes |
| **[docs/WHATS_NEW.md](docs/WHATS_NEW.md)** | The same history, written for a parent rather than a developer |
| **[LICENSE](LICENSE)** | Project license |

---

### 🗂️ `docs/README.md`

| Document | Purpose |
|----------|---------|
| **[docs/README.md](docs/README.md)** | Index of the `docs/` directory |

---

## 🚀 Quick Links by Task

### "I want to understand the app"
→ Read: [README.md](README.md), then
[docs/THREE_PERSONA_SCHEDULING.md](docs/THREE_PERSONA_SCHEDULING.md)

### "I want to set up sign-in or calendar OAuth"
→ Read: [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)

### "I want to deploy"
→ Read: [CLAUDE.md](CLAUDE.md) (Deployment section) and `fly.toml`

### "I want to see what changed"
→ Read: [CHANGELOG.md](CHANGELOG.md)

### "I want API documentation"
→ Run the app locally or on Fly.io and visit `/docs` (interactive,
generated from `openapi.json`)

---

## Current Structure

```
/
├── README.md                    # Project overview
├── CLAUDE.md                    # Git flow, CI/CD, deployment
├── CHANGELOG.md                 # Version history
├── DOCUMENTATION_INDEX.md       # This file
└── docs/
    ├── README.md
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
    ├── shortcuts/
    │   └── MewAssistant.shortcut
    └── features/                # per-feature intent/spec/plan artifacts
```

---

## ✅ Documentation Quality Standards

All documentation follows these principles:
- Reflects the app as it actually runs today (checked against the code,
  not assumed from filenames)
- Historical/superseded documents are labeled as such rather than left
  to be mistaken for current instructions
- Links only to files that exist in this repository
