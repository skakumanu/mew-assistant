# Plan: Align repo documentation with the current app

(spec: docs/features/align-docs-with-current-app/spec.md)

Documentation-only pass. No app/test/CI/config files touched. Order below
is the actual execution sequence.

## 1. Ground-truth confirmation (read-only, done before editing)

- [x] `app/main.py` — confirm mounted routers and the `/parent` + `/guardian`
      dual-prefix pattern (lines 89-132).
- [x] `app/routers/oauth_workos.py` (`/auth/workos` prefix, sign-in) vs.
      `app/routers/calendar_oauth.py` (`/calendar-sync/google` prefix,
      calendar connect) — confirm no `oauth.py`/`oauth_simple.py` exist.
- [x] `app/database/models.py` `UserRole` enum (SUPERUSER, ADMIN, PARENT,
      CAREGIVER, KID, THERAPIST, EDUCATOR) — used only as the RBAC banner's
      pointer, not restated in full.
- [x] `fly.toml` — app `mew-assistant`, region `iad`, `/health` check.
- [x] `CHANGELOG.md`'s `[1.1.0] - August 24, 2026` entry — source for the
      README feature table.
- [x] Grep root + `docs/` for cross-references to every file slated for
      deletion, to know what the four rewritten files must stop linking to,
      and confirm no surviving non-deleted doc (other than `CLAUDE.md`,
      handled as a documented exception below) is left with a dangling
      link.

## 2. Rewrite in place

