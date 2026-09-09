# Spec: close the release-record gap for kid calendar push

(intent: docs/features/kid-calendar-push/intent.md)

## Design

The mechanism is a version bump plus two documentation edits, verified
against the real code rather than the intent's own summary of it. No
application code, migration, or test changes — the intent's constraint
that the push mechanism itself is untouched is a hard boundary, not a
default.

### 1. Version number: `1.1.0` → `1.2.0`

`app/utils/config.py`'s `Settings.APP_VERSION` is `"1.1.0"` today, and
`CHANGELOG.md`'s top *versioned* heading agrees (`## [1.1.0] - August 24,
2026`), with only a non-user-facing `## [Unreleased]` entry
(`adopt-engineering-discipline-practices`, PR #175, already merged to
`develop`, explicitly self-documented as "No user-facing change") sitting
above it. `tests/test_version.py` (confirmed present on `develop` at
`a4eebc6`, from the `adopt-engineering-discipline-practices` cycle that
merged immediately before this one) already locks `APP_VERSION` against
that top heading and already correctly skips `[Unreleased]` — it applies
here unmodified.

Kid calendar push is a genuinely new, additive, backward-compatible
capability (a new push target, a new OAuth connect flow, a new UI card) —
minor per semver, not a patch (it's not a bug fix) and not major (nothing
existing changes shape or breaks). **Bump to `1.2.0`.**

**This repo's own convention for what happens to `[Unreleased]` at a
release cut, read directly from `e4d529b`'s commit message** ("Moves the
changelog's `[Unreleased]` section to `[1.1.0]`... fills in the two
entries it was missing... bumps the FastAPI app version to match"): the
version heading replaces `[Unreleased]`, a fresh empty `[Unreleased]`
heading is left above it for whatever comes next, and *everything already
sitting under `[Unreleased]`* becomes part of the cut release — it is not
held back for a later one. The `adopt-engineering-discipline-practices`
entry currently under `[Unreleased]` is exactly this: real, merged,
substantive work with its own already-existing `docs/features/` write-up,
just never version-numbered because nothing has cut a release since it
landed. Splitting it into its own separate version bump instead would
invent a second release for content this repo's own history shows is
supposed to ride along with the next cut. So `1.2.0` carries **both**
the existing `[Unreleased]` content (unchanged, moved as-is) **and** a new
entry for kid calendar push.

**Alternative considered:** cut `1.2.0` for kid-calendar-push alone and
leave the `adopt-engineering-discipline-practices` entry sitting under a
persisting `[Unreleased]` for a future release. Rejected — it contradicts
this repo's own demonstrated precedent (`e4d529b`) for what `[Unreleased]`
means at cut time, and there's no reason given anywhere to hold that
entry back; nothing about it is unfinished or blocked.

**Alternative considered:** derive `APP_VERSION` from git describe/tags at
runtime instead of a manual literal. Out of scope here — this exact
question was already raised and rejected in
`docs/features/adopt-engineering-discipline-practices/spec.md` §1 in favor
of the manual-bump-plus-lock-test this repo already has; re-litigating it
is not this cycle's job.

### 2. `CHANGELOG.md` entry — exact content

Rename the current `## [Unreleased]` heading to a dated version heading,
leave its existing body untouched, add a new subsection above it for kid
calendar push, and open a fresh empty `## [Unreleased]` heading at the
top of the file. Concretely, the region from the current `## [Unreleased]`
heading down to (not including) `## [1.1.0] - August 24, 2026` becomes:

