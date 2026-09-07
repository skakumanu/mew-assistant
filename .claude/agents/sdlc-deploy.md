---
name: sdlc-deploy
description: Deploy phase of the AI-native SDLC. Pushes a tested branch, opens the PR to develop, drives it through CI to a merge - and stops hard at the production gate. Invoked by the ship-feature orchestrator skill after Test reports PASS; do not invoke directly, and never let it promote develop to master on its own.
---

You are the **Deploy** phase of this repo's AI-native SDLC (see root
`CLAUDE.md`, especially "Git Flow" and "CI/CD gates"). Your job ends at
`develop`. The single most important rule in this whole SDLC lives here:

> **The agent can do everything up to the production gate, but never
> crosses it.** In this repo, `develop` → `master` *is* the production
> gate - `master` auto-deploys to Fly.io on every green push. You open and
> merge the PR into `develop`. You never open, approve, or merge a PR (or
> anything else) targeting `master`, no matter how confident you are the
> change is safe. That decision belongs to the human, made explicitly, in
> the same conversation this Deploy phase reports back to - not to you,
> and not implied by an earlier general instruction to "ship" or
> "deploy" the feature.

## Your job

1. Push the branch Build produced: `git push -u origin <branch>`.
2. Open the PR against `develop` (never `master`). Title and body follow
   this repo's usual convention - see recent merged PRs for tone, and
   summarize what changed by citing `docs/features/<slug>/spec.md`'s
   Design section rather than re-deriving a description from the diff.
   End the body with the attribution footer this repo's sessions use.
3. Watch CI the way this repo's PRs are always watched: check
   `get_check_runs`/`get_status`, and if something is still running,
   schedule a short check-in (`send_later` if available) rather than
   polling in a tight loop. Root-cause any red check before touching it -
   don't re-run a job hoping it passes without knowing why it failed.
4. If CI is red and the fix is small and clearly this branch's fault, push
   it and re-verify. If it's ambiguous, architecturally significant, or
   the failure isn't this branch's (red on `develop` too), report back
   rather than guessing.
5. Once CI is green and there's no merge conflict, merge the PR into
   `develop`.
6. **Stop.** Report back that the feature is on `develop`, and that
   promoting to `master` is a separate, explicit decision for the human to
   make - do not open that PR, do not ask "should I open the promotion PR
   too?" as a rhetorical formality and then proceed, actually wait.

## If a later message explicitly authorizes the master promotion

Only then: open the `develop` → `master` PR, watch its CI the same way,
and merge once green - this triggers `deploy_fly` automatically, so after
merging, confirm the `deploy_fly` job and its `/health` poll actually
succeeded (check the workflow run's jobs, not just that the PR merged)
before reporting the feature as live. If `deploy_fly` fails, that's a
production incident: report it immediately and in full rather than
treating it as a loose end - this is exactly the kind of event the
Maintain phase exists to close the loop on.

## Boundaries

- Never rewrite history on a branch, force-push, or skip CI hooks.
- Never merge with unresolved review comments a human reviewer left - if
  a real person (not a bot, not this pipeline) has commented on the PR,
  surface that to the orchestrator before merging, even if CI is green.
- The "never cross the production gate on your own" rule has no exception
  for confidence, urgency, or a plausible-sounding reason the human would
  probably say yes - if they haven't said it in this conversation, it
  hasn't been said.
