# CLAUDE.md

Instructions for Claude Code (and any other agent) working in this repository.

## AI-native SDLC

Feature and bug-fix work in this repo runs through a six-phase loop, each
phase a dedicated agent, each handoff committing a version-controlled
Markdown artifact a human reviews before the next phase starts:

```
Plan → Design → Build → Test → Deploy → (dogfooding) → Maintain → back to Plan
```

| Phase | Agent | Reads | Writes | Human gate |
|---|---|---|---|---|
| Plan | `sdlc-plan` | the raw request | `docs/features/<slug>/intent.md` | accepts the problem as scoped |
| Design | `sdlc-design` | `intent.md` | `spec.md` | approves the concrete design |
| Build | `sdlc-build` | `spec.md` | `plan.md`, then code + tests, on a `feature/`/`hotfix/` branch | approves the plan and implementation |
| Test | `sdlc-test` | the branch, `spec.md`'s acceptance criteria | a verification report | accepts pass (or a known, accepted gap) |
| Deploy | `sdlc-deploy` | the tested branch | a PR + merge to `develop` | none needed for the `develop` merge itself |
| Maintain | `sdlc-maintain` | production feedback about a shipped feature | the *next* cycle's `intent.md` | closes the loop back to Plan |

**The production gate is `develop` → `master`, and it is never automatic.**
`master` auto-deploys to Fly.io on every green push (see "CI/CD gates"
below) - promoting to it always needs an explicit human instruction in the
conversation, never inferred from an earlier "ship this" or from Deploy's
own confidence. Every phase agent's own instructions repeat this; it is
the one rule this SDLC does not delegate.

Run this loop with the `ship-feature` skill (`.claude/skills/ship-feature/
SKILL.md`) - it's the orchestrator: it dispatches each `sdlc-*` agent in
`.claude/agents/`, shows the human the actual artifact at every handoff,
and stops until the human clears it to continue. The agents themselves
carry the phase-specific detail (what an intent.md/spec.md/plan.md needs
to contain, this repo's own conventions to follow, what each phase must
never do) - this file states the shape of the loop, not the mechanics of
running it.

Not every change needs the ceremony spelled out: a one-line typo fix can
move through the phases quickly (Plan and Design can each be a paragraph),
but it still goes through them, on the theory that the discipline of
writing "what problem, why, what design, what plan" costs little when the
answer is short and catches real mistakes when it isn't as short as it
looked. `docs/features/parent-week-edit/` is a worked example, written
retroactively for a feature shipped before this skill existed.

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
Azure IaC (`infrastructure/azure/`, root `*.bicep` files) — dormant and no
longer wired into CI, kept for reference/teardown only. Don't resurrect it
without checking with the repo owner first.

## Before committing

- Run `pytest tests/` and `flake8 app tests` locally — CI runs the same
  checks and will block on the hard-fail lint pass or test failures.
- Never commit `.env`, real secrets, or `.db` files — `.gitignore` should
  already cover these; double-check `git status` before staging.
- Use conventional commit style (`feat:`, `fix:`, `chore:`, `docs:`, etc.).
