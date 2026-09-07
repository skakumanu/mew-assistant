# Spec: let a parent propose a schedule edit from the Week tab

*(Written retroactively - see `intent.md` in this directory and root
`CLAUDE.md`'s "AI-native SDLC" section.)*

(intent: docs/features/parent-week-edit/intent.md)

## Design

Pure frontend feature. `POST /requests` already authorizes
`RequestedBy.PARENT` and evaluates it through the same rule engine as a
kid's or provider's request - no backend change needed or wanted. Add a
per-session toggle in the Week tab that expands into an inline form (a
"New time" picker + Move button, and a Cancel session button with a
confirm prompt), calling `POST /requests` exactly as `provider.send()`
already does in `mew.js` for the provider persona. Reusing that existing
call shape (same endpoint, same body, same error-detail handling from the
`api()` helper) was chosen over inventing a parent-specific endpoint
because a second endpoint would either duplicate the rule-evaluation logic
or bypass it - both worse than reuse.

## Affected files

- `app/static/mew/mew.js` - split `loadWeek()` into fetch + `renderWeek()`
  so toggling a row doesn't require a re-fetch; add `sessionRow()` /
  `sessionForm()` / `requestChange()` to `parent`, modeled on the existing
  `provider.row()` / `provider.form()` / `provider.send()` pattern.
- `app/static/mew/mew.css` - `.session-row` becomes a `<button>` (toggle
  target); new `.week-edit` / `.week-edit__input` / `.session-row__action`
  styles matching the existing `.provider-session__form` conventions.
- `app/locales/{en,es,hi,ar}.json` - six new `parent.*` keys:
  `edit_session`, `close_edit`, `new_time_label`, `move_session`,
  `cancel_session`, `cancel_session_confirm`.
- `tests/test_change_requests.py` - new `TestParentInitiated` class.
- No changes to any file under `app/routers/` or `app/services/` - the
  point of this spec is that none are needed.

## Data / API / UI changes

No schema change, no new endpoint. UI: each Week tab session row gains a
toggle (`aria-expanded`) that reveals a `datetime-local` input seeded with
the session's current start time (browser-local, matching the existing
`provider.draft()` convention of treating browser-local as family-local -
not fully timezone-rigorous, but consistent with how the provider persona
already does it) and two buttons. Submitting calls `POST /requests` with
`{session_id, kind: 'move'|'cancel', new_start}` and shows the response's
own localized `message` field - no new client-side message strings needed
for outcomes, only for the two buttons and the confirm prompt.

## Edge cases

- **A move that violates a rule** (e.g. outside `earliest_start`/
  `latest_end`): parks for approval exactly like a kid's non-compliant
  request would - the parent then sees it in their own Inbox tab. Slightly
  unusual (a parent "approving" their own request) but correct given the
  design principle of one shared write path; not worth special-casing.
- **Cancel with `cancellation_needs_approval` on** (the fixture default):
  always parks, even for the parent - same reasoning as above.
- **Another family's session**: already rejected with 403 by
  `_authorize()` - no new check needed, but worth an explicit regression
  test given this is a new call site into that logic.
- **A no-op move** (same time re-submitted): not specifically handled or
  tested here - falls through to the same rule evaluation as any other
  move and is out of scope for this pass.

## Acceptance criteria

1. A parent can move a compliant session to a new time from the Week tab;
   it applies immediately and the Week tab reflects the new time.
2. A parent can cancel a session; when `cancellation_needs_approval` is
   on, it parks with reason codes rather than applying immediately.
3. A parent cannot move or cancel a session belonging to another family
   (403).
4. All four locale files carry the six new keys (`tests/test_locales.py`
   parity check).
5. Full suite and `flake8 app tests` (hard-fail pass) stay green.

## Out of scope

Same as intent.md's non-goals: no Week tab redesign beyond the edit
affordance, no bulk actions, no changes to the kid-calendar push pipeline
itself.