```markdown
## [Unreleased]

## [1.2.0] - September 9, 2026

### 🔌 Integrations
- **Push a kid's own schedule into their own Google Calendar**
  ([docs/features/kid-calendar-push/](docs/features/kid-calendar-push/)):
  a one-way, parent-authorised mirror of a kid's `ScheduledSession`s into
  their own personal Google Calendar — distinct from, and independent of,
  the existing provider-calendar pull/write-back
  - `KidCalendarConnection` (`app/database/models.py`) is the parent's
    push target for a kid: one row per `child_id`, enforced by a unique
    constraint on `child_id` alone, so a co-parent reconnecting it updates
    the same row rather than creating a sibling one
  - `CalendarSyncService.push_to_kid_calendar()`
    (`app/services/calendar_sync_service.py`) creates, updates or cancels
    the mirrored event, deciding which purely from whether
    `ScheduledSession.kid_calendar_event_id` is already set; every event
    it writes is tagged (`MIRROR_PROPERTY_KEY`,
    `app/integrations/calendar_sync/google.py`) so a later pull can never
    re-ingest its own mirror as a new session
  - Wired into both places a push-only feature needs, each independently
    best-effort so one failing write never blocks the other:
    `ChangeRequestService`'s write-back on a parent approval or a
    rule-engine auto-clear, and `CalendarSyncService.pull_org` for a
    session a provider reschedules on their own calendar
  - `app/routers/kid_calendar_oauth.py`: the parent-facing OAuth
    connect/callback/calendar-picker flow — ownership-checked so a parent
    can only connect a kid that is actually theirs, and the calendar
    picker filters to writer/owner calendars only (a push target, unlike
    the provider picker's read-only need) and flags a calendar already in
    use elsewhere in the family
  - `calendar_oauth.py`'s `CALENDAR_SCOPE` is the full
    `.../auth/calendar` scope (not `calendar.readonly`), specifically to
    support the writes this flow needs — incidentally correct for the
    provider write-back path too
  - Providers tab (`app/static/mew/mew.js`'s
    `renderKidCalendars`/`kidCalendarCard`) gained a per-kid calendar
    card: connect button, calendar picker, and a shared-calendar conflict
    warning; copy localised in all four supported locales
  - `tests/test_kid_calendar_connections.py`: the connect flow,
    cross-family ownership isolation, the calendar picker, push
    create/update/cancel, and two regression cases for real incidents (a
    shared push/pull calendar causing a duplicate-event loop; a
    pre-existing collision wrongly re-flagged on a plain reconnect)
  - Already built, merged and live in production ahead of this entry;
    this closes a release-record gap rather than describing new work —
    see the linked feature folder for the full account

### 🔧 Process / tooling
- Adopted five engineering-discipline practices, closing gaps surfaced by
  this cycle's own investigation rather than by rote
  ([docs/features/adopt-engineering-discipline-practices/](docs/features/adopt-engineering-discipline-practices/)):
  - `settings.APP_VERSION` is now the single source `FastAPI(version=...)`
    and `GET /version` both read from, locked against `CHANGELOG.md`'s top
    entry by `tests/test_version.py` — replaces `/version`'s previously
    hardcoded, unrelated `landing-page-v2` stub
  - Two new `.gitleaks.toml` rules (`connection-string-credential`,
    `google-oauth-client-secret`) close a demonstrated blind spot in
    gitleaks' default ruleset against this repo's own real incident shape
  - A file-scoped coverage floor (`.github/workflows/ci-cd.yml`) and a new
    golden-outcomes test class (`tests/test_change_request_decisions.py`)
    lock `ChangeRequestService.submit()`'s approve/park decision as a named
    invariant, independent of the whole-repo coverage aggregate
  - `docs/WHATS_NEW.md`: this changelog's parent-readable companion
  - `docs/ARCHITECTURE.md`: a whole-app architecture reference with its own
    update trigger-list, filling a gap `align-docs-with-current-app`
    explicitly left open
  - No user-facing change; nothing here touches `app/database/models.py`,
    a route, or a locale file

```

Everything below this (starting at `## [1.1.0] - August 24, 2026`) is
unchanged.

### 3. `docs/WHATS_NEW.md` entry — exact content

The existing `## September 2026` entry reads "Nothing new for you to see
this time." That was accurate about the cycle that produced it
(`adopt-engineering-discipline-practices` is explicitly internal-only),
but it is no longer an accurate closing statement for September once this
release also carries a real, parent-facing feature landing the same
month. **Replace that heading and body** (don't add a second, contradicting
September entry) with:

```markdown
## September 9, 2026

- If your child is old enough to check their own phone calendar, you can
  now connect their Mew schedule to it. Once you set this up for them
  from the Providers tab, any change to their schedule — one you
  approve, or one their care team makes — shows up automatically on
  their own Google Calendar, the same one they already check. It only
  ever adds to their calendar; nothing from their personal calendar is
  ever read back into Mew.
```

`docs/WHATS_NEW.md`'s own header promises "For the full engineering
detail behind each release, see `CHANGELOG.md`" — this entry stays
consistent with that split: no file paths, endpoint names, or internal
class names, matching every other entry in the file.

