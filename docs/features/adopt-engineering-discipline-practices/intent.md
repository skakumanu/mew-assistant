# Intent: adopt five engineering-discipline practices from `llm-pricing-mcp-server`

## Problem

The repo owner maintains a sibling repo, `skakumanu/llm-pricing-mcp-server`,
whose `CLAUDE.md` carries five mandatory pre-commit-checklist practices
that mew-assistant's own `CLAUDE.md`/SDLC has none of today. Each is
evaluated below against mew-assistant's actual current state, not the
pricing repo's framing.

**1. Semantic version bumping.** mew-assistant already has version-shaped
state, and it already disagrees with itself:
- `app/utils/config.py` declares `APP_VERSION: str = "1.0.0"` on the
  `Settings` model, but a repo-wide grep shows nothing ever reads
  `settings.APP_VERSION` — it is dead configuration, never bumped, never
  rendered anywhere.
- `CHANGELOG.md`'s most recent entry is `[1.1.0] - August 24, 2026`.
- `app/main.py` serves a live `GET /version` endpoint today, but it
  returns a hardcoded, unrelated value —
  `{"version": "landing-page-v2", "deployed": "2025-11-28T02:00:00Z"}` —
  a leftover from a prior (pre-three-persona, Azure-era) build of this
  app, per `docs/features/align-docs-with-current-app/intent.md`'s
  findings.

So there are three live "version" signals in this repo right now — an
unused `1.0.0` default, a changelog claiming `1.1.0`, and an actually-served
endpoint claiming `landing-page-v2` dated November 2025 — and they agree
with nothing, including each other. This isn't a hypothetical gap the
pricing repo's practice would prevent; it's a gap that already exists and
is already visible to anyone who hits `/version`. There is no MCP
`serverInfo` field or equivalent here, and no other consumer of a version
string today — unlike the pricing repo, adopting this practice doesn't
plug into an existing integration, it establishes one.

**2. A mandatory pre-commit secret-scan grep.** mew-assistant already runs
`gitleaks` as both a local pre-commit hook (`.pre-commit-config.yaml`) and
a CI job (`secret_scan` in `.github/workflows/ci-cd.yml`), and this is not
theoretical: a real incident this session (a Postgres password and OAuth
client secrets committed in a stray Azure config dump) was found via a
live GitGuardian alert and required deleting the file and rewriting git
history with `git-filter-repo`. `.gitleaks.toml` currently carries zero
repo-specific rules — only an allowlist for known documentation
placeholders — meaning detection today is entirely gitleaks' out-of-the-box
ruleset. Whether that ruleset would have caught the specific incident
above (a plaintext password/secret embedded in an infra config dump,
rather than a recognizably-shaped API key or token) is not established
either way from what's in the repo; nothing here indicates gitleaks was
bypassed, disabled, or predated the incident, but nothing confirms its
default rules cover this shape of leak either. Treating "add a redundant
manual grep" as self-evidently additive would be adding ceremony next to
a gate that already exists and already runs on every commit and every CI
run; the honest problem to hand to Design is narrower: verify whether
today's gitleaks configuration has a demonstrable blind spot for this
repo's own incident shape, and if so close *that* gap (which may mean a
`.gitleaks.toml` rule addition, not a second manual grep step at all) —
not to assume a gap and bolt on parallel tooling regardless.

**3. A domain-specific "data accuracy" gate.** This app's closest analog
to the pricing repo's pricing-data correctness is the deterministic
`RuleEngine` (`app/services/rule_engine.py`) and the orchestration layer
around it (`app/services/change_request_service.py`) that decides whether
a kid's or provider's schedule-change request auto-applies or is parked
for parent approval. A regression here is not cosmetic: a family could
have a change silently auto-applied that should have needed approval, or
vice versa. This is meaningfully less bare than it first looks —
`tests/test_rule_engine.py` already locks 28 cases across every
`ReasonCode`, both cancellation paths, and the three-alternatives
behavior, and `CHANGELOG.md`'s `1.1.0` entry claims the rule engine
shipped "100% covered." `tests/test_change_requests.py` covers the
orchestration layer separately. What's genuinely missing is a *gate*, not
a *test suite*: nothing in CI enforces that `rule_engine.py`'s coverage
stays at its current level specifically (the `test` job's
`--cov=app` is whole-repo aggregate; a change elsewhere in the app cannot
fail CI over a coverage drop isolated to this one file), and there is no
fixed, named set of approval-decision outcomes that a future change must
never flip silently (today's 28 tests exist, but nothing frames them as
that kind of invariant, and there's no equivalent discipline yet extended
to `change_request_service.py`'s approve/park decision itself, only to
the engine it calls).

**4. A user-facing changelog/"what's new" page.** mew-assistant has no
such page today. `CHANGELOG.md` exists but is a developer-facing file at
repo root, written for engineers reading diffs (e.g. its `1.1.0` entry
cites file paths, endpoint names, and internal service names throughout)
— not something a parent using `/app/parent` would ever see or read. The
app's UI (`app/templates/mew/`) has no "what's new" surface for any of
the three personas. Parents are the realistic audience for such a page
(kids and providers have narrower, task-focused UI with less standing
reason to check back for changes), but there's no existing precedent in
this app's UI structure to extend, and no evidence yet that user-visible
releases are frequent or externally-facing enough (the app is not
publicly launched) to justify an in-app rendered page's ongoing
maintenance burden versus a much smaller step in that direction.

