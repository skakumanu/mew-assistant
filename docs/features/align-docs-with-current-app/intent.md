# Intent: Align repo documentation with the current app

## Problem

Most of this repo's documentation describes an app that no longer exists.
The current code (as of the `1.1.0` changelog, 2026-08-24) is a
three-persona scheduling app: WorkOS AuthKit handles parent sign-in
(`app/routers/oauth_workos.py`, `app/services/workos_client.py`,
`docs/OAUTH_SETUP.md` §1), it deploys to Fly.io (`fly.toml`,
`.github/workflows/ci-cd.yml`'s `deploy_fly` job), and its core surface is
the rule-engine-driven kid/parent/provider flow (`docs/features/`,
`docs/THREE_PERSONA_SCHEDULING.md`). But reading through the rest of the
docs tree turns up a much older app: a single-user Google-Calendar viewer,
signed in via a hand-rolled/Authlib OAuth flow, deployed on Azure
Container Apps.

Concretely, all still present and none flagged as outdated:

- Root `README.md` — status badges and every URL point at an
  `azurecontainerapps.io` host, describes "OAuth Sign-In - Google
  (Microsoft & Apple coming soon)" and "Azure Container Apps" as the
  infrastructure, and its own feature table has no mention of kids,
  providers, rules, or approvals.
- Root `DEPLOYMENT_GUIDE.md`, `OAUTH_SETUP.md`, `USER_GUIDE.md`,
  `SIRI_SETUP_GUIDE.md`, `DOCUMENTATION_INDEX.md`, `GUIDE.md` (dated
  December 2025) — same Azure/Google-only-OAuth story, and
  `DOCUMENTATION_INDEX.md` cross-links several of the stale root docs as
  the canonical entry points.
- A cluster of root files that read as one-off session/PR notes rather
  than reference docs — `TOMORROW.md`, `NEXT_STEPS.md`,
  `SESSION_SUMMARY.md`, `OAUTH_SUCCESS.md`, `PR19_MERGE_CHECKLIST.md`,
  `COPILOT_REVIEW_RESPONSE.md`, `PRODUCTION_DEPLOYMENT_COMPLETE.md`,
  `PRODUCTION_RECOVERY.md`, `SECURITY_INCIDENT.md` and several other
  `SECURITY_*.md` files, `.pr-body-44.md`, `.pr-body-45.md` — all dated
  November/December 2025, all describing the same defunct Azure/Google
  setup as current state.
- `docs/README.md` (the docs index) links to root files by paths that
  don't match where those files actually live, and describes the same
  stale architecture.
- Roughly 18 of the ~24 files directly under `docs/` (e.g.
  `GETTING_STARTED.md`, `DEVELOPMENT.md`, `PLANNING.md`,
  `PROJECT_MANAGEMENT.md`, `USING_MEW.md`, `GUIDE.md`, `OAUTH_STATUS.md`,
  `FEDERATED_AUTH_GUIDE.md`, `MOBILE_REGISTRATION.md`,
  `RBAC_SETUP_COMPLETE.md`, `NONPROFIT_TRANSITION.md`,
  `DEPLOYMENT_GUIDE.md`, `DEPLOYMENT_OPERATIONS.md`, the
  `AZURE_KEYVAULT_CD_SETUP.md`/`CONTINUOUS_DEPLOYMENT_CREDENTIALS.md`/
  `CD_CREDENTIAL_QUICK_REFERENCE.md` trio) reference the Azure
  Container Apps host, Google-only OAuth, or both. `docs/PROJECT_HISTORY.md`
  is itself a leftover dated session summary, not project history.
  By contrast, `docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
  and `docs/KNOWN_ISSUES.md` are accurate and current — this isn't
  uniform rot, it's a mix, which is part of why it's hard for a reader to
  tell which doc to trust.
- `.github/copilot-instructions.md` — the AI-agent guide for this repo —
  still describes `app/routers/oauth.py`/`oauth_simple.py` as the OAuth
  flows, Bicep/Azure Container Apps as the deployment path, and has no
  mention of WorkOS, kids, providers, rules, approvals, or Fly.io. Any
  agent (Claude, Copilot, or otherwise) that reads this file first for
  orientation gets actively misled about how auth and deploy work today.
- `scripts/DATABASE_CLEANUP_GUIDE.md` is a one-time remediation runbook
  tied to a specific past security incident, not living reference
  documentation, but nothing marks it as historical/completed.

This isn't a hypothetical — it's what a reader lands on today opening
`README.md`, `DOCUMENTATION_INDEX.md`, or `docs/README.md`, and every URL
in them 404s or points at infrastructure this repo no longer runs.

## Why now

The repo owner flagged this directly: the documentation should reflect
the code that's actually here. Beyond that, three concrete costs compound
the longer this sits:

- `.github/copilot-instructions.md` actively misdirects any AI coding
  agent working in this repo toward a defunct auth/deploy model, which
  works against the same AI-native SDLC this repo is now built around.
- New contributors (human or agent) landing on `README.md` or
  `DOCUMENTATION_INDEX.md` get routed to instructions for a product and
  infrastructure that no longer exist.
- The stale root docs conflict with `CLAUDE.md`'s own statement that
  legacy Azure material is "dormant... kept for reference/teardown only"
  — right now nothing in the docs themselves signals that; they present
  Azure Container Apps as the live, current deployment.

## Constraints

- Documentation only. No application code, tests, CI config, or
  infrastructure code changes — including `infrastructure/azure/` and the
  root `*.bicep` files. Per `CLAUDE.md`, that legacy Azure IaC is
  intentionally kept dormant for reference/teardown; this work does not
  touch it, only ensures docs don't describe it as the current, live
  deployment.
- `docs/features/**` (this SDLC's intent/spec/plan artifacts) is
  explicitly current and out of scope — don't touch it.
- Don't invent new documentation structure or a new docs site — work
  within the existing `docs/` tree and root-level convention already in
  use.

## Non-goals

- Fixing or refactoring anything in application code, even where reading
  it surfaced something questionable (e.g. `docs/KNOWN_ISSUES.md`'s
  already-tracked voice-pipeline bugs) — those stay exactly as tracked
  today, unrelated to this doc pass.
- Rewriting `CLAUDE.md` itself — it was checked and is accurate as of
  this review.
- Producing a brand-new user guide, architecture doc, or onboarding doc
  from scratch. This is about making existing docs stop contradicting the
  code, not adding net-new documentation coverage beyond that.
- Deciding the exact fate (delete vs. rewrite vs. move to an `archive/`
  location) of every individual stale file — that's a Design-phase call;
  this intent only establishes that the stale/misleading ones need to
  stop being presented as current.

## Success looks like

- `README.md`, `DOCUMENTATION_INDEX.md`, and `docs/README.md` describe
  the app that's actually in this repo today: WorkOS AuthKit sign-in,
  Fly.io deployment, and the three-persona (parent/kid/provider)
  scheduling model — with no live links to the retired
  `azurecontainerapps.io` host.
- `.github/copilot-instructions.md` matches the current routers, auth
  flow, and deployment target, so an agent using it as its first
  orientation point is not misled.
- Every doc that describes Azure Container Apps, Bicep, or single-provider
  Google-only OAuth as the *current* setup either is corrected or
  carries an unambiguous "legacy/historical" label — a reader can no
  longer land on any doc and reasonably conclude Azure Container Apps is
  where this app runs today.
- The one-off session-note files at repo root (`TOMORROW.md`,
  `NEXT_STEPS.md`, `SESSION_SUMMARY.md`, `OAUTH_SUCCESS.md`,
  `PR19_MERGE_CHECKLIST.md`, `COPILOT_REVIEW_RESPONSE.md`, PR-body
  scratch files, etc.) are no longer sitting at the root presented as
  reference documentation.
- Docs that are already accurate (`docs/OAUTH_SETUP.md`,
  `docs/THREE_PERSONA_SCHEDULING.md`, `docs/KNOWN_ISSUES.md`,
  `docs/features/**`) are left alone.
