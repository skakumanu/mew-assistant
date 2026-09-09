# Plan: adopt five engineering-discipline practices

(spec: docs/features/adopt-engineering-discipline-practices/spec.md)

Ordered task breakdown for Build, derived from spec.md's "Affected files"
and "Data / API / UI changes" sections. Each numbered group corresponds to
one of the five items; within a group, code before tests before docs.

## 1. Semantic version bumping

1. `app/utils/config.py` — bump `Settings.APP_VERSION` default from
   `"1.0.0"` to `"1.1.0"`, matching `CHANGELOG.md`'s actual top released
   entry and closing the pre-existing three-way drift (this is not a new
   user-visible change needing its own bump; it is fixing the drift item 1
   exists to fix).
2. `app/main.py` — `FastAPI(version=settings.APP_VERSION)` instead of the
   `"1.1.0"` literal; `GET /version` returns
   `{"version": settings.APP_VERSION, "deployed": os.environ.get("BUILD_TIME")}`
   instead of the hardcoded `landing-page-v2` stub (`BUILD_TIME` is an
   optional env var nothing sets today — Fly could inject one later; absent,
   it's `null`, which is honest given no reliable source exists yet).
3. New `tests/test_version.py`: (a) `GET /version` body's `version` equals
   `settings.APP_VERSION`; (b) a `CHANGELOG.md` parser (skip
   `## [Unreleased]`, find the first `## [X.Y.Z]` heading) equals
   `settings.APP_VERSION`.
4. `CLAUDE.md` "Before committing" — add the version-bump-and-tag line.
5. Verify acceptance criterion 1's negative case by hand: temporarily bump
   only one of `APP_VERSION`/`CHANGELOG.md` in a scratch (uncommitted) edit,
   confirm `tests/test_version.py` fails, then revert before moving on.

## 2. Secret-scan gap

1. `.gitleaks.toml` — add two `[[rules]]`: `connection-string-credential`
   (schemes: postgres/postgresql, mysql, mongodb/mongodb+srv, redis,
   amqp/amqps) and `google-oauth-client-secret` (`GOCSPX-` prefix), each
   with a comment recording the investigation in spec.md section 2.
2. Grep the repo for existing `scheme://user:pass@host`-shaped strings
   that would now match, against `.gitleaks.toml`'s current allowlist
   paths and `tests/` fixtures (spec's named Edge Case). Extend the
   `[allowlist].regexes` list for any real false positive found before
   landing (expected: `app/database/connection.py`'s default,
   `docker-compose.yml`, `.github/workflows/performance-test.yml`, all of
   which hard-code the same non-secret dev placeholder credentials).
3. New `tests/test_gitleaks_rules.py` — load `.gitleaks.toml` with
   `tomllib`, extract each new rule's `regex`, assert each matches an
   incident-shaped synthetic fixture and does not match the allowlist
   placeholders or a bare credential-free URL.
4. Verify acceptance criterion 2 by running the new test file and
   confirming both directions (match / no-match) actually exercise the
   real regex, not a stand-in.

## 3. Data-accuracy gate for the rule engine / change-request decisions

1. Measure today's real coverage for the two files with the exact command
   spec.md gives, overriding `pytest.ini`'s blanket `--cov=app` addopt (which
   otherwise silently widens any `--cov=<module>` back to whole-repo) via
   `--override-ini=addopts=`. Record the number; pick `<N>` with a small,
   real margin below it (see report for the measured figure and the exact
   value chosen).
2. `.github/workflows/ci-cd.yml` — add a step to the existing `test` job,
   after the main `pytest tests/` run: the file-scoped coverage-floor
   command from spec.md (with the same `--override-ini=addopts=` needed to
   make the restriction real rather than a no-op alongside `pytest.ini`).
3. New `tests/test_change_request_decisions.py` — a "golden outcomes" test
   class calling `ChangeRequestService.submit()` directly (bypassing the
   HTTP client), reusing `family`/`rules`/`session_row`/`db_session` from
   `tests/conftest.py`. One case per `ReasonCode` (8) plus the auto-applied
   cancellation branch plus a compliant-move baseline, each asserting
   `ChangeOutcome.auto_applied`, the resulting `ApprovalRequest.status`, and
   `applied_to_calendar`. Module docstring states the golden-outcomes
   warning verbatim from spec.md.
4. Verify acceptance criterion 3 by temporarily commenting out one test
   covering a distinct branch, confirming only the new coverage-floor step
   (not the main `--cov=app` step) would catch the drop, then revert.
5. Verify acceptance criterion 4 by temporarily inverting one branch's
   expected `auto_applied`/status in `change_request_service.py`, confirming
   the new golden-outcomes class (not `test_rule_engine.py`) fails, then
   revert.

## 4. Parent-readable changelog surface

1. New `docs/WHATS_NEW.md` — one plain-language entry for `1.1.0`
   (backfilled) and one for this cycle's own process changes (framed for a
   parent: nothing here is user-visible, so this entry says so plainly
   rather than inventing a feature). No file paths, endpoint names, or
   internal class/service names anywhere in the file.
2. `docs/README.md` and `DOCUMENTATION_INDEX.md` — list `docs/WHATS_NEW.md`
   alongside the other docs, matching the existing table/list pattern.
3. `CLAUDE.md` "Before committing" — add the `docs/WHATS_NEW.md`
   companion-update line, adjacent to the version-bump line since both fire
   on the same "is this user-visible" trigger.

## 5. Architecture doc + trigger-list

1. New `docs/ARCHITECTURE.md` — the seven sections from spec.md's table of
   contents (Overview, Request lifecycle, Router layer map, Data model,
   Services layer, Deployment topology, Trigger-list), cross-referencing
   `docs/THREE_PERSONA_SCHEDULING.md` rather than duplicating it, and
   explicitly flagging `Family`/`ApprovalRule`/`ScheduleEntry`/`UserProfile`
   as pre-three-persona and `infrastructure/azure/`/root `*.bicep` as
   dormant legacy.
2. Trigger-list placement: its own closing section in `docs/ARCHITECTURE.md`
   itself (keeps the list next to the doc it governs; `CLAUDE.md` gets a
   one-line pointer to it rather than a second copy that could drift from
   the first).
3. `docs/README.md` and `DOCUMENTATION_INDEX.md` — list
   `docs/ARCHITECTURE.md`.
4. `CLAUDE.md` — new "Documentation" section (placed after "Deployment",
   before "Before committing", since it's reference material like the
   sections around it) with the one-line pointer to
   `docs/ARCHITECTURE.md`'s trigger-list.

## Cross-cutting

1. `CHANGELOG.md` — one `[Unreleased]` entry pointing at this cycle's own
   checklist additions (process/tooling, not a product feature).
2. Run `pytest tests/` and `flake8 app tests`; fix anything red.
3. Commit with conventional-commit types per file group (`feat:` for the
   version/gitleaks/coverage-gate/golden-outcomes mechanisms, `docs:` for
   the two new docs and README/index updates, `chore:` for the CI workflow
   step and CLAUDE.md checklist wording) — likely 2-4 commits rather than
   one, to keep each commit's diff legible against what it's doing.
4. Push to `feature/adopt-engineering-discipline-practices` (already
   exists; no new branch, no PR — that is Deploy's job).