**5. An explicit trigger-list for updating an architecture doc.**
mew-assistant has no `docs/ARCHITECTURE.md` today. The prior docs pass
(`docs/features/align-docs-with-current-app/intent.md`, PR #152)
rewrote `README.md`, `DOCUMENTATION_INDEX.md`, and `docs/README.md` to
match the current app but explicitly scoped out "producing a brand-new
... architecture doc ... from scratch" as a non-goal — so this gap is
known, not newly discovered. The closest existing doc,
`docs/THREE_PERSONA_SCHEDULING.md`, documents one feature domain (the
request/approval loop, its code map, its data model) in detail but says
nothing about the router layer as a whole, the full set of database
tables outside the scheduling ones, calendar sync's place in the system,
or deployment topology — it isn't, and doesn't claim to be, a whole-app
architecture reference. Without either a real architecture doc or an
explicit list of doc(s) that already play that role well enough, there is
no anchor for a trigger-list like the pricing repo's ("new service, new
endpoint group, new DB table, new UI page..." requires an update) to even
point at.

## Why now

All five gaps above are ones the owner asked to close in this cycle, and
for at least two of them (version drift, the missing architecture-doc
anchor) this investigation surfaced they're not just absent but already
producing live inconsistency (`/version`'s stale hardcoded response;
`docs/THREE_PERSONA_SCHEDULING.md` being asked to stand in for an
architecture doc it was never scoped to be). Closing them now, while the
SDLC's own artifact chain (this Plan → Design → Build loop) is being
exercised on the practices that govern that same chain, means the
resulting checklist additions to `CLAUDE.md` land through the same
discipline they're meant to enforce going forward.

## Constraints

- This is a `CLAUDE.md`/SDLC and process change, not a product feature —
  it should not require its own feature flag or user-facing rollout.
- Item 2 must not duplicate `gitleaks` coverage without a demonstrated,
  specific gap; Design must show its work on what, if anything, gitleaks'
  current configuration misses before proposing an additional check.
- Item 3 must not force-fit the pricing repo's `confirmed_pct`/
  `stale_models`-shaped metric onto a codebase with no equivalent concept;
  whatever gate is proposed must be a real, checkable invariant against
  `rule_engine.py` and/or `change_request_service.py` as they actually
  exist, not a renamed copy of the pricing repo's mechanism.
- Item 4, if pursued, should have a maintenance cost proportionate to an
  app that has not yet publicly launched — Design should weigh a plain
  `CHANGELOG.md`-adjacent file against a rendered in-app page rather than
  defaulting to the heavier option because the pricing repo did it that
  way.
- Item 5's trigger-list, if it points at a new `docs/ARCHITECTURE.md`,
  must describe the app as `align-docs-with-current-app` left it (WorkOS
  sign-in, Fly.io deployment, three-persona scheduling) — not resurrect
  any of the stale pre-#152 material that pass removed or flagged.

## Non-goals

- Deciding the exact file each practice's state lives in (e.g. where a
  version constant is declared, what a "data accuracy" gate's test file
  is named, whether item 4 is a route or a markdown file, what
  `docs/ARCHITECTURE.md`'s table of contents is) — that's Design's call
  once this problem framing is accepted.
- Writing or modifying any code, test, CI config, or doc outside this
  `intent.md` — including not touching `.pre-commit-config.yaml`,
  `.github/workflows/ci-cd.yml`, `app/utils/config.py`, `app/main.py`'s
  `/version` route, or `CLAUDE.md` itself in this phase.
- Fixing `/version`'s currently-stale hardcoded response as a standalone
  bug — it's cited above as evidence the version-drift problem is real
  and present-tense, not as a bug-fix request in its own right; whether
  the eventual version-bumping practice touches that endpoint is a Design
  decision.
- Re-litigating whether `gitleaks` itself is adequate as a secret-scanning
  tool choice — only whether a *second*, manual, pre-`git add` check is
  additive on top of it.
- Producing the five checklist items' final wording for `CLAUDE.md` — Plan
  establishes the problem each solves for this repo; Design proposes the
  concrete mechanism and wording.

## Success looks like

Design receives, for each of the five practices, either (a) a concrete
mechanism scoped to a real gap identified above, or (b) an explicit,
argued "this doesn't apply here as originally shaped" — never a
practice adopted by rote because the sibling repo has it. Concretely:
`CLAUDE.md` eventually gains version-bump guidance that resolves the
three-way version disagreement found above rather than adding a fourth
disagreeing source; the secret-scan question is answered with either a
named, verified gitleaks blind spot or an explicit decision not to add a
redundant step; the data-accuracy gate is a real, running check against
`rule_engine.py`/`change_request_service.py` (e.g. a coverage floor or a
locked outcome set) that would have failed loudly had a real rule-engine
regression shipped; a changelog surface (in whatever form Design picks)
exists that a parent, not just a developer, could read and learn
something from; and either `docs/ARCHITECTURE.md` exists and is accurate
to the current app, or the trigger-list explicitly names which existing
doc(s) serve that role instead — never left pointing at nothing.
