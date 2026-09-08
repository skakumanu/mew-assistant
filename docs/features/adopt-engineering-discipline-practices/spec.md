# Spec: adopt five engineering-discipline practices from `llm-pricing-mcp-server`

(intent: docs/features/adopt-engineering-discipline-practices/intent.md)

## Design

Each of the five items got its own investigation before a mechanism was
proposed, per the intent's own instruction not to adopt anything by rote.
Two (items 1 and 5) get a concrete build; one (item 2) gets a narrow,
evidence-based `.gitleaks.toml` addition instead of a redundant manual
check; one (item 3) gets two small additions using tooling already in the
repo; one (item 4) gets the lighter of the two options the intent asked
Design to weigh, with the reasoning for not building the heavier one made
explicit.

### 1. Semantic version bumping — collapse three signals into one

**Current state, verified:**
- `app/utils/config.py`'s `Settings.APP_VERSION` defaults to `"1.0.0"` and
  is read nowhere (`grep -rn "APP_VERSION" app` shows only its own
  declaration).
- `app/main.py` line 30 sets `FastAPI(version="1.1.0")` — this *does*
  agree with `CHANGELOG.md`'s top entry, `[1.1.0] - August 24, 2026`, and
  with the `v1.1.0` git tag (2026-08-24). Confirmed via
  `git for-each-ref --sort=-creatordate refs/tags`: this repo already has
  a real, if manual, discipline of tagging releases in step with
  `CHANGELOG.md` (`v1.0.0` → `v1.1.0`, six tags total) — it's just that
  `APP_VERSION` and `/version` were never plugged into it.
- `app/main.py`'s `GET /version` (line ~145) hardcodes
  `{"version": "landing-page-v2", "deployed": "2025-11-28T02:00:00Z"}`,
  disconnected from both of the above.

**Mechanism:** make `settings.APP_VERSION` the single source every
runtime signal reads from, and lock it against `CHANGELOG.md` with a
test:
- `app/main.py`: `FastAPI(version=settings.APP_VERSION)` instead of the
  literal `"1.1.0"`.
- `app/main.py`'s `GET /version`: return
  `{"version": settings.APP_VERSION, "deployed": <build/deploy timestamp>}`
  instead of the hardcoded stub. (The `deployed` field's exact source —
  e.g. a `BUILD_TIME` env var Fly can inject, or simply dropped if no
  reliable source exists — is Build's call; it is not the drift this
  item is about.)
- Bump `APP_VERSION` in the same PR whenever a change is user-visible,
  following semver (patch/minor/major), and add the matching
  `CHANGELOG.md` entry and git tag in the same release, extending the
  tagging discipline that already exists rather than inventing a new one.
- New test, `tests/test_version.py`: (a) `GET /version` returns
  `settings.APP_VERSION`; (b) parse `CHANGELOG.md`'s first `## [X.Y.Z]`
  heading (skipping `## [Unreleased]`) and assert it equals
  `settings.APP_VERSION` — so a PR that bumps one without the other fails
  CI instead of drifting silently again.
- `CLAUDE.md` gains a "Before committing" checklist line (draft wording,
  Build finalizes): *"If this change is user-visible, bump `APP_VERSION`
  in `app/utils/config.py` (semver), add a matching `CHANGELOG.md` entry
  and git tag."*

**Alternatives considered:**
- *Derive version from git describe/commit SHA at runtime, no manual
  bump.* Rejected: the intent asks for the discipline of bumping, and
  this repo already has a tagging habit (six semver tags) worth
  reinforcing, not replacing with an automatic scheme it doesn't use
  anywhere else.
- *A new `app/__version__.py` single-source module.* Rejected as
  unnecessary churn — `Settings.APP_VERSION` already exists, was clearly
  built for exactly this, and is simply unused today.

### 2. Secret-scan gap — verified against gitleaks' actual default ruleset, not assumed

`.gitleaks.toml` has zero `[[rules]]` of its own (only a doc-placeholder
allowlist), so detection today is entirely gitleaks v8.18.4's bundled
default config (confirmed by fetching
`https://raw.githubusercontent.com/gitleaks/gitleaks/v8.18.4/config/gitleaks.toml`
and diffing against what this repo overrides — nothing). The real
incident's shape, read directly from the fix commit (`98ae088`, since the
file itself was deleted): `ca-config-no-probes.json`, an `az containerapp
show`-style export, containing:

```
"name":  "DATABASE_URL",
"value":  "postgresql://mewadmin:<REDACTED-ROTATED-PASSWORD>@mew-assistant-db.postgres.database.azure.com:5432/mew_assistant"
...
"name":  "GOOGLE_CLIENT_SECRET",
"value":  "GOCSPX-<REDACTED-ROTATED-SECRET>"
...
"name":  "MICROSOFT_CLIENT_SECRET",
"value":  "<REDACTED-ROTATED-SECRET-WITH-TILDE>"
```

(Both credentials were rotated earlier this session; values are redacted here
rather than re-committed verbatim, to avoid undoing the `git-filter-repo`
history purge that already removed them once.)

The only default rule broad enough to have plausibly caught any of this
is `generic-api-key`:

```
regex = (?i)(?:key|api|token|secret|client|passwd|password|auth|access)
        (?:[0-9a-z\-_\t .]{0,20})(?:[\s|']|[\s|"]){0,3}
        (?:=|>|:{1,3}=|\|\|:|<=|=>|:|\?=)
        (?:'|"|\s|=|`){0,5}([0-9a-z\-_.=]{10,150})(?:['|"|\n|\r|\s|`|;]|$)
entropy = 3.5
```

Tracing this regex by hand against the actual leaked lines (no `\n` is
in any of its character classes, so a match cannot cross a line break):

- **`GOOGLE_CLIENT_SECRET` / `MICROSOFT_CLIENT_SECRET` values**: the
  export splits the identifying field and its value across two separate
  JSON lines (`"name": "...SECRET",` then `"value": "GOCSPX-..."` on the
  next line). The keyword (`secret`) is on the first line; the value is
  on the second, which contains no keyword at all (`"value"` matches
  none of `key/api/token/secret/client/passwd/password/auth/access`).
  `generic-api-key` cannot fire on either line. **Demonstrated blind
  spot #1: this repo's own `name`/`value`-split export shape defeats
  keyword-adjacent generic secret detection.**
- **The Postgres password**: the leaked value sits inside a
  connection-string URI, after a bare `:` inside the netloc, not after a
  `key<operator>` pair. Tracing the regex from the substring `password`
  forward: the characters that follow never produce one of
  the required operator characters (`=`, `:`, etc.) before hitting `@`,
  which isn't in any of the rule's allowed character classes — so the
  match fails regardless of line-splitting. Checked the fetched default
  config for any dedicated connection-string/database-credential rule:
  there is none (`grep -i "postgres\|database\|connection"` against the
  fetched `gitleaks.toml` returns nothing; the only Google-related rule
  is `gcp-api-key`, matching the unrelated `AIza...` API-key format, not
  OAuth client secrets or connection strings). **Demonstrated blind spot
  #2: gitleaks' default rules have no detector at all for a plaintext
  password embedded in a `scheme://user:password@host` credential
  string** — exactly this repo's own `DATABASE_URL` shape
  (`app/utils/config.py`'s `DATABASE_URL: str`).

**Mechanism:** two small, additive, pattern-only custom rules in
`.gitleaks.toml` (not a manual grep step — the intent's own steer):

- `connection-string-credential`: a regex matching
  `scheme://user:password@host` for the schemes this repo's own secrets
  actually use (`postgres`/`postgresql`, `mysql`, `mongodb`/`mongodb+srv`,
  `redis`, `amqp`/`amqps`). Pattern-only, no keyword dependency, so a
  `name`/`value` line split can't defeat it — the whole URI, credential
  included, is one contiguous string wherever it appears in a file.
- `google-oauth-client-secret`: a regex matching Google's `GOCSPX-`
  prefix format (a scanner-friendly prefix Google added specifically so
  tools like this can recognize it context-free). Also pattern-only.
- A Microsoft/Azure-AD client-secret rule was *considered* (the leaked
  value had a `~`-containing shape) but is **not** proposed with the same
  confidence: Microsoft
  hasn't published as fixed/public a format guarantee as Google's
  `GOCSPX-` prefix, so a regex here risks either missing real secrets or
  false-positiving on unrelated strings. Flagged as a followup, not
  force-added on a guess — consistent with the intent's steer against
  assuming a gap.
- New test, `tests/test_gitleaks_rules.py`: loads `.gitleaks.toml` with
  the stdlib `tomllib` (Python 3.11, already the pinned runtime), extracts
  each new rule's `regex`, and — using Python's `re`, never invoking the
  gitleaks binary or committing a real secret — asserts each pattern
  matches a synthetic fixture shaped like the incident (e.g.
  `postgresql://user:REDACTEDFORTEST1234@host:5432/db`, a same-length
  synthetic `GOCSPX-...` string) and does *not* match benign strings (a
  bare `https://` URL with no credentials, the existing
  `.gitleaks.toml` allowlist placeholders). This is the real,
  Test-runnable verification that the fix works, without the danger of
  testing it against an actual secret.

**Alternatives considered:**
- *A mandatory pre-commit manual grep step, parallel to gitleaks.*
  Rejected per the intent's explicit constraint: it would be ceremony
  next to a gate that already runs on every commit and CI push, and
  wouldn't close either demonstrated gap (a grep step is exactly as
  vulnerable to the line-split and keyword-absence problems above unless
  it *is* essentially a gitleaks rule, in which case put it there).
- *Declare gitleaks adequate, do nothing.* Rejected — two gaps above are
  demonstrated by regex tracing against gitleaks' own real default
  config and this repo's own real incident, not asserted.
- *Rewrite/replace the whole default ruleset.* Rejected as
  disproportionate; two targeted additive rules close the named gap
  without touching a ruleset that otherwise works.

### 3. Data-accuracy gate for the rule engine and change-request decision

Verified: `tests/test_rule_engine.py` (23 test methods across 4 classes)
already locks every `ReasonCode`, both cancellation branches, and the
alternatives behavior at the pure-engine layer. `tests/test_change_requests.py`
(815 lines, ~35 test methods) separately covers `ChangeRequestService`'s
HTTP-facing scenarios (`TestAutoApply`, `TestParkedForParent`,
`TestParentDecides`, `TestAuthorisation`, `TestParentInitiated`, ...) —
real coverage, but none of it is framed as an invariant a future change
must not silently flip, and none of it isolates the orchestration layer's
own approve/park decision (`ChangeRequestService.submit()` translating an
`Evaluation` into `auto_applied` / `ApprovalStatus` / `applied_to_calendar`)
the way `test_rule_engine.py` isolates the engine's decision. Two
additive pieces, both using tooling already in `requirements.txt`
(`pytest-cov`) — no new tool:

- **A file-scoped coverage floor**, added as a step in the existing
  `test` job of `.github/workflows/ci-cd.yml` (after the main test run,
  same job, no new job/setup needed):
  ```
  pytest tests/test_rule_engine.py tests/test_change_requests.py \
    --cov=app.services.rule_engine --cov=app.services.change_request_service \
    --cov-report=term-missing --cov-fail-under=<N>
  ```
  `--cov=<module>` restricts *measured* source to just these two files,
  so `--cov-fail-under` becomes a real per-file gate instead of today's
  whole-repo aggregate (`--cov=app`), which the intent correctly notes
  can't fail over a drop isolated to one file. `<N>` must be Build's
  actual measured number for these two files today (run the command and
  read it off), not a guessed round figure that already fails.
- **A named "golden outcomes" test class** — new
  `tests/test_change_request_decisions.py` (or a new class inside
  `tests/test_change_requests.py`; Build's call), reusing the existing
  `family`/`rules`/`session_row`/`db_session` fixtures from
  `tests/conftest.py`, calling `ChangeRequestService.submit()` directly
  (bypassing the HTTP client, matching how `test_rule_engine.py` calls
  the engine directly) across one case per `ReasonCode` plus both
  cancellation branches. Each case asserts the *orchestration* outcome —
  `ChangeOutcome.auto_applied`, the resulting `ApprovalRequest.status`
  (`APPROVED` vs `PENDING`), and `applied_to_calendar` — not just the
  engine's `Evaluation`, which `test_rule_engine.py` already locks. The
  class/module docstring frames it explicitly: *"Golden outcomes: change
  an assertion here only alongside a deliberate, reviewed decision to
  change what auto-applies vs. what needs a parent — never to make a
  failing test pass."*

**Alternatives considered:**
- *Raise `.coveragerc`'s global `fail_under`.* Rejected — whole-repo
  aggregate, so it can't isolate a drop to these two files, and raising
  it repo-wide would fail today against unrelated, lower-covered code.
- *Force-fit the pricing repo's `confirmed_pct`/`stale_models` metric.*
  Rejected per the intent's explicit constraint — no equivalent
  "confirmed" or "staleness" concept exists for schedule rules.
- *Coverage floor only, no golden-outcomes class.* Rejected — a coverage
  floor doesn't catch a logic mistake that keeps the same lines exercised
  but returns the wrong `auto_applied`/status; only an outcome-asserting
  test does, and the intent's success bar is explicitly "would have
  failed loudly had a real rule-engine regression shipped."
- *Golden-outcomes class only, no coverage floor.* Rejected — doesn't
  close the intent's specifically-named CI-aggregation gap.

### 4. A parent-readable changelog surface — the lighter option, with the reasoning made explicit

New file, `docs/WHATS_NEW.md`: one entry per user-visible release,
written in plain language a parent could read (no file paths, endpoint
names, or internal service names — unlike `CHANGELOG.md`'s `1.1.0` entry,
which cites all three throughout). Updated in the same PR as
`CHANGELOG.md` whenever a change is user-visible, per the same
"Before committing" checklist addition as item 1. No new route, no new
template, no new locale keys.

**Why not the rendered in-app page** (the heavier option the intent asked
Design to explicitly weigh, not default past): this app's own
established, repo-wide convention — grepped in
`app/services/change_request_service.py` (`text_key`/`meta_key` +
`params`, e.g. `"parent.log_moved"`) and `app/static/mew/mew.js`'s `t()`
helper — is that *no* user-facing string in the three-persona UI is ever
hardcoded English; everything resolves through `app/locales/{en,es,hi,ar}.json`,
checked by `tests/test_locales.py`. A rendered "what's new" page holding
freeform, frequently-changing release-note prose would either violate
that established convention outright (raw English mixed into an
otherwise strictly locale-driven UI) or require every release note to
become new keys in all four locale files — including `hi` and `ar`,
which `app/locales/README.md` already flags as unreviewed
machine-quality translations needing a native speaker before shipping.
That's a real, compounding, ongoing translation cost for an app that has
not publicly launched — exactly what the intent's constraint says not to
default into. A markdown file sidesteps it entirely, matching this
repo's existing precedent for other English-only docs
(`docs/THREE_PERSONA_SCHEDULING.md`, `docs/GETTING_STARTED.md`).

**Alternatives considered:**
- *In-app rendered page.* Rejected for the reasons above.
- *Do nothing, `CHANGELOG.md` is enough.* Rejected — the intent's success
  bar wants something "a parent, not just a developer, could read," and
  today's `CHANGELOG.md` doesn't clear that bar for any entry checked.
- *Add a parent-readable section at the top of `CHANGELOG.md` itself
  instead of a separate file.* Rejected — mixing audiences in one file
  means either the engineering detail crowds out the parent-readable
  summary or vice versa; a second, small, purpose-built file keeps both
  legible for their own reader at negligible extra authoring cost (one
  more short paragraph per release, written alongside the existing
  entry).

### 5. Architecture doc + trigger-list

New `docs/ARCHITECTURE.md`, describing the app as `align-docs-with-current-app`
(PR #152) left it — WorkOS sign-in, Fly.io deployment, three-persona
scheduling — never resurrecting the pre-#152 Azure/Container-Apps
material that pass removed (the very shape of file this cycle's own
gitleaks incident came from). Proposed table of contents, grounded in the
actual code (not a generic template):

1. **Overview** — one paragraph: a deterministic rule-engine scheduling
   assistant for three personas (parent/kid/provider), not a chatbot;
   points to `docs/THREE_PERSONA_SCHEDULING.md` for the request/approval
   loop in depth rather than re-explaining it.
2. **Request lifecycle** — one diagram: persona → FastAPI router →
   `ChangeRequestService.submit()` → `RuleEngine.evaluate()` → DB write →
   calendar write-back (best-effort) → notification. Cross-references
   `docs/THREE_PERSONA_SCHEDULING.md`'s existing loop diagram instead of
   duplicating it.
3. **Router layer map** (`app/routers/`, 24 files, grouped by concern,
   one line each — the thing the intent notes no doc covers today):
   - Sign-in & auth: `auth.py`, `oauth_workos.py`, `oauth_success_page.py`
   - The scheduling loop: `requests.py` (`change_requests_router`),
     `rules.py`, `parent_approval.py` (both its routers), `kid_friendly.py`,
     `provider.py`, `smart_approval.py`
   - Calendar: `calendar.py`, `calendar_web.py`, `calendar_oauth.py`,
     `calendar_sync.py`, `kid_calendar_oauth.py`
   - Voice: `voice.py`, `voice_requests.py`, `voice_platforms.py`
   - Setup & onboarding: `onboarding_setup.py`, `session.py`
   - Cross-cutting / other: `mew_ui.py`, `mobile.py`, `message.py`,
     `summary.py`, `notifications.py`, `webhooks.py`, `ai_scheduler.py`,
     `landing.py`, `debug_page.py`
4. **Data model** (`app/database/models.py`, ~38 model/enum classes) —
   grouped by domain, not an exhaustive field list: identity (`User`,
   `FederatedIdentity`, `UserRole`), scheduling (`ScheduledSession`,
   `RuleSet`, `ProtectedBlock`, `WeeklyCap`, `ApprovalRequest`,
   `ApprovalAuditLog`, `ChangeLogEntry`), providers
   (`ProviderOrg`, `ProviderPerson`, `ProviderOrgConnection`),
   calendar (`KidCalendarConnection`, `OAuthProvider`), notifications
   (`Notification`, `NotificationKind`), locale (`UserLocale`) — and an
   explicit callout that some models (`Family`, `ApprovalRule`,
   `ScheduleEntry`, `UserProfile`) predate the three-persona model and
   should be confirmed live-vs-legacy before being documented as current.
5. **Services layer** (`app/services/`, 23 files) — one line each,
   grouped the same way as the router map, with `rule_engine.py` and
   `change_request_service.py` called out as the one write path
   (`docs/THREE_PERSONA_SCHEDULING.md` already covers these in depth;
   link, don't duplicate).
6. **Deployment topology** — Fly.io (`fly.toml`, `Procfile`,
   `Dockerfile`), the CI/CD gates already described in `CLAUDE.md`
   (link, don't duplicate), and an explicit note that
   `infrastructure/azure/` and root `*.bicep` files are dormant
   legacy, not live topology — the same distinction the intent's own
   gitleaks-incident investigation had to make manually.
7. **Trigger-list** (the actual ask of item 5) — appended either as
   `docs/ARCHITECTURE.md`'s own closing section or to `CLAUDE.md`
   (Build's call on placement, not Design's): *"Update
   `docs/ARCHITECTURE.md` when: a new router file is added to
   `app/routers/`; a new table/model is added to
   `app/database/models.py`; a new service is added to
   `app/services/`; deployment topology changes (`fly.toml`,
   `Dockerfile`, `Procfile`); a new external integration is added
   (new OAuth provider, new calendar source, new
   notification channel)."*

**Alternatives considered:**
- *Retrofit `docs/THREE_PERSONA_SCHEDULING.md` into the whole-app doc.*
  Rejected — it documents one feature domain in real depth
  intentionally; stretching it to cover the router layer, the full data
  model, and deployment topology would either dilute its current
  usefulness or produce a doc that's neither a good feature reference
  nor a good architecture reference.
- *Point the trigger-list at "no doc, update `docs/README.md`'s
  structure diagram instead."* Considered and rejected — the intent's
  own success bar requires either a real, accurate architecture doc or
  an explicit list of doc(s) that already play that role; nothing in
  this repo already plays it (verified: `docs/README.md`'s "Documentation
  Structure" section is a file listing, not an architecture description).

## Affected files

- `app/utils/config.py` — no field changes (`APP_VERSION` already
  exists); comment/no-op unless Build finds a reason to touch it.
- `app/main.py` — `FastAPI(version=...)` reads `settings.APP_VERSION`;
  `GET /version` returns `settings.APP_VERSION` instead of the hardcoded
  `landing-page-v2` stub.
- `tests/test_version.py` — new. Locks `/version` and `CHANGELOG.md`'s
  top entry against `settings.APP_VERSION`.
- `.gitleaks.toml` — two new `[[rules]]`: `connection-string-credential`,
  `google-oauth-client-secret`; brief comment recording what investigation
  produced them (so a future reader doesn't have to re-derive it).
- `tests/test_gitleaks_rules.py` — new. Verifies the two new regexes
  against synthetic fixtures (match) and benign strings (no match), via
  `tomllib` + `re`, no gitleaks binary invocation.
- `.github/workflows/ci-cd.yml` — new step in the existing `test` job:
  file-scoped coverage floor over `app/services/rule_engine.py` and
  `app/services/change_request_service.py`.
- `tests/test_change_request_decisions.py` (new) or a new class inside
  `tests/test_change_requests.py` (Build's call) — golden-outcomes
  regression lock over `ChangeRequestService.submit()`'s approve/park
  decision.
- `docs/WHATS_NEW.md` — new. Parent-readable release notes, first entry
  covering whatever's already unreleased plus a backfilled note for
  `1.1.0` so it isn't empty on day one.
- `docs/ARCHITECTURE.md` — new, per the table of contents above.
- `docs/README.md`, `DOCUMENTATION_INDEX.md` — add `docs/ARCHITECTURE.md`
  and `docs/WHATS_NEW.md` to their existing tables/lists (same pattern
  `align-docs-with-current-app` used for other docs).
- `CLAUDE.md` — "Before committing" gains: the version-bump-and-tag line
  (item 1), the `docs/WHATS_NEW.md` companion-update line (item 4), and
  a "Documentation" (or similar) section carrying the
  `docs/ARCHITECTURE.md` trigger-list (item 5). Exact section placement
  and final wording are Build's to finalize; this spec fixes the
  substance.
- `CHANGELOG.md` — a `[1.1.0]`-adjacent or `[Unreleased]` note pointing
  at this cycle's own checklist additions, consistent with existing
  entries citing the features that introduced them.

## Data / API / UI changes

- **No database schema change** — nothing here touches
  `app/database/models.py`; no migration needed.
- **`GET /version`** (`app/main.py`) — response body changes from the
  hardcoded stub to `{"version": settings.APP_VERSION, "deployed": ...}`.
  No auth change (this endpoint is unauthenticated today and stays
  that way — it carries no family-scoped or otherwise sensitive data).
- **No new endpoints.** Item 4 is a static doc, not a route; item 5 is
  documentation only.
- **No UI changes, no new locale keys.** Item 4's explicit design
  decision (see above) is to not touch the rendered UI or
  `app/locales/*.json`, so `tests/test_locales.py`'s four-file contract
  is unaffected by this feature.

## Edge cases

- **A PR bumps `APP_VERSION` but not `CHANGELOG.md` (or vice versa).**
  `tests/test_version.py` fails CI in either direction — that's the
  point of locking them together.
- **`CHANGELOG.md`'s top entry is `[Unreleased]` with no version yet.**
  The parser in `tests/test_version.py` must skip `[Unreleased]` and
  find the first *versioned* heading beneath it, not treat
  `[Unreleased]` itself as a version string to compare.
- **The new `.gitleaks.toml` rules produce false positives on this
  repo's own legitimate content** — e.g. a doc showing an example
  connection string, or a test fixture already using a
  `postgresql://user:pass@host` placeholder. Both new rules must be
  checked against the existing `[allowlist]` paths/regexes
  (`docs/GETTING_STARTED.md`, `docs/FEDERATED_AUTH_GUIDE.md`,
  `DEPLOYMENT_SUMMARY.md`, and `tests/` fixtures using synthetic
  connection strings) before landing, and the allowlist extended if
  Build finds a real false positive — not discovered for the first time
  when CI's `secret_scan` job blocks an unrelated PR.
- **A real secret slips into a PR that also happens to touch
  `.gitleaks.toml`.** No special handling needed — gitleaks still scans
  the whole diff regardless of which file changed; this item only adds
  detection surface, never narrows it.
- **The coverage-floor step's threshold (`<N>`) is set too tight and
  starts failing on unrelated, legitimate refactors** (e.g. dead-code
  removal that drops a line coverage.py was crediting). Build sets `<N>`
  from a real measured run, with a small margin below today's number,
  not the number itself, so a single incidental line move doesn't break
  unrelated PRs.
- **The golden-outcomes test class is edited to make a red test green
  without a real product decision.** The class/module docstring exists
  precisely to make this the wrong instinct visible to a reviewer; this
  is a process safeguard, not something CI itself can block (a human
  reviewer must actually read the diff to the test, same as any other
  test change).
- **`docs/WHATS_NEW.md` drifts from `CHANGELOG.md`** (one updated, the
  other forgotten) the same way `APP_VERSION` drifted from
  `CHANGELOG.md` before this cycle. No automated lock is proposed here
  (unlike item 1) because `docs/WHATS_NEW.md`'s content is prose, not a
  single comparable value — this is accepted as a process risk covered
  by the `CLAUDE.md` checklist line, not a test.
- **`docs/ARCHITECTURE.md` goes stale the same way
  `docs/THREE_PERSONA_SCHEDULING.md` was asked to stand in for a doc it
  wasn't scoped to be.** The trigger-list is the mitigation; like the
  changelog pairing above, this is a checklist discipline, not an
  automated gate — enforcing "was the architecture doc updated" in CI
  would require detecting semantic router/model/service additions,
  which is out of proportion for this cycle.

## Acceptance criteria

1. `GET /version` returns `settings.APP_VERSION`'s current value, not
   `landing-page-v2`; `FastAPI(version=...)` matches it; `tests/test_version.py`
   passes and demonstrably fails if either value diverges from
   `CHANGELOG.md`'s top versioned entry (verify by temporarily bumping
   one without the other in a scratch commit).
2. `.gitleaks.toml`'s two new rules exist and `tests/test_gitleaks_rules.py`
   passes: each new regex matches its incident-shaped synthetic fixture
   and does not match the existing allowlist placeholders or a benign
   credential-free URL.
3. The `test` job in `.github/workflows/ci-cd.yml` includes the new
   file-scoped coverage-floor step for `rule_engine.py` and
   `change_request_service.py`, and CI fails if either file's coverage
   drops below the recorded floor (verify by temporarily commenting out
   one branch's test and confirming only this step, not the whole-repo
   `--cov=app` step, is what catches it).
4. A new golden-outcomes test class exists covering
   `ChangeRequestService.submit()`'s approve/park decision for every
   `ReasonCode` and both cancellation branches, explicitly documented as
   a regression lock; verify by inverting one branch's expected
   `auto_applied`/status in `change_request_service.py` and confirming
   this class (not just `test_rule_engine.py`) is what fails.
5. `docs/WHATS_NEW.md` exists, contains at least one entry a parent could
   read without needing to know what a router or a service is (no file
   paths, endpoint names, or internal class names), and is listed in
   `docs/README.md`/`DOCUMENTATION_INDEX.md`.
6. `docs/ARCHITECTURE.md` exists, matches the table of contents above,
   accurately describes the WorkOS/Fly.io/three-persona app (no
   pre-#152 Azure Container Apps material presented as current), and its
   trigger-list is findable from `CLAUDE.md` or the doc itself.
7. `pytest tests/` and `flake8 app tests` both still pass with all of the
   above in place (existing "Before committing" gate, unaffected in
   substance by this change).
8. `tests/test_locales.py` still passes unmodified — confirms item 4 did
   not add any UI-facing string, keeping the four-locale contract
   untouched as designed.

## Out of scope

- Fixing `/version`'s stale response as a standalone bug independent of
  this mechanism — restated from the intent; it's fixed *as* the
  version-bump mechanism's direct consequence, not as a separate task.
- Rewriting or replacing gitleaks as a tool, or auditing its coverage of
  anything beyond this repo's own actual incident shape — restated from
  the intent's constraint.
- A Microsoft/Azure-AD client-secret detection rule — considered, not
  proposed, for lack of a confirmed, fixed public format to regex
  against; a real followup once a genuine example format is confirmed,
  not a guess landed now.
- Any change to `app/database/models.py` or a new migration — none of
  the five mechanisms need one.
- A rendered in-app "what's new" page, or any new locale keys — the
  explicit, reasoned Design decision for item 4 (see above); deferred,
  not forgotten, if the app's audience/localization posture changes
  post-launch.
- Automated enforcement that `docs/ARCHITECTURE.md` or
  `docs/WHATS_NEW.md` was actually updated when its trigger fires — both
  are checklist disciplines for `CLAUDE.md`, not CI gates, per the Edge
  Cases section; building a semantic "did the architecture change"
  detector is out of proportion for this cycle.
- Retagging or backfilling git tags for versions prior to this change —
  the existing `v0.2.0`–`v1.1.0` tag history is left as-is; the new
  discipline applies going forward.
- Producing `CLAUDE.md`'s exact final section placement/wording — this
  spec fixes the substance of each checklist addition; Build finalizes
  phrasing and placement within `CLAUDE.md`'s existing structure.