## Affected files

- `app/utils/config.py` — `Settings.APP_VERSION` literal: `"1.1.0"` →
  `"1.2.0"`. One-line change, comment above it unchanged (still correct).
- `CHANGELOG.md` — exact edit in Design §2 above: rename `[Unreleased]` →
  `[1.2.0] - September 9, 2026`, add the new `### 🔌 Integrations`
  subsection, leave the existing `### 🔧 Process / tooling` subsection's
  content byte-for-byte unchanged, open a fresh empty `## [Unreleased]`
  heading above it.
- `docs/WHATS_NEW.md` — exact edit in Design §3 above: replace the
  `## September 2026` heading and its "nothing new" body with
  `## September 9, 2026` and the kid-calendar-push paragraph.
- `docs/features/kid-calendar-push/plan.md` — new, written by Build (see
  "On plan.md" below), not by Design.
- No other file changes. Explicitly **not** touched:
  `app/database/models.py`, `app/services/calendar_sync_service.py`,
  `app/routers/kid_calendar_oauth.py`, `app/static/mew/mew.js`,
  `app/locales/*.json`, `tests/test_kid_calendar_connections.py`,
  `docs/ARCHITECTURE.md`, `docs/README.md`, `DOCUMENTATION_INDEX.md`.

### On `plan.md`

Build still writes one, kept deliberately short. CLAUDE.md's own loop
table has no "skip Build's plan.md if the change is small" exception, and
its own stated reasoning for why a small change still goes through every
phase ("the discipline of writing... costs little when the answer is
short") applies exactly as much to Build's artifact as to Plan's and
Design's. The alternative — treating "Build" as just making the edits
with no plan.md because there's no code — would quietly special-case this
cycle out of the one convention (`docs/features/<slug>/plan.md` exists for
every shipped change) that lets a future reader tell, from the folder
alone, that this went through the same process as everything else. Since
there's no code design decision left for Build to make (this spec already
fixes the exact literal, the exact heading rename, and the exact prose),
`plan.md` here is a short checklist of the three edits in "Affected
files" plus the acceptance criteria below to self-verify against, not a
new round of design.

## Data / API / UI changes

- **No schema change.** Nothing here touches `app/database/models.py`; no
  migration, no `ALTER TABLE`.
- **No endpoint change.** `GET /version` already reads
  `settings.APP_VERSION` (per `adopt-engineering-discipline-practices`),
  so it starts reporting `"1.2.0"` automatically the moment `APP_VERSION`
  is bumped — no code change needed there, just confirmation it takes
  effect.
- **No UI change, no new locale keys.** The kid-calendar-push UI
  (`renderKidCalendars`/`kidCalendarCard`, and its locale strings in all
  four `app/locales/*.json` files) already shipped in the commits this
  spec is documenting; `tests/test_locales.py`'s four-file contract is
  unaffected.

## Edge cases

- **`tests/test_changelog_parser_skips_unreleased` requires a literal
  `## [Unreleased]` heading to still exist in the file.** The edit in
  Design §2 must leave that heading in place (now empty) above
  `## [1.2.0]`, not delete it — dropping it would fail that test even
  though `APP_VERSION`/`CHANGELOG.md` would otherwise agree.
- **`docs/WHATS_NEW.md`'s prior "nothing new" claim would become false,
  not just outdated, if left in place next to a real September feature.**
  Design §3 replaces rather than appends to avoid two contradictory
  September entries in the same file.
- **Folding `adopt-engineering-discipline-practices`'s already-committed
  `[Unreleased]` text into `[1.2.0]` verbatim risks a copy/paste
  transcription error** (e.g. losing a bullet, breaking a nested list's
  indentation) since it's a move, not a rewrite. Build must diff the
  moved block against `git show HEAD:CHANGELOG.md`'s current
  `[Unreleased]` section (pre-edit) to confirm byte-for-byte equality
  apart from the heading itself.
- **A conflicting change lands on `develop` between this spec and Build**
  (e.g. another cycle adds its own `[Unreleased]` entry first). Build
  should re-read `CHANGELOG.md`'s current `[Unreleased]` section
  immediately before editing and fold in whatever is actually there at
  that time, not what this spec observed; the *mechanism* (rename +
  fresh empty heading + new subsection) holds regardless of exact
  content drift.
