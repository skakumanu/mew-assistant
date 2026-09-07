# 🐱 Mew Assistant

**A scheduling assistant for special-needs families, shared by a parent
(or guardian), a kid, and their service providers.**

---

## What it is

Mew Assistant is a three-persona scheduling app, not a general calendar
app or a chatbot. A parent declares a set of rules once. A kid or a
service provider proposes a change through a single write path
(`POST /requests`); a deterministic rule engine
(`app/services/rule_engine.py`) evaluates it immediately — anything that
satisfies every active rule is applied on the spot and logged quietly,
and anything that doesn't reaches the parent as one card with three
compliant alternatives already attached, approved in one tap.

"Parent" and "guardian" are interchangeable throughout: the same
handlers answer on both the `/parent` and `/guardian` route prefixes, so
a family that uses one word never sees the other in a URL.

See [`docs/THREE_PERSONA_SCHEDULING.md`](docs/THREE_PERSONA_SCHEDULING.md)
for the full request/approval loop and code map.

---

## Sign-in and deployment

- **Sign-in:** [WorkOS AuthKit](https://workos.com/docs/authkit) (hosted
  UI, no per-provider code in this app) — email/password, Google,
  Microsoft, Apple, and passwordless magic-code sign-in. See
  [`app/routers/oauth_workos.py`](app/routers/oauth_workos.py).
- **Calendar connect:** a separate, unrelated Google Cloud OAuth flow
  lets a parent grant Mew read access to a provider's Google Calendar
  once already signed in — see
  [`app/routers/calendar_oauth.py`](app/routers/calendar_oauth.py) and
  [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md) for setup of both flows.
- **Deployment:** [Fly.io](https://fly.io) (`fly.toml`), app
  `mew-assistant`, region `iad`, health-checked at `/health`. CI
  (`.github/workflows/ci-cd.yml`'s `deploy_fly` job) deploys on push to
  `master` once tests, lint, security, and secret scans all pass. See
  `CLAUDE.md`'s Deployment section for details.

---

## Features (as of `CHANGELOG.md`'s `1.1.0` entry)

| Feature | Status | Notes |
|---------|--------|-------|
| Three-persona scheduling (parent/kid/provider) | ✅ Shipped | Deterministic rule engine, `POST /requests` sole write path |
| Parent approval with compliant alternatives | ✅ Shipped | `POST /parent/approvals/{id}/choose` |
| Service provider sessions view | ✅ Shipped | `GET /provider/sessions`, scoped to the caller's org |
| Calendar sync (Google OAuth + ICS) | ✅ Shipped | Idempotent pull, write-back on approved changes |
| Voice requests | ✅ Shipped (request-only) | `POST /voice/requests` reads a request back; can never approve |
| Notifications (email/SMS) | ✅ Shipped | Locale-keyed, best-effort delivery |
| Onboarding setup | ✅ Shipped | `POST /onboarding/setup`, idempotent |
| Sign-in via WorkOS AuthKit | ✅ Shipped | HttpOnly session cookie, `Authorization` header still wins |
| Internationalization (en/es/hi/ar) | ✅ Shipped | `hi`/`ar` are unreviewed machine translations |
| Voice command pipeline (`POST /voice/command`) | 🐛 Known broken | See `docs/KNOWN_ISSUES.md` |

See `CHANGELOG.md` for the full, dated history.

---

## For developers

**Local development:**

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
# Edit .env with your credentials (WorkOS, Google Calendar OAuth, etc.)

# Start development server
uvicorn app.main:app --reload --port 8888
```

**Docker:**

```bash
docker build -t mew-assistant .
docker run -p 8888:8000 --env-file .env mew-assistant
```

**Testing:**

```bash
pytest tests/
flake8 app tests
```

See `CLAUDE.md` for the full git-flow, CI/CD gate, and deployment
conventions this repo follows.

---

## Documentation

- [`CHANGELOG.md`](CHANGELOG.md) — version history
- [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md) — WorkOS sign-in and
  Google Calendar OAuth setup
- [`docs/THREE_PERSONA_SCHEDULING.md`](docs/THREE_PERSONA_SCHEDULING.md) —
  the request/rule/approval loop and code map
- [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) — tracked, un-fixed bugs
- [`CLAUDE.md`](CLAUDE.md) — git flow, CI/CD gates, and deployment

---

## License

See [LICENSE](LICENSE) file for details.

---

**🐱 Mew Assistant** — one schedule, three people, almost no decisions.
