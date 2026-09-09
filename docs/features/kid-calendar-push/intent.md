# Intent: Kid calendar push

## Problem

The raw request: a kid old enough to check their own phone calendar should
be able to see their Mew schedule there too, pushed one-way from Mew into
their own Google Calendar, set up by the parent on the kid's behalf — not
only visible in the simplified kid UI.

Investigation of the actual codebase (not the "prior research" notes this
cycle started from, which were explicitly flagged as unverified) shows
this mechanism is **already fully implemented, tested, and wired into the
UI** in the current working tree:

- `app/database/models.py`'s `KidCalendarConnection` (one push target per
  kid, enforced by a unique constraint on `child_id` alone) already exists.
- `app/services/calendar_sync_service.py`'s `push_to_kid_calendar()`
  already creates/updates/cancels a mirrored event on the kid's own Google
  Calendar, tagging what it writes (`MIRROR_PROPERTY_KEY`) so a pull can
  never re-ingest its own mirror.
- Both hook points a push-only feature needs are already wired: parent
  approvals and rule auto-clears call it via
  `change_request_service.py`'s `_write_back_to_calendar` (independently
  of the provider-calendar write-back, so one failing never blocks the
  other), and `CalendarSyncService.pull_org` also calls it for every
  session touched by a provider rescheduling on their own calendar.
- `app/routers/kid_calendar_oauth.py` already implements the parent-facing
  OAuth connect/callback/calendar-picker flow, scoped and ownership-checked
  (a parent can only connect a kid that is actually theirs).
- The `calendar.readonly` scope-vs-`update_event()`/`cancel_event()`
  mismatch the prior-research notes flagged as a live, unverified bug is
  **not currently a bug**: `app/routers/calendar_oauth.py`'s
  `CALENDAR_SCOPE` is already the full `.../auth/calendar` scope, and its
  own comment states this was widened specifically to support this kid
  push flow (and incidentally fixed the same latent problem for the
  provider write-back path).
- The Providers tab already renders a per-kid calendar card
  (`app/static/mew/mew.js`'s `renderKidCalendars`/`kidCalendarCard`) with a
  connect button, a calendar picker, a shared-calendar conflict warning,
  and copy localized in all four supported locales.
- `tests/test_kid_calendar_connections.py` covers the connect flow,
  ownership isolation across families, the calendar picker, push
  create/update/cancel, and two regression cases whose own docstrings
  describe real production/dogfooding incidents (a shared push/pull
  calendar causing a duplicate-event loop; a pre-existing collision being
  wrongly re-flagged on a plain reconnect).
- Matching named git branches already exist for this build and its
  hardening (`feature/kid-calendar-push`,
  `feature/block-shared-push-pull-calendar`,
  `hotfix/kid-calendar-push-pull-loop`,
  `hotfix/kid-calendar-event-id-column`,
  `hotfix/allow-unchanged-calendar-resave`).

What is genuinely missing is not code: it's the paper trail and the
release signal. There is no `docs/features/kid-calendar-push/` (this is
the first artifact for it), no `CHANGELOG.md` entry — neither under the
current `[Unreleased]` heading nor under `[1.1.0]`, the release that
predates this work — and no `docs/WHATS_NEW.md` entry. `WHATS_NEW.md`'s
most recent entry (September 2026) explicitly says "Nothing new for you
to see this time," which as of today (September 9, 2026) means no parent
has ever been told this exists, and there's no committed evidence this
went through this repo's own Test/Deploy gates as a named, verified
change. Whether the code is actually live on `develop`/`master` in
production could not be confirmed from this working tree with the tools
available to this phase (no git history/ancestry inspection) — that
confirmation is exactly what needs to happen before this closes.

## Why now

CLAUDE.md's own convention ("Before committing") requires a user-visible
change to carry an `APP_VERSION` bump, a `CHANGELOG.md` entry, and a
`docs/WHATS_NEW.md` entry in the same release. A fully built, dogfooded
(the regression tests' own docstrings describe real incidents this
already went through), user-facing capability sitting undocumented and
possibly unannounced is exactly the kind of gap that undermines the audit
trail this SDLC exists to produce — and, more concretely, if it is live
today with nobody told, it's a parent-facing feature going to waste on the
group who asked for it (a kid old enough to check their own phone
calendar). This is worth resolving before any other calendar work
(Outlook, additional providers) builds on top of an undocumented
foundation.

## Constraints

- Must not re-implement, redesign, or modify the existing push mechanism.
  `app/services/calendar_sync_service.py`, `app/routers/kid_calendar_oauth.py`,
  `KidCalendarConnection`, and the Providers-tab UI in `app/static/mew/mew.js`
  already work and are regression-tested against real incidents; touching
  them here would be scope creep, not scoping.
- Must follow the existing release convention: `APP_VERSION` bump,
  `CHANGELOG.md` entry, `docs/WHATS_NEW.md` entry (parent-readable, no file
  paths or internal names), all in the same change.
- Must independently confirm actual deployment status (is this merged to
  `develop`? Has it reached `master`/production?) before deciding what, if
  anything, Design needs to scope beyond documentation — this Plan phase
  could not verify that with the tools available to it.

## Non-goals

- Building push-to-kid-calendar itself — it already exists.
- Outlook support — already an explicit, separate future phase per the
  shape confirmed earlier, and untouched by the existing implementation.
- Apple Calendar write support — permanently out of scope (no clean OAuth
  path to iCloud); Apple stays read-only ICS, unaffected by this.
- Multiple push targets per kid — the existing `KidCalendarConnection`
  unique constraint on `child_id` already enforces exactly one, by design.
- Any change to how the kid-facing simplified UI shows the schedule today.

## Success looks like

A parent who connects their kid's Google Calendar today sees their kid's
Mew schedule appear and stay current there (this may already be true —
Design/Build's first job is to confirm it, not assume it). Beyond that:
this capability has a `CHANGELOG.md` entry, a matching plain-language
`docs/WHATS_NEW.md` entry, and an `APP_VERSION` bump landed together, so
the release record accurately reflects that it shipped. If investigation
turns up that the code is not actually merged past a stale feature branch,
success instead means getting it through Test and Deploy properly before
any announcement is written.
