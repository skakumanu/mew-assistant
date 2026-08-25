# CLAUDE.md

Instructions for Claude Code (and any other agent) working in this repository.

## Git Flow — mandatory

- `master` and `develop` are protected. Never commit directly to either.
- New work branches from `develop`: `feature/<name>`, `hotfix/<name>`,
  or `release/<name>`. `.github/workflows/gitflow.yml` enforces branch
  naming (`^(main|develop|feature/.+|release/.+|hotfix/.+)$`) on every
  push/PR to `main`/`develop`.
- Open the PR against `develop` first. `develop` → `master` promotion is a
  separate PR once the change is verified.
- `.github/workflows/sync-develop.yml` runs after every push to `master` and
  opens an automatic PR back into `develop` if `develop` is missing commits
  `master` already has (e.g. from a hotfix merged straight to `master`).
- `.pre-commit-config.yaml`'s `no-commit-to-branch` hook backs this up
  locally for both `develop` and `master`.

## CI/CD gates

Every push/PR runs `.github/workflows/ci-cd.yml`, five parallel jobs:

1. `test` — `pytest tests/ -v --cov=app --cov-report=term-missing`
2. `lint` — flake8, two passes: a hard-fail syntax-error check
   (`E9,F63,F7,F82`), then a warning-only complexity/line-length pass
   (`--max-complexity=10 --max-line-length=119`, matching `.flake8`)
3. `osv_scan` — Google's OSV Scanner against `requirements.txt`
4. `security` — `bandit -r app -q`
5. `secret_scan` — Gitleaks (see `.gitleaks.toml`/`.gitleaksignore`)

On push to `master` (or manual dispatch), once all five pass, `deploy_fly`
deploys to Fly.io (`flyctl deploy --remote-only`) and polls `/health` for up
to 3 minutes before declaring the deploy done.

## Deployment

The app deploys to **Fly.io** (see `fly.toml`, `Procfile`, `runtime.txt`).
The Fly build reuses the existing multi-stage `Dockerfile` unchanged.
Secrets (`DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, OAuth/Twilio/SMTP
keys) are set via `flyctl secrets set`, not committed anywhere. CI needs a
`FLY_API_TOKEN` repository secret to deploy.

Before touching deploy config, know that this repo *also* still has legacy
Azure IaC and docs (`infrastructure/azure/`, root `*.bicep` files,
`docs/DEPLOYMENT_GUIDE.md`, etc.) — those are dormant and no longer wired
into CI, kept for reference/teardown only. Don't resurrect them without
checking with the repo owner first.

## Before committing

- Run `pytest tests/` and `flake8 app tests` locally — CI runs the same
  checks and will block on the hard-fail lint pass or test failures.
- Never commit `.env`, real secrets, or `.db` files — `.gitignore` should
  already cover these; double-check `git status` before staging.
- Use conventional commit style (`feat:`, `fix:`, `chore:`, `docs:`, etc.).
