# Plan: close the release-record gap for kid calendar push

(spec: docs/features/kid-calendar-push/spec.md)

Version bump + two documentation edits only. No application code,
migration, or test changes.

## Tasks

1. `app/utils/config.py`: bump `Settings.APP_VERSION` from `"1.1.0"` to
   `"1.2.0"`. One-line literal change; comment above it stays as-is.

2. `CHANGELOG.md`: before editing, re-read the current `## [Unreleased]`
   section live and diff its body against `git show HEAD:CHANGELOG.md` to
   confirm this plan's understanding of it is still accurate (it is a
   move, not a rewrite — the existing `### 🔧 Process / tooling` body must
   survive byte-for-byte). Then:
   - Rename `## [Unreleased]` to `## [1.2.0] - September 9, 2026`.
   - Insert a new `### 🔌 Integrations` subsection for kid calendar push
     above the existing `### 🔧 Process / tooling` subsection, using the
     exact content from spec.md.
   - Leave the existing `### 🔧 Process / tooling` subsection's text
     untouched.
   - Add a fresh, empty `## [Unreleased]` heading at the very top of the
     changelog body (above the new `## [1.2.0]` heading).
   - Leave everything from `## [1.1.0] - August 24, 2026` downward
     unchanged.

3. `docs/WHATS_NEW.md`: replace the `## September 2026` heading and its
   "Nothing new for you to see this time" body with `## September 9,
   2026` and the parent-facing paragraph from spec.md. Do not leave a
   second, contradicting September entry.

4. Self-verify against spec.md's acceptance criteria:
   - `Settings.APP_VERSION == "1.2.0"`.
   - `CHANGELOG.md`'s first versioned heading (skipping `[Unreleased]`) is
     `## [1.2.0] - September 9, 2026`; an empty `## [Unreleased]` heading
     sits above it; the new `### 🔌 Integrations` subsection names
     `KidCalendarConnection`, `push_to_kid_calendar`,
     `kid_calendar_oauth.py`, and `tests/test_kid_calendar_connections.py`;
     the `### 🔧 Process / tooling` subsection is byte-identical to its
     pre-change form.
   - `tests/test_version.py` passes unmodified.
   - `GET /version` reports `"1.2.0"` (via the existing test/route).
   - `docs/WHATS_NEW.md` has `## September 9, 2026`, no bare `## September
     2026` remains, and the new entry has no file path/endpoint/internal
     identifier.
   - `docs/features/kid-calendar-push/` contains `intent.md`, `spec.md`,
     `plan.md`.
   - `git diff origin/develop...HEAD --stat` touches only
     `app/utils/config.py`, `CHANGELOG.md`, `docs/WHATS_NEW.md`, and files
     under `docs/features/kid-calendar-push/`.
   - `pytest tests/` and `flake8 app tests` both pass.

5. Run `pytest tests/` and `flake8 app tests`; fix anything they catch.

6. Commit (conventional commit style, e.g. `docs:`/`chore:`) and push to
   `feature/kid-calendar-push-release-notes`.

## Out of scope

Any kid-calendar-push application code, model, router, UI, locale file,
or test (already shipped); the `v1.2.0` git tag; `docs/ARCHITECTURE.md`.
