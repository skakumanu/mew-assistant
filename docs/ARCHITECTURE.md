# Architecture

This describes Mew Assistant as `align-docs-with-current-app` (PR #152)
left it: WorkOS sign-in, Fly.io deployment, three-persona scheduling. It
does not resurrect any pre-#152 Azure/Container-Apps material that pass
removed or flagged - the same shape of stale documentation that produced
this cycle's own gitleaks incident (a leftover Azure config export, not
live topology, committed by mistake).

## 1. Overview

Mew Assistant is a deterministic rule-engine scheduling assistant for
three personas - a parent (or other caregiver), a kid, and a service
provider (e.g. an ABA clinic or speech practice) - not a chatbot. A
parent declares their scheduling rules once; a kid or a provider proposes
a change; the engine either applies it immediately or parks it for the
parent with reason codes and compliant alternatives already attached. See
[`docs/THREE_PERSONA_SCHEDULING.md`](THREE_PERSONA_SCHEDULING.md) for the
request/approval loop in depth - this document points at it rather than
re-explaining it.

## 2. Request lifecycle

```
persona (parent | kid | provider)
        │
        ▼
  FastAPI router (app/routers/)
        │
        ▼
  ChangeRequestService.submit()   -- the one write path
        │
        ▼
  RuleEngine.evaluate()           -- pure, no DB, no AI
        │
        ▼
  DB write (ScheduledSession, ApprovalRequest, ChangeLogEntry)
        │
        ▼
  calendar write-back (best-effort - never undoes an applied change)
        │
        ▼
  notification (stored, then delivered best-effort by email/SMS)
```

See `docs/THREE_PERSONA_SCHEDULING.md`'s own loop diagram for the
approve/park branches in full; this is the same loop, one level up.

## 3. Router layer map

`app/routers/`, 24 files, grouped by concern:

- **Sign-in & auth**: `auth.py`, `oauth_workos.py`, `oauth_success_page.py`
- **The scheduling loop**: `requests.py` (`change_requests_router`),
  `rules.py`, `parent_approval.py` (both its routers), `kid_friendly.py`,
  `provider.py`, `smart_approval.py`
- **Calendar**: `calendar.py`, `calendar_web.py`, `calendar_oauth.py`,
  `calendar_sync.py`, `kid_calendar_oauth.py`
- **Voice**: `voice.py`, `voice_requests.py`, `voice_platforms.py`
- **Setup & onboarding**: `onboarding_setup.py`, `session.py`
- **Cross-cutting / other**: `mew_ui.py`, `mobile.py`, `message.py`,
  `summary.py`, `notifications.py`, `webhooks.py`, `ai_scheduler.py`,
  `landing.py`, `debug_page.py`

## 4. Data model

`app/database/models.py`, ~38 model/enum classes, grouped by domain:

- **Identity**: `User`, `FederatedIdentity`, `UserRole`
- **Scheduling**: `ScheduledSession`, `RuleSet`, `ProtectedBlock`,
  `WeeklyCap`, `ApprovalRequest`, `ApprovalAuditLog`, `ChangeLogEntry`
- **Providers**: `ProviderOrg`, `ProviderPerson`, `ProviderOrgConnection`
- **Calendar**: `KidCalendarConnection`, `OAuthProvider`
- **Notifications**: `Notification`, `NotificationKind`
- **Locale**: `UserLocale`

**Predates the three-persona model, confirm live-vs-legacy before
documenting as current:** `Family`, `ApprovalRule`, `ScheduleEntry`,
`UserProfile`. These still exist in the schema but this document does not
claim they are part of the current scheduling loop above.

## 5. Services layer

`app/services/`, 23 files, grouped the same way as the router map:

- **The scheduling loop**: `rule_engine.py` (pure engine),
  `change_request_service.py` (the one write path — orchestrates the
  engine, the DB, calendar write-back and notifications),
  `ruleset_service.py` (stored `RuleSet` ⇄ engine translation),
  `presenter.py` (reason codes → sentences), `smart_approval_service.py`
  (advice on already-parked requests, never a decision)
  — `docs/THREE_PERSONA_SCHEDULING.md` covers the first two in depth;
  linked, not duplicated, here.
- **Calendar**: `calendar_service.py`, `calendar_sync_service.py`
- **Voice**: `voice_service.py`
- **Notifications**: `notification_service.py`, `notification_delivery.py`
- **Setup & onboarding**: `onboarding_service.py`, `session_service.py`
- **Auth**: `auth_service.py`, `workos_client.py`
- **Cross-cutting / other**: `ai_scheduler_service.py`, `ai_service.py`,
  `approval_service.py`, `caregiver.py`, `kid_service.py`,
  `message_service.py`, `mobile_service.py`, `scheduler.py`,
  `summary_service.py`, `tutor.py`

## 6. Deployment topology

Fly.io (`fly.toml`, `Procfile`, `Dockerfile`) - see `CLAUDE.md`'s
"Deployment" and "CI/CD gates" sections for the deploy path and the five
CI gates that must pass first; not duplicated here.

`infrastructure/azure/` and root `*.bicep` files are **dormant legacy**,
not live topology - kept for reference/teardown only, per `CLAUDE.md`.

## 7. Trigger-list

Update this document when:

- a new router file is added to `app/routers/`;
- a new table/model is added to `app/database/models.py`;
- a new service is added to `app/services/`;
- deployment topology changes (`fly.toml`, `Dockerfile`, `Procfile`);
- a new external integration is added (new OAuth provider, new calendar
  source, new notification channel).

This is a checklist discipline, not a CI gate (see
`docs/features/adopt-engineering-discipline-practices/spec.md`'s Edge
Cases for why an automated "did the architecture change" detector is out
of proportion for this cycle) - a human reviewer applies it, the same way
they already apply "Before committing" in `CLAUDE.md`.