1. `README.md` — replace Azure/Google-OAuth-only framing: WorkOS AuthKit
   sign-in, Fly.io deploy (`mew-assistant.fly.dev`), three-persona
   (parent/kid/provider) scheduling as the real feature set pulled from the
   `1.1.0` changelog entry, a features table reflecting shipped state, and a
   documentation section linking only to files surviving this pass
   (`CHANGELOG.md`, `docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
   `docs/KNOWN_ISSUES.md`, `CLAUDE.md`). Drop Azure badges/URLs and links to
   files being deleted.
2. `DOCUMENTATION_INDEX.md` — rebuild to list only post-pass files, correct
   one-line purposes, drop the dead `docs/SECURITY_PRIVACY_COMPLIANCE.md`
   link, drop the stale "Files Removed (December 3, 2025)" section, update
   the "Current Structure" tree.
3. `docs/README.md` — same treatment: point at `docs/OAUTH_SETUP.md`,
   `docs/THREE_PERSONA_SCHEDULING.md`, `docs/KNOWN_ISSUES.md`; drop Azure
   URLs, the dead compliance-doc link, and the stale
   `feature/customerzerosetup` branch reference.
4. `.github/copilot-instructions.md` — rewrite the Auth/OAuth bullet
   (`oauth_workos.py` sign-in vs. `calendar_oauth.py` calendar-connect,
   dropping the nonexistent `oauth.py`/`oauth_simple.py`), rewrite the
   Deployment bullet (Fly.io / `fly.toml` / `deploy_fly` CI job instead of
   Bicep/Azure Container Apps), and add a new bullet naming the
   three-persona model (`POST /requests` single write path, `RuleEngine`,
   parent/kid/provider routers) at the same depth as the existing
   auth/data-model bullets.

## 3. Delete — root

`USER_GUIDE.md`, `DEPLOYMENT_GUIDE.md`, `OAUTH_SETUP.md`,
`SIRI_SETUP_GUIDE.md`, `TOMORROW.md`, `NEXT_STEPS.md`, `SESSION_SUMMARY.md`,
`OAUTH_SUCCESS.md`, `PR19_MERGE_CHECKLIST.md`,
`COPILOT_REVIEW_RESPONSE.md`, `PRODUCTION_DEPLOYMENT_COMPLETE.md`,
`PRODUCTION_RECOVERY.md`, `SECURITY_INCIDENT.md`,
`SECURITY_AUDIT_SUMMARY.md`, `SECURITY_FIXES_DETAILED.md`,
`SECURITY_ISSUES_CODEQL.md`, `SECURITY_QUICK_FIX.md`,
`SECURITY_REPORTS_INDEX.md`, `SECURITY_SCAN_RESULTS.md`,
`CD_CREDENTIAL_MANAGEMENT_IMPLEMENTATION.md`, `.pr-body-44.md`,
`.pr-body-45.md`.

## 4. Delete — docs/

`docs/DEPLOYMENT_GUIDE.md`, `docs/DEPLOYMENT_OPERATIONS.md`,
`docs/OAUTH_STATUS.md`, `docs/GETTING_STARTED.md`, `docs/GUIDE.md`,
`docs/DEVELOPMENT.md`, `docs/PLANNING.md`, `docs/PROJECT_MANAGEMENT.md`,
`docs/NONPROFIT_TRANSITION.md`, `docs/USING_MEW.md`,
`docs/FEDERATED_AUTH_GUIDE.md`, `docs/MOBILE_REGISTRATION.md`,
`docs/PROJECT_HISTORY.md`, `docs/CHANGELOG_HISTORY.md`,
`docs/AZURE_KEYVAULT_CD_SETUP.md`, `docs/CONTINUOUS_DEPLOYMENT_CREDENTIALS.md`,
`docs/CD_CREDENTIAL_QUICK_REFERENCE.md`.

## 5. Legacy-label in place

Prepend the spec's verbatim banner (before the existing `# Title`) to:

- `docs/SIRI_SETUP.md` — topic "Siri integration", pointer
  `app/routers/voice_platforms.py`.
- `docs/SIRI_SETUP_GUIDE.md` — same topic/pointer.
- `docs/RBAC_SETUP_COMPLETE.md` — topic "role-based access control setup",
  pointer `app/database/models.py`'s `UserRole` enum.

No other content in these three files changes.

## 6. Dangling-link sweep

Grep the surviving doc set named in the spec's edge cases
(`README.md`, `DOCUMENTATION_INDEX.md`, `docs/README.md`,
`docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
`docs/KNOWN_ISSUES.md`, `docs/SECURITY.md`,
`docs/integrations/SETUP_GUIDE.md`, `.github/copilot-instructions.md`) for
the basename of every file deleted in steps 3-4. Fix or drop any hit.

`CLAUDE.md` is checked too, per the spec's edge-case list, but per the
spec's own acceptance criteria it must stay byte-for-byte unchanged and
rewriting it is an explicit non-goal — if it turns out to reference a
deleted filename, that gets reported back rather than edited (see note
below).

## 7. Verification

- `pytest tests/`
- `flake8 app tests`
- Confirm `docs/OAUTH_SETUP.md`, `docs/THREE_PERSONA_SCHEDULING.md`,
  `docs/KNOWN_ISSUES.md`, `docs/features/**`, `docs/SECURITY.md`,
  `docs/integrations/SETUP_GUIDE.md`, `CLAUDE.md` are untouched
  (`git diff` shows no changes to these paths).
- Confirm no file under `infrastructure/azure/`, no root `*.bicep` file,
  and no application/test/CI/config file was touched.
- Re-run the deleted-basename grep across root + `docs/` (excluding
  `docs/features/**`) as a final check.

## 8. Known spec discrepancies to flag in the Build report (not fixed here)

- `CLAUDE.md` line 89 names `docs/DEPLOYMENT_GUIDE.md` as an example of a
  dormant, no-longer-wired-into-CI doc. This pass deletes that file, so the
  reference becomes stale, but `CLAUDE.md` is explicitly required to stay
  byte-for-byte unchanged and out of scope to rewrite — left alone,
  reported instead of silently edited.
- The spec's edge cases assert "no file this spec deletes or moves is
  referenced anywhere in `.github/workflows/`, `.gitleaksignore`, or
  `.gitleaks.toml`." That's not accurate for `docs/GETTING_STARTED.md` and
  `docs/FEDERATED_AUTH_GUIDE.md`, both of which are deleted in step 4 and
  both of which are named in `.gitleaksignore` and `.gitleaks.toml`'s
  allowlist. In practice this doesn't break the `secret_scan` job (a
  gitleaks allowlist path/fingerprint that matches no existing file is
  inert, same as the pre-existing dead `DEPLOYMENT_SUMMARY.md` entry the
  spec already calls out and leaves alone) — but the claim itself is wrong,
  and per the acceptance criteria + out-of-scope section, `.gitleaksignore`
  and `.gitleaks.toml` are config, not touched by this pass. Reported, not
  fixed.
