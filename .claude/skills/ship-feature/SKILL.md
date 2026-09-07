---
name: ship-feature
description: Orchestrator for this repo's AI-native SDLC. Walks a feature or bug fix through Plan -> Design -> Build -> Test -> Deploy -> Maintain in this conversation, dispatching a dedicated agent per phase and stopping at every human gate. Use when the user asks to "ship", "build and release", "take through the SDLC", or run /ship-feature on a feature request, bug report, or dogfooding finding.
---

# ship-feature: the AI-native SDLC orchestrator

This skill is the orchestrator. It does not do the phase work itself - it
dispatches one of six agents (`sdlc-plan`, `sdlc-design`, `sdlc-build`,
`sdlc-test`, `sdlc-deploy`, `sdlc-maintain`, all in `.claude/agents/`) per
phase, and its own job is entirely about the handoffs between them: what
gets shown to the human, and where the loop must stop and wait.

Background and rationale for this whole model: root `CLAUDE.md`'s
"AI-native SDLC" section. Read it once if this is your first time running
this skill in a session.

## The loop

```
Plan → Design → Build → Test → Deploy → (dogfooding happens) → Maintain → back to Plan
```

Six phases, one artifact chain per feature, committed to
`docs/features/<slug>/`: `intent.md` (Plan) → `spec.md` (Design) →
`plan.md` (Build, written before any code) → the diff itself (still Build)
→ a verification report (Test, not committed - it's this conversation's
output) → a merged PR on `develop` (Deploy). Maintain runs later, when
feedback about the shipped feature comes back, and produces the *next*
`intent.md` - closing the loop rather than chaining immediately after
Deploy.

## How to run it

You're given a starting point: a feature request, a bug report, a
dogfooding observation, or (from Maintain) a diagnosis. Determine which
phase that starting point belongs to - most of the time this is Plan, but
if the human hands you an already-written intent.md and says "design
this," start at Design instead. Don't force every invocation through all
six phases if the human clearly wants to resume partway through.

For each phase, in order:

1. **Dispatch the phase's agent** via the Agent tool, `subagent_type` set
   to that phase's name (e.g. `sdlc-plan`), **`run_in_background: false`**
   - the next step always depends on this phase's result, so there's
   nothing to gain from backgrounding it and it would break the gate.
   Write a self-contained prompt: the agent has no memory of this
   conversation, so include the raw request (for Plan/Maintain), or the
   prior artifact's full content and file path (for Design/Build/Test/
   Deploy) directly in the prompt rather than saying "see above."

2. **Show the human what came back.** Not a paraphrase - the actual
   `intent.md`/`spec.md`/`plan.md` content (or, for Test, the verification
   report; for Deploy, the PR link and CI state). This is the whole point
   of committing a version-controlled Markdown artifact at every stage:
   the human is approving a real document, not the model's a summary of
   one.

3. **Stop and ask before advancing.** Plain conversation is fine for this
   - it doesn't have to be `AskUserQuestion` every time - but the
   conversation must not silently move to the next phase. Accept
   "looks good, continue" as clearance. If the human asks for a revision,
   re-dispatch the *same* phase's agent with the revision request folded
   into the prompt, don't skip ahead with a patched version yourself.

4. Only after clearance, dispatch the next phase.

## The gates, explicitly

| Handoff | What the human is approving |
|---|---|
| Plan → Design | The problem is real and worth solving as scoped - not yet how |
| Design → Build | The concrete design, affected files, and acceptance criteria |
| Build → Test | The implementation and its own self-run checks are worth independent verification |
| Test → Deploy | Verification passed (or a known, accepted gap) - safe to open a PR |
| Deploy → `develop` merge | Deploy phase merges once CI is green - this one doesn't need a fresh chat gate beyond "PR looks right," since it mirrors this repo's existing PR-driving rules |
| `develop` → `master` (production) | **Never automatic.** This is the actual production gate - `master` auto-deploys to Fly.io. Only proceed on an explicit instruction in this same conversation, exactly as `sdlc-deploy`'s own instructions require. A prior "go ahead and ship this" does not cover this gate - production promotion needs its own explicit word. |

## Starting a fresh cycle vs. resuming

- New request, nothing written yet → start at Plan.
- Human hands you an intent.md/spec.md directly and says "run design/build
  from this" → skip straight to that phase, using the given file as the
  prior artifact.
- Human reports something wrong with an already-shipped feature → that's
  Maintain, not a bug fix you jump straight into. Run Maintain first; its
  output intent.md is what starts the next full cycle, with its own Design
  and Build gates, even if the fix looks obvious.

## Worked example

`docs/features/parent-week-edit/` holds a real intent.md/spec.md/plan.md
for a feature shipped in this repo before this skill existed, written
retroactively as a reference for what "right-sized" looks like at each
phase - read it once if a phase's expected depth is unclear.
