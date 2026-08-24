# Known issues

Findings from a dead-code sweep (2026-08-24) that are real bugs but out of
scope for the sweep itself — tracked here rather than fixed blind, since
some require a design decision, not just a correction.

## The voice command pipeline does not work end to end

**Symptom:** `POST /voice/command` fails on every real call.

**What's fixed:** `VoiceService.process_voice_command` used to construct
`VoiceCommand(...)` with four kwargs that don't exist on the model
(`audio_duration`, `transcript`, `entities`, `timestamp`) — SQLAlchemy's
default `__init__` raised `TypeError` on every call. Fixed in this sweep;
see `tests/test_voice_service.py`.

**What's still broken, one step further in:** `_process_intent()` runs
immediately after that DB write and reads `transcription.intent` and
`transcription.entities`. Neither field exists on `VoiceTranscription`
(`app/schemas/voice.py`) — it only defines `text`, `language`, `confidence`.
Every constructor of `VoiceTranscription`
(`app/integrations/voice_integration.py`, both the real Azure path and
`_mock_transcription`) passes `intent=`, `entities=`, `duration=`, and
`timestamp=` anyway. Pydantic's default behaviour silently **drops** unknown
constructor kwargs rather than raising, so this doesn't fail loudly — it
just produces an object with no `.intent` attribute at all, and the next
access to it raises `AttributeError`. That's why nothing caught this:
`_mock_transcription()` (the path used whenever Azure credentials aren't
configured, i.e. every dev/test environment) *looks* like it's returning a
fully-populated transcription, but four of its seven fields are silently
discarded before the object exists.

There's also a return-type mismatch: `VoiceCommandResponse.transcription`
is typed `Optional[str]`, but `voice_service.py` passes the whole
`VoiceTranscription` object.

**Why this wasn't fixed here:** deciding what `VoiceTranscription` should
actually carry (make `intent`/`entities`/`duration` real optional fields?
change the NLU extraction to return them separately instead of bolting them
onto the transcription object? what does the response schema owe callers?)
is a design call, not a mechanical correction — different in kind from
deleting a duplicate file or fixing a column-name typo.

**To reproduce:**
```python
from app.integrations.voice_integration import VoiceIntegration
import asyncio
t = asyncio.run(VoiceIntegration().transcribe_audio(b"x", hint_language="en"))
t.intent  # AttributeError: 'VoiceTranscription' object has no attribute 'intent'
```

**Affected:** `app/services/voice_service.py` (`_process_intent` and every
`_handle_*` method it dispatches to), `app/integrations/voice_integration.py`,
`app/schemas/voice.py`.

## Other findings from the same sweep — not bugs, need a product decision

- `app/routers/backup.py` — a complete, working admin backup/restore/GDPR
  export flow that was never registered in `app/main.py`. Not broken, not
  referenced by anything, no tests. Ship it or delete it is a product call.
- `app/routers/voice_platforms.py` — complete Siri/Alexa/Google
  Assistant/Tesla webhook integrations, same situation: working, unmounted,
  untested, no comment marking it deprecated.
- Five orphaned service files, untouched since the initial commit and
  referenced by nothing: `app/services/ai_service.py`, `caregiver.py`,
  `onboarding_service.py`, `tutor.py`, `scheduler.py` (not to be confused
  with the live `ai_scheduler_service.py`). Left in place deliberately —
  deleting scaffolding for a feature nobody has decided against yet destroys
  work that might still be wanted.

## `tests/test_auth.py::test_refresh_token` is flaky (~2.5% failure rate)

**Not something this PR touched or caused** — found while landing PR #53,
which never touches `app/middleware/bot_protection.py`, `app/routers/auth.py`
or `tests/test_auth.py`. Documented here because it's real, reproducible, and
otherwise easy to mistake for a broken PR on the next red run.

**Cause:** `BotProtectionMiddleware._check_suspicious_content` regex-scans
every POST body against a fixed pattern list that includes `r"(--|;)"`
(meant to catch SQL-injection-style tautologies). Refresh tokens are
base64url-encoded JWTs, which use `-` as part of their alphabet. Any token
whose encoding happens to contain two consecutive `-` characters trips the
pattern and the request is rejected with `400 Bad Request` before it ever
reaches the `/auth/refresh` handler — nothing wrong with the token or the
handler, the request never got there.

**Measured:** 1 failure in 40 local runs (~2.5%), consistent with the
theoretical collision rate for two adjacent characters landing on `-` in a
base64url alphabet (64 symbols) across a token-length string.

**Not fixed here:** the middleware's suspicious-content regex is
security-sensitive shared code — every POST endpoint in the app goes through
it, not just `/auth/refresh` (any base64-bearing payload is equally exposed:
image uploads, encoded IDs, other JWTs). Tightening it needs its own
change and its own review, not a rider on an unrelated PR.