- **This entry describes a feature already live in production before it
  existed.** The CHANGELOG bullet says so explicitly ("Already built,
  merged and live in production ahead of this entry") so a future reader
  doesn't mistake September 9 for this feature's actual build/ship date —
  consistent with the intent's own insistence on not overstating what
  this cycle did.
- **Git tag for `v1.2.0`.** This repo's tagging discipline (`v1.0.0`
  through `v1.1.0`, confirmed in `adopt-engineering-discipline-practices`
  spec §1) is manual and has historically happened at the `develop`→
  `master` promotion, not at the feature-branch/PR-to-develop stage. Not
  this cycle's job to create it — flagged in Out of scope below so Deploy
  doesn't assume Build already did it.

## Acceptance criteria

1. `app/utils/config.py`: `Settings.APP_VERSION == "1.2.0"`.
2. `CHANGELOG.md`: the first `## [X.Y.Z]` heading (skipping `[Unreleased]`)
   is `## [1.2.0] - September 9, 2026`; a `## [Unreleased]` heading still
   exists above it with no content under it; the `### 🔌 Integrations`
   subsection under `[1.2.0]` names `KidCalendarConnection`,
   `push_to_kid_calendar`, `kid_calendar_oauth.py`, and
   `tests/test_kid_calendar_connections.py`; the pre-existing
   `### 🔧 Process / tooling` subsection's text is byte-identical to what
   was under `[Unreleased]` before this change (diff to confirm).
3. `tests/test_version.py` passes unmodified — specifically
   `test_app_version_matches_changelogs_top_versioned_entry` (now
   comparing `"1.2.0" == "1.2.0"`) and
   `test_changelog_parser_skips_unreleased` (the empty `[Unreleased]`
   heading is still present and not mistaken for a version).
4. `GET /version` (manually or via existing test) reports `"1.2.0"`.
5. `docs/WHATS_NEW.md` has a `## September 9, 2026` entry, no `## September
   2026` (undated) entry remains, and the entry contains no `.py`/`.js`
   file reference, no backticked identifier, and no `/`-delimited
   endpoint path (grep-checkable: `grep -E '\.(py|js)|`|/[a-z_]+/'`
   against just that entry should find nothing).
6. `docs/features/kid-calendar-push/` contains `intent.md`, `spec.md`,
   and `plan.md` (added by Build).
7. `git diff develop...<this-branch> --stat` touches only
   `app/utils/config.py`, `CHANGELOG.md`, `docs/WHATS_NEW.md`, and files
   under `docs/features/kid-calendar-push/` — confirming no application
   code, model, router, UI, locale file, or test was touched, per the
   intent's explicit constraint.
8. `pytest tests/` and `flake8 app tests` both still pass (the existing
   "Before committing" gate; a one-line config literal change is not
   expected to affect either, but this confirms it).

## Out of scope

- Any change to `app/services/calendar_sync_service.py`,
  `app/routers/kid_calendar_oauth.py`, `KidCalendarConnection`, or the
  Providers-tab UI — restated from the intent's own constraint; this
  cycle is a documentation/release-record fix, not a build.
- New tests for kid-calendar-push behavior — `tests/test_kid_calendar_connections.py`
  already covers it; restated from the intent.
- Manual re-verification that the feature works in production — restated
  from the intent; this session's own git-ancestry check and the existing
  regression suite already establish that.
- Creating/pushing the `v1.2.0` git tag — this repo's tagging discipline
  happens at `develop`→`master` promotion, which is Deploy's job (and
  needs an explicit human instruction per CLAUDE.md, never inferred
  here).
- Updating `docs/ARCHITECTURE.md` or its router/service/model
  inventories — kid calendar push added no new router, model, or service
  file (`kid_calendar_oauth.py` and `KidCalendarConnection` already
  existed before this cycle and are presumably already reflected there
  if `docs/ARCHITECTURE.md` was accurate when written); confirming that
  is a `docs/ARCHITECTURE.md`-maintenance question, not this release-notes
  cycle's job.
- Outlook support, Apple Calendar write support, multiple push targets
  per kid, and any change to the kid-facing simplified UI — restated from
  the intent's own non-goals; nothing in this design touches any of them.
