# Spec: Align repo documentation with the current app

(intent: docs/features/align-docs-with-current-app/intent.md)

## Design

This is a documentation remediation pass with three kinds of outcome per
file, decided per-file/group below rather than deferred further:

1. **Rewrite in place** — files that are the canonical entry points a
   reader actually lands on first, so they must exist and must be
   accurate: root `README.md`, root `DOCUMENTATION_INDEX.md`,
   `docs/README.md`, `.github/copilot-instructions.md`.
2. **Delete** — files that are either (a) superseded by an already-
   accurate doc elsewhere in the tree (no value in keeping a second,
   wrong copy), or (b) pure one-off session/PR notes with no
   reference value going forward. Git history preserves them if anyone
   ever needs the old text; leaving them at the root mislabeled as
   current, or moving them to an `archive/` folder nobody will read
   either, doesn't serve a reader better than deleting outright.
3. **Label legacy in place** — files that describe a real, still-
   relevant *topic* (e.g. Siri/Shortcuts integration, RBAC roles, CD
   credential rotation) where the mechanism described is superseded but
   writing an accurate replacement is out of scope per the intent's
   non-goals ("not adding net-new documentation coverage"). These get a
   prominent banner at the top marking them historical/superseded and
   pointing at the current equivalent, rather than being deleted (losing
   institutionally useful "how we did X before" context) or silently
   rewritten (which would mean inventing new documentation this pass
   isn't scoped to produce).

**Alternative considered and rejected:** moving everything stale into a
single `docs/archive/` directory instead of deleting outright. Rejected
for the pure session-note cluster (`TOMORROW.md`, `SESSION_SUMMARY.md`,
`.pr-body-*.md`, etc.) because they were never reference material even
when fresh — archiving implies "kept for a reason," and git log already
is that archive. Used instead, narrowly, for docs that describe a
still-existing concern (Siri, RBAC, CD credentials) where "this used to
work differently" is genuinely useful institutional memory that a
future contributor might want without digging through git blame.

**Alternative considered and rejected:** leaving root `USER_GUIDE.md`,
`DEPLOYMENT_GUIDE.md`, `OAUTH_SETUP.md`, `SIRI_SETUP_GUIDE.md` in place
with corrected content. Rejected because each already has a more
accurate, more current equivalent doing that job today (`docs/
OAUTH_SETUP.md` for OAuth, `CLAUDE.md`'s Deployment section for
deploy) or would require writing new user-facing instructions from
scratch (a User Guide for the three-persona app doesn't exist yet and
authoring one is explicitly a non-goal). Keeping a second, stale copy
next to the real one is exactly the confusion the intent describes.

Ground truth used throughout, confirmed by reading the files, not
assuming from names:

- Auth: `app/routers/oauth_workos.py` (`/auth/workos/*`, WorkOS AuthKit
  via `app/services/workos_client.py`), sole sign-in path. Google Cloud
  OAuth (`app/routers/calendar_oauth.py`) is a second, unrelated flow
  used only for connecting a provider's Google Calendar, not sign-in —
  already documented correctly in `docs/OAUTH_SETUP.md`.
- Deploy: Fly.io (`fly.toml`, `.github/workflows/ci-cd.yml`'s
  `deploy_fly` job), health-checked at `/health`, app name
  `mew-assistant`, region `iad`.
- Core model: three-persona scheduling (`docs/THREE_PERSONA_SCHEDULING.md`,
  confirmed accurate against `app/routers/requests.py`, `rules.py`,
  `provider.py`), `POST /requests` as the sole write path, `/parent` and
  `/guardian` as interchangeable route prefixes for the same handlers
  (`app/main.py` lines 101-111), rule engine in
  `app/services/rule_engine.py`.
- Routers actually mounted today (`app/main.py`): landing, auth,
  oauth_workos, calendar_web, debug, session, message, summary,
  calendar, mobile, voice, kid, ai_scheduler, parent_approval (dual
  prefix), rules, change_requests (`requests.py`), parent_log (dual
  prefix), provider, calendar_sync, calendar_oauth,
  kid_calendar_oauth, smart_approval, notifications,
  onboarding_setup, mew_ui, voice_requests, webhooks. No `oauth.py` or
  `oauth_simple.py` router exists in the current tree at all —
  `.github/copilot-instructions.md`'s description of them is not just
  outdated, it names files that no longer exist.
- Version: `CHANGELOG.md`'s `[1.1.0] - August 24, 2026` entry is the
  current, accurate feature list (three-persona scheduling, calendar
  sync, voice request-only, provider org/person model) and is the
  source used for the rewritten README's feature table.
- `docs/README.md` and root `DOCUMENTATION_INDEX.md` both link to
  `docs/SECURITY_PRIVACY_COMPLIANCE.md`, which does not exist anywhere
  in the tree — a dead link in both, on top of the stale content, fixed
  by removing that entry rather than inventing the file.

## Affected files

### Rewrite in place (accurate, current content)

- `README.md` — replace Azure/Google-only-OAuth framing with: WorkOS
  AuthKit sign-in, Fly.io deployment (`mew-assistant.fly.dev`), the
  three-persona (parent/kid/provider) scheduling model as the actual
  feature set (pulled from the `1.1.0` changelog entry), a features
  table reflecting shipped vs. not, and a documentation section linking
  only to files that survive this pass: `CHANGELOG.md`,
  `docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
  `docs/KNOWN_ISSUES.md`, `CLAUDE.md` (deploy/CI). Drop the Azure status
  badges, the `azurecontainerapps.io` URLs, and links to files being
  deleted in this pass (`USER_GUIDE.md`, root `DEPLOYMENT_GUIDE.md`,
  root `OAUTH_SETUP.md`, `SIRI_SETUP_GUIDE.md`).
- `DOCUMENTATION_INDEX.md` — rebuild the index to list only files that
  exist after this pass, correct their one-line purpose, drop the
  broken `docs/SECURITY_PRIVACY_COMPLIANCE.md` link, drop the stale
  "Files Removed (December 3, 2025)" section (a historical index of a
  previous cleanup, itself now stale and not this pass's job to
  extend), and update the "Current Structure" tree to match reality.
- `docs/README.md` — same treatment: point at `docs/OAUTH_SETUP.md`,
  `docs/THREE_PERSONA_SCHEDULING.md`, `docs/KNOWN_ISSUES.md`, drop the
  Azure production URLs and the dead `SECURITY_PRIVACY_COMPLIANCE.md`
  link, drop the stale `feature/customerzerosetup` branch reference.
- `.github/copilot-instructions.md` — rewrite the Auth/OAuth bullet to
  describe `app/routers/oauth_workos.py` (WorkOS AuthKit, sign-in) vs.
  `app/routers/calendar_oauth.py` (Google Calendar connect, unrelated
  concern) instead of the nonexistent `oauth.py`/`oauth_simple.py`.
  Rewrite the Deployment bullet to describe Fly.io (`fly.toml`,
  `deploy_fly` CI job) instead of Bicep/Azure Container Apps. Add a
  bullet naming the three-persona model (`POST /requests` single write
  path, `RuleEngine`, parent/kid/provider routers) since that's now the
  core surface an agent orienting itself needs to know about first,
  matching the depth already given to auth/data model.

### Delete (superseded duplicate or pure session-note; no reference value)

Root:
- `USER_GUIDE.md` — describes single-user Google Calendar viewer with
  30-day JWT sessions; the three-persona app has no equivalent doc and
  writing one is out of scope (non-goal). Its one live link
  (README → USER_GUIDE) is removed as part of the README rewrite.
- `DEPLOYMENT_GUIDE.md` — Azure Container Apps deployment walkthrough;
  superseded by `CLAUDE.md`'s Deployment section plus `fly.toml`.
- `OAUTH_SETUP.md` — describes Authlib/hand-rolled Google+Microsoft+Apple
  OAuth; superseded by the accurate `docs/OAUTH_SETUP.md`. Keeping both
  is exactly the "which do I trust" problem the intent calls out.
- `SIRI_SETUP_GUIDE.md` — walks through a now-defunct
  "sign in via Safari, copy a token into Shortcuts" flow against the
  old single-user app; see docs/ Siri cluster below for why this is
  deleted rather than legacy-labeled (unlike its docs/ siblings, it has
  no companion accurate doc and duplicates two files under docs/).
- `TOMORROW.md`, `NEXT_STEPS.md`, `SESSION_SUMMARY.md`,
  `OAUTH_SUCCESS.md`, `PR19_MERGE_CHECKLIST.md`,
  `COPILOT_REVIEW_RESPONSE.md`, `PRODUCTION_DEPLOYMENT_COMPLETE.md`,
  `PRODUCTION_RECOVERY.md`, `SECURITY_INCIDENT.md`,
  `SECURITY_AUDIT_SUMMARY.md`, `SECURITY_FIXES_DETAILED.md`,
  `SECURITY_ISSUES_CODEQL.md`, `SECURITY_QUICK_FIX.md`,
  `SECURITY_REPORTS_INDEX.md`, `SECURITY_SCAN_RESULTS.md`,
  `CD_CREDENTIAL_MANAGEMENT_IMPLEMENTATION.md`, `.pr-body-44.md`,
  `.pr-body-45.md` — one-off session/PR/incident notes from
  November/December 2025, none referenced from CI config, `.gitleaksignore`,
  `.gitleaks.toml`, or any workflow (checked directly — no hits), so
  deleting them breaks no tooling.

`docs/`:
- `docs/DEPLOYMENT_GUIDE.md`, `docs/DEPLOYMENT_OPERATIONS.md` — Azure
  Container Apps operational runbooks; no Fly.io equivalent needed
  beyond what `CLAUDE.md` already states, and authoring a full Fly.io
  ops runbook is net-new documentation (non-goal).
- `docs/OAUTH_STATUS.md` — a dated (2025-11-25) status snapshot of the
  old `/auth/simple/*` Google-only flow deployed to
  `*.azurecontainerapps.io`; fully superseded by `docs/OAUTH_SETUP.md`.
- `docs/GETTING_STARTED.md`, `docs/GUIDE.md`, `docs/DEVELOPMENT.md`,
  `docs/PLANNING.md`, `docs/PROJECT_MANAGEMENT.md`,
  `docs/NONPROFIT_TRANSITION.md`, `docs/USING_MEW.md`,
  `docs/FEDERATED_AUTH_GUIDE.md`, `docs/MOBILE_REGISTRATION.md` — each
  confirmed (grepped) to describe Azure/Container Apps and/or the old
  Google-only OAuth as current state; large, narrative documents whose
  useful current-state content (setup, testing, contribution flow) is
  already covered by `CLAUDE.md` + root `README.md` post-rewrite +
  `docs/OAUTH_SETUP.md`. Rewriting nine multi-hundred-to-thousand-line
  docs in place would mean authoring new reference documentation at a
  scale well past "stop contradicting the code" — deletion is the
  decisive call the intent asks Design to make here.
- `docs/PROJECT_HISTORY.md`, `docs/CHANGELOG_HISTORY.md` — the intent
  names `PROJECT_HISTORY.md` directly as "itself a leftover dated
  session summary, not project history." `CHANGELOG_HISTORY.md` is the
  same shape (a superset dump duplicating root `CHANGELOG.md` plus old
  session summaries) — same disposition, same reasoning.
- `docs/AZURE_KEYVAULT_CD_SETUP.md`, `docs/CONTINUOUS_DEPLOYMENT_CREDENTIALS.md`,
  `docs/CD_CREDENTIAL_QUICK_REFERENCE.md` — all describe Azure Key
  Vault-based CD credential rotation for a deploy target
  (`deploy_fly` replaced this; there's no equivalent Fly.io credential
  doc needed beyond `CLAUDE.md`'s existing "`FLY_API_TOKEN` repository
  secret" line). Deleted rather than legacy-labeled because CD
  credential handling is operationally *replaced*, not historically
  interesting — an agent or contributor doing CD work today gets
  nothing from an Azure Key Vault rotation runbook, unlike the Siri
  cluster below where the underlying user-facing feature still exists.

### Legacy-label in place (topic still relevant; mechanism superseded, no accurate replacement authored this pass)

- `docs/SIRI_SETUP.md`, `docs/SIRI_SETUP_GUIDE.md` — Siri/Shortcuts
  integration is a real, still-mounted feature
  (`app/routers/voice_platforms.py`'s `/api/v1/voice/siri/webhook`,
  `docs/shortcuts/MewAssistant.shortcut`), but both docs describe the
  old single-user Google-token-in-Shortcuts mechanism against an
  `azurewebsites.net`/`azurecontainerapps.io` host — materially
  different from the current webhook-based integration. Add an
  identical banner to both, top of file, rather than deleting (the
  feature is real and a future doc pass will need *something* to
  revise) or rewriting (an accurate current Siri setup guide is new
  documentation coverage, out of scope per the intent's non-goals).
  Banner text (see Data/API/UI changes section for exact wording).
- `docs/RBAC_SETUP_COMPLETE.md` — describes SUPERUSER/ADMIN/PARENT/
  CAREGIVER roles; `app/database/models.py`'s `UserRole` enum needs to
  be checked against this list before deciding wording, but regardless
  of exact enum drift this file's own title ("Implementation - Complete
  ✅") presents a point-in-time completion note as living reference.
  Same banner treatment: mark it as a historical implementation record,
  point readers to `app/database/models.py` (`UserRole`) as the source
  of truth for current roles rather than re-deriving the list by hand.

### Left alone (already accurate, or accurate-and-out-of-scope)

- `docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
  `docs/KNOWN_ISSUES.md`, `docs/features/**` — per intent, confirmed
  accurate by direct reading.
- `docs/SECURITY.md` (bot-protection reference, matches
  `app/middleware/bot_protection.py`, no Azure/OAuth content),
  `docs/integrations/SETUP_GUIDE.md` (Email/SMS/WhatsApp/AI/Calendar
  integration setup, zero Azure references, matches current
  integration code), `docs/shortcuts/MewAssistant.shortcut` (binary
  shortcut asset, not a doc) — none contradict current auth, deploy, or
  persona model; not named in the intent; out of scope to touch.
- `CHANGELOG.md`, `openapi.json`, `CLAUDE.md` — accurate and/or
  explicitly a non-goal to edit.
- `.github/CI_CD_DOCUMENTATION.md`, `.github/QUICK_START_CI_CD.md` —
  read and confirmed to describe the current `ci-cd.yml` pipeline
  (test/lint/osv/security/secret-scan, Fly deploy), not Azure; not
  named in the intent, left alone.
- `infrastructure/azure/`, root `*.bicep` files, `deploy-azure.sh`,
  and other Azure-era shell/PowerShell/SQL scripts at root
  (`deploy-oauth.sh`, `deploy-simple.ps1`, `finish-deployment.sh`,
  `init-azure-db.py`, `get_keyvault_secrets.py`, `add_oauth_tokens.sql`,
  `fix_oauth_schema.sql`, `fix_federated_id.sql`, etc.) — explicitly
  out of scope per the intent's constraints (infrastructure code, not
  docs). Not touched.

## Data / API / UI changes

No schema, endpoint, or UI changes — this is a documentation-only pass.
No database migration is needed (nothing in `app/database/models.py`
changes). No locale-file changes are needed: nothing here adds a
user-facing string inside the running application (README/docs are not
rendered through `app/locales/*.json` / `t()`), so `tests/
test_locales.py` is unaffected.

**Legacy banner text** (used verbatim, adjusted only for the specific
file being labeled), placed as the first lines of each legacy-labeled
file, above its existing `# Title`:

```markdown
> **Historical / superseded.** This document describes an earlier
> version of Mew Assistant's <TOPIC> that no longer matches the current
> app. Kept for historical reference only — see <POINTER> for the
> current setup. Do not follow these steps for the app as it exists
> today.
```

- `docs/SIRI_SETUP.md` / `docs/SIRI_SETUP_GUIDE.md`: `<TOPIC>` = "Siri
  integration", `<POINTER>` = "`app/routers/voice_platforms.py` for the
  current webhook-based integration."
- `docs/RBAC_SETUP_COMPLETE.md`: `<TOPIC>` = "role-based access
  control setup", `<POINTER>` = "`app/database/models.py`'s `UserRole`
  enum for the roles that exist today."

## Edge cases

- **Broken cross-links after deletion**: deleting root `USER_GUIDE.md`,
  `DEPLOYMENT_GUIDE.md`, `OAUTH_SETUP.md`, `SIRI_SETUP_GUIDE.md` and the
  ~15 `docs/*.md` files above means every remaining doc's links to them
  must be updated in the same change. Concretely: `README.md` and
  `DOCUMENTATION_INDEX.md` are being rewritten anyway (covers their
  links); `docs/README.md` is being rewritten (covers its links).
  Before finishing, Build should grep the surviving doc set
  (`README.md`, `DOCUMENTATION_INDEX.md`, `docs/README.md`,
  `docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
  `docs/KNOWN_ISSUES.md`, `docs/SECURITY.md`,
  `docs/integrations/SETUP_GUIDE.md`, `CLAUDE.md`,
  `.github/copilot-instructions.md`) for any remaining reference to a
  deleted filename and fix or drop it — this is listed explicitly as an
  acceptance criterion below rather than left implicit.
- **`docs/SECURITY_PRIVACY_COMPLIANCE.md` never existed**: both indexes
  link to it today. Don't recreate it (net-new doc, out of scope) —
  just drop the dead link when rewriting both indexes.
- **CHANGELOG.md's own historical entries mention Azure**: `CHANGELOG.md`
  is a chronological record, not a statement of current state, and the
  intent leaves it untouched — old entries correctly describing what
  was true *at that time* are not "documentation describing the current
  app" and are not touched by this design.
- **`.gitleaksignore` references `DEPLOYMENT_SUMMARY.md`** (a file that
  doesn't exist in the tree at all, pre-existing and unrelated to any
  file this spec deletes) — confirmed via grep that no file this spec
  deletes or moves is referenced anywhere in `.github/workflows/`,
  `.gitleaksignore`, or `.gitleaks.toml`, so no CI/tooling config needs
  changing. The pre-existing dead `.gitleaksignore` entry is unrelated
  pre-existing drift, not caused by or in scope for this change, and is
  left alone.
- **Legacy banners must not get lost in a future edit**: the banner is
  placed as the literal first lines of the file (before the `#` title)
  specifically so it survives a casual reader skimming past a title,
  and so a future `grep -l "Historical / superseded"` can audit all
  legacy-labeled docs at once.
- **Root vs. docs duplication surviving the pass**: after deletion,
  `docs/OAUTH_SETUP.md` is the sole OAuth doc (root copy deleted) and
  `CLAUDE.md` is the sole deployment doc (both root and `docs/`
  deployment guides deleted) — no remaining doc pair describes the same
  topic differently, which was the root cause of "which do I trust."

## Acceptance criteria

- `README.md`, `DOCUMENTATION_INDEX.md`, and `docs/README.md` contain no
  occurrence of `azurecontainerapps.io`, `azurewebsites.net`, "Azure
  Container Apps", or "Bicep", and each states WorkOS AuthKit for
  sign-in and Fly.io for deployment.
- `.github/copilot-instructions.md` contains no reference to
  `app/routers/oauth.py` or `app/routers/oauth_simple.py` (neither file
  exists in `app/routers/`), references `oauth_workos.py` and
  `calendar_oauth.py` by name, and references Fly.io/`fly.toml` instead
  of Bicep/Azure Container Apps for deployment.
- None of the following paths exist after this change: `USER_GUIDE.md`,
  `DEPLOYMENT_GUIDE.md`, `OAUTH_SETUP.md`, `SIRI_SETUP_GUIDE.md`,
  `TOMORROW.md`, `NEXT_STEPS.md`, `SESSION_SUMMARY.md`,
  `OAUTH_SUCCESS.md`, `PR19_MERGE_CHECKLIST.md`,
  `COPILOT_REVIEW_RESPONSE.md`, `PRODUCTION_DEPLOYMENT_COMPLETE.md`,
  `PRODUCTION_RECOVERY.md`, `SECURITY_INCIDENT.md`,
  `SECURITY_AUDIT_SUMMARY.md`, `SECURITY_FIXES_DETAILED.md`,
  `SECURITY_ISSUES_CODEQL.md`, `SECURITY_QUICK_FIX.md`,
  `SECURITY_REPORTS_INDEX.md`, `SECURITY_SCAN_RESULTS.md`,
  `CD_CREDENTIAL_MANAGEMENT_IMPLEMENTATION.md`, `.pr-body-44.md`,
  `.pr-body-45.md`, `docs/DEPLOYMENT_GUIDE.md`,
  `docs/DEPLOYMENT_OPERATIONS.md`, `docs/OAUTH_STATUS.md`,
  `docs/GETTING_STARTED.md`, `docs/GUIDE.md`, `docs/DEVELOPMENT.md`,
  `docs/PLANNING.md`, `docs/PROJECT_MANAGEMENT.md`,
  `docs/NONPROFIT_TRANSITION.md`, `docs/USING_MEW.md`,
  `docs/FEDERATED_AUTH_GUIDE.md`, `docs/MOBILE_REGISTRATION.md`,
  `docs/PROJECT_HISTORY.md`, `docs/CHANGELOG_HISTORY.md`,
  `docs/AZURE_KEYVAULT_CD_SETUP.md`,
  `docs/CONTINUOUS_DEPLOYMENT_CREDENTIALS.md`,
  `docs/CD_CREDENTIAL_QUICK_REFERENCE.md`.
- `docs/SIRI_SETUP.md`, `docs/SIRI_SETUP_GUIDE.md`, and
  `docs/RBAC_SETUP_COMPLETE.md` each still exist and each begins with
  the "Historical / superseded" banner before their original title.
- `docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
  `docs/KNOWN_ISSUES.md`, `docs/features/**`, `docs/SECURITY.md`,
  `docs/integrations/SETUP_GUIDE.md`, and `CLAUDE.md` are byte-for-byte
  unchanged from before this pass.
- No file under `infrastructure/azure/`, no root `*.bicep` file, and no
  application/test/CI/config file is modified, added, or removed.
- Grepping every surviving Markdown file at repo root and under `docs/`
  (excluding `docs/features/**`) for the basenames of every deleted
  file in the list above returns no matches (no dangling links to
  deleted docs).
- `pytest tests/` and `flake8 app tests` both still pass unchanged
  (this pass touches no code, so this is a no-op check, but confirms
  nothing was accidentally modified outside docs).

## Out of scope

- Everything in the intent's own Non-goals section: no application code
  changes, no rewriting `CLAUDE.md`, no new user guide/architecture
  doc/onboarding doc from scratch, no fixing the already-tracked
  voice-pipeline bugs in `docs/KNOWN_ISSUES.md`.
- Writing an accurate, current Siri/Shortcuts setup guide or an updated
  RBAC role reference — deferred by design (legacy-labeled, not
  rewritten) because authoring either is net-new documentation coverage
  beyond "stop contradicting the code."
- Reconciling `docs/RBAC_SETUP_COMPLETE.md`'s specific role list against
  the live `UserRole` enum field-by-field — the legacy banner points at
  the enum as source of truth instead of hand-verifying and restating
  the list, which would itself be new documentation authorship.
- Fixing the pre-existing dead `.gitleaksignore` entry for the
  nonexistent `DEPLOYMENT_SUMMARY.md` — unrelated to any file this pass
  touches, and `.gitleaksignore` is config, not documentation.
- Any change to `infrastructure/azure/`, root `*.bicep` files, or the
  Azure-era shell/PowerShell/SQL scripts at root — explicitly fenced
  off by the intent's constraints, kept dormant per `CLAUDE.md`.
- Deciding whether `docs/SIRI_SETUP.md` and `docs/SIRI_SETUP_GUIDE.md`
  should eventually be merged into one file — both get the same banner
  in this pass; consolidating them is a separate, later editorial call
  not required to meet this intent's success criteria.
