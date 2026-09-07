# Plan: let a parent propose a schedule edit from the Week tab

*(Written retroactively - see `spec.md` in this directory.)*

Branch: `feature/parent-week-edit` off `develop`.

1. Add the six new locale keys (`edit_session`, `close_edit`,
   `new_time_label`, `move_session`, `cancel_session`,
   `cancel_session_confirm`) to all four `app/locales/*.json` files.
   Verify with `pytest tests/test_locales.py`.
2. In `app/static/mew/mew.js`: add `weekOpen`/`weekDraft` to `parent.state`;
   split `loadWeek()` into a fetch that stores the result and a
   `renderWeek()` that draws from it; add `sessionRow()` (the toggle
   button + rail/body/pill, modeled on `provider.row()`), `sessionForm()`
   (the datetime-local input + Move/Cancel buttons, modeled on
   `provider.form()`), and `requestChange()` (the `POST /requests` call,
   modeled on `provider.send()`). Verify with `node --check`.
3. In `app/static/mew/mew.css`: convert `.session-row` to button styling
   (width 100%, cursor, text-align, an `[aria-expanded="true"]` variant for
   the connected-form look), add `.session-row-wrap`, `.session-row__action`,
   `.week-edit`, `.week-edit__input`.
4. Add `TestParentInitiated` to `tests/test_change_requests.py`: a
   compliant parent move auto-applies; a parent cancel parks for approval
   under the default `cancellation_needs_approval` rule; a parent cannot
   touch another family's session (403).
5. Run the full suite (`pytest tests/ -v --cov=app --cov-report=term-missing`)
   and `flake8 app tests` (both passes). Fix anything either catches.
6. Commit, push, open PR to `develop`, watch CI, merge once green.
7. Once dogfooded on `develop`: open the `develop` → `master` promotion PR
   on explicit instruction, watch CI, merge, confirm `deploy_fly` and its
   `/health` poll succeed.

This is exactly what shipped as PR #148 (feature branch) and PR #149
(promotion) - reconstructed here as the plan.md this feature's Build phase
would have produced had this skill existed at the time.
