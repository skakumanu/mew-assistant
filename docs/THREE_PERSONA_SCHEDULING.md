# Three-persona scheduling

One schedule, three people, almost no decisions.

A parent declares their rules once. A kid and a service provider propose
changes. Anything that satisfies every active rule is applied immediately and
recorded in a quiet log; anything that does not reaches the parent as one card
with three compliant alternatives already attached.

The assistant is invisible: a deterministic rule engine, not a chatbot.

---

## The loop

```
                       POST /requests
                     (kid | provider | parent)
                              │
                              ▼
                   ┌──────────────────────┐
                   │  RuleEngine.evaluate │   pure, no DB, no AI
                   └──────────┬───────────┘
                  passes      │      fails
              ┌───────────────┴───────────────┐
              ▼                               ▼
   session moves + calendar         ApprovalRequest (PENDING)
   write-back + ChangeLogEntry      + reason_codes
   (tone=auto) + confirmation       + 3 alternatives (closest first)
                                             │
                                             ▼
                                POST /parent/approvals/{id}/choose
                                (one tap - the expected path)
```

`POST /requests` is the only write path for a kid or a provider. No client
decides whether something is allowed.

## Code map

| Piece | File |
| --- | --- |
| Deterministic engine (pure) | `app/services/rule_engine.py` |
| Rules ⇄ engine translation, backfill | `app/services/ruleset_service.py` |
| The loop: evaluate, apply or park | `app/services/change_request_service.py` |
| Codes and keys → sentences per reader | `app/services/presenter.py` |
| Locale resolution and rendering | `app/utils/locale.py`, `app/utils/locale_context.py` |
| Locale files (`en.json` is the contract) | `app/locales/` |
| Schemas | `app/schemas/change_request.py` |
| Routers | `app/routers/rules.py`, `requests.py`, `provider.py`, `parent_approval.py`, `kid_friendly.py` |
| Screens | `app/routers/mew_ui.py`, `app/templates/mew/`, `app/static/mew/` |
| Migration | `scripts/migrate_three_persona_scheduling.py` |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/rules` | The parent's rule set, protected blocks and weekly caps |
| `PUT` | `/rules` | Upsert; only fields present in the body are touched |
| `POST` | `/requests` | The one write path — `{session_id, kind, new_start?, new_provider_person_id?}` |
| `GET` | `/parent/approvals/pending` | Existing list, now carrying `reason_codes` and `alternatives` |
| `GET` | `/parent/approvals/inbox` | The "Needs you" cards, rendered for this reader |
| `POST` | `/parent/approvals/{id}/approve` | Approve as asked ("Allow their time anyway") |
| `POST` | `/parent/approvals/{id}/choose` | Approve one alternative — `{alternative_index}` |
| `POST` | `/parent/approvals/{id}/deny` | Deny; a note is still required |
| `GET` | `/parent/log?limit=8` | "Handled for you" |
| `GET` | `/parent/week` | Day headings, sessions, `updated` pills |
| `GET` | `/kid/today` | Today's cards and pending flags |
| `POST` | `/kid/ask` | The kid's two buttons — `{session_id, ask: "later"\|"skip"}` |
| `GET` | `/provider/sessions` | That organisation's sessions for this child |

`POST /requests` answers with one of two shapes and the same status code:

```jsonc
// rules satisfied - it already happened
{ "auto_applied": true, "session": { ... }, "message": "Confirmed for Fri 2pm. ..." }

// rules not satisfied - the parent has one card
{ "auto_applied": false, "request_id": 12,
  "reason_codes": ["latest_end"],
  "reasons_text": "outside the allowed hours",
  "alternatives": [ { "index": 0, "start": "...", "label": "Thu, Sep 10 at 4:30pm",
                      "note": "closest" }, ... ] }
