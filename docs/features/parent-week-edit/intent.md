# Intent: let a parent propose a schedule edit from the Week tab

*(Written retroactively as a worked example for the AI-native SDLC - see
root `CLAUDE.md`. This feature shipped as PR #148 before this artifact
chain existed; this reconstructs what each phase would have produced.)*

## Problem

While dogfooding the app as a parent, after confirming a duplicate-events
bug was fixed, the reporter tried to act on that confirmation the natural
way - editing a session directly from the Week tab - and hit a dead end:
"I am not able to make edit to the schedule in Week tab for approve a
schedule change, I am in parent app." Reading `loadWeek()` in
`app/static/mew/mew.js` confirmed the Week tab renders sessions as pure
read-only rows (title, time, provider name, an "updated" pill) with no
edit, cancel, or request-change affordance anywhere in the parent UI.

## Why now

This blocks the parent from testing the very feature (kid-calendar push on
an approved change) the dogfooding session set out to exercise end-to-end.
It's also a gap, not a design choice already made elsewhere: the backend's
`_authorize()` in `change_request_service.py` already recognizes a parent
as a legitimate actor on `POST /requests` (`RequestedBy.PARENT`, when
`child.parent_id == actor.id`) - the write path exists and is exercised by
kids and providers today, it was simply never wired up for the parent's
own Week tab.

## Constraints

- Must reuse the existing `POST /requests` write path - this repo's
  design principle (`mew.js`'s own header comment) is that no client
  decides whether a change is allowed; every ask goes through the rule
  engine the same way regardless of who's asking.
- No new backend authorization logic - the parent-as-actor path is already
  correct and tested elsewhere; a new endpoint would duplicate it.

## Non-goals

- Redesigning the Week tab's overall layout - only adding the edit
  affordance to the existing session rows.
- Bulk edit / multi-session actions.
- Anything about the kid-calendar push pipeline itself - that's already
  built and separately dogfooded; this only unblocks testing it.

## Success looks like

A parent can tap a session in the Week tab, see an inline form, move it to
a compliant time (applies immediately, same as a kid's or provider's
compliant request) or cancel it (parks for approval when the rule set
requires it, exactly like any other actor's cancel request) - without any
new backend code.