```

## Reason codes

A rule failure is identified by a stable code, never by a sentence, so one
parked request reads correctly for a parent in Spanish and a provider in
English. The codes are locked:

`min_notice` · `latest_end` · `protected_block` · `same_provider` · `buffer` ·
`max_per_week` · `cancel_needs_approval` · `outside_allowed_days`

`latest_end` covers the whole allowed-hours window — too early and too late
alike — which is why its string reads "outside the allowed hours".

Log rows follow the same discipline: `ChangeLogEntry` stores a locale key
(`parent.log_moved`) plus parameters, and the sentence is rendered when it is
read.

## Data model

New tables: `provider_orgs`, `provider_people`, `scheduled_sessions`,
`rule_sets`, `protected_blocks`, `weekly_caps`, `change_log_entries`,
`user_locales`.

`approval_requests` gains `requested_by`, `provider_org_id`, `change_kind`,
`scheduled_session_id`, `new_start_utc`, `new_provider_person_id`,
`reason_codes`, `alternatives`, `auto_applied`, `chosen_alternative_index`.

The session model is called `ScheduledSession`, not `Session`: this codebase
already has a `Session` model for assistant conversations, and
`sqlalchemy.orm.Session` is imported across the service layer.

### Migration

```bash
DATABASE_URL=postgresql://... python scripts/migrate_three_persona_scheduling.py --dry-run
DATABASE_URL=postgresql://... python scripts/migrate_three_persona_scheduling.py
```

Idempotent, and safe to re-run. It creates the new tables, adds the new
columns, and seeds one `RuleSet` per parent from whatever the family already
declared through the older free-form `ApprovalRule` rows — so nobody re-enters
their rules.

## What was reused, and what changed

| Area | Outcome |
| --- | --- |
| `parent_approval.py`, `approval_service.py` | **Reused.** Gained "approve one of three alternatives" as a third action. |
| `ApprovalRule` | **Extended.** Backfilled into `RuleSet`; `SmartApprovalService` keeps its own rows. |
| `smart_approval_service.py` | **Split.** The deterministic engine runs FIRST. A request that satisfies the declared rules never waits on a confidence score. |
| `kid_friendly.py` | **Changed semantics.** A compliant request is applied and the kid is told it is done. Cancellations still route to the parent when `cancellation_needs_approval` is on. |
| Kid copy | **Replaced.** Plain sentences, no emoji, 56px targets. Stickers map onto the "calm days in a row" streak. |
| Provider persona | **New.** `ProviderOrg` / `ProviderPerson`, and `requested_by` on requests. |
| `ScheduleSuggestion` | **Reused** in spirit — alternatives come from `RuleEngine.alternatives()`. |
| Calendar integration | **Reused.** Applied changes write back as calendar updates, best effort: a calendar hiccup never undoes a change the rules allowed. |
| Voice | **Reused, constrained.** Voice may REQUEST anything and approve nothing — it calls `POST /requests` like every other caller. |
| `app/utils/language_detector.py` | **Not used for UI.** UI locale comes from `Accept-Language` / the device, never from sniffing message text. |

## Screens

`GET /app/parent`, `GET /app/kid`, `GET /app/provider` — Jinja shells plus a
small vanilla-JS runtime (`app/static/mew/mew.js`), matching the rest of
`app/templates/`. The prototype's own runtime (`support.js` in the design
bundle) is not ported; these talk to the real API.

## Accessibility

These are requirements, not preferences, and they are enforced in code:

* Nothing is announced in a single channel. Every banner also lands in a live
  region as the same sentence, and read-aloud speaks that same sentence.
* Status is never colour alone — each rule row carries the word "on"/"off",
  and every state has text.
* One-column reading order per screen; buttons announce intent.
* Touch targets never shrink responsively: kid 56px, provider 50px, parent
  46–48px.
* Text to 200% without a sideways scroll.
* Symbols mode: two taps per request, the same two every time, in the same
  place. No timeouts.
* `prefers-reduced-motion` disables all motion.
* Voice can request, never approve.

Real AAC symbol sets (PCS, ARASAAC, Bliss) need licensed artwork. The design
leaves a slot for them; the shipped symbols are plain glyphs.

## Internationalisation

Locale resolves from `Accept-Language`, then an explicit per-user override
recorded in `UserLocale` (`source` says which). `meta.dir` drives RTL and
`meta.clock` drives 12h/24h. Per-person locale is real: a parent reading
Spanish and a provider reading English share one schedule.

`app/locales/en.json` is the contract — `tests/test_locales.py` fails if any
locale drifts from its keys or placeholders.

**`hi` and `ar` are unreviewed machine-quality translations. They need a
native speaker before shipping.** See `app/locales/README.md`.

## Tests

```bash
pytest tests/test_rule_engine.py tests/test_ruleset_service.py \
       tests/test_change_requests.py tests/test_locales.py
```

* `test_rule_engine.py` — pure, no DB. Locks the reason codes.
* `test_ruleset_service.py` — defaults, engine translation, `ApprovalRule` backfill.
* `test_change_requests.py` — the loop end to end, both outcomes, authorisation.
* `test_locales.py` — the locale contract and device-based resolution.
