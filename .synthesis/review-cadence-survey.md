# Review cadence: what we looked at before changing the loop's reviews

Written 2026-11-06, from the owner's question after H3: the chunk loop
builds, reviews, fixes and re-reviews every chunk, then reviews the
whole slice once more at D. Would fewer reviews in between, with one
cold review of the slice by a strong model at the end, give the same
code quality for less, the way `tdd-implementation-lite` matched the
heavier implementer at a quarter of the cost? This file keeps what we
read so it can be read again, and what the decision rested on. The
decision itself is a third policy arm to be measured after slice 2, not
a redesign; see "What we decided" at the end.

## What our own runs say

- Run 3 (`audit-docs/personal-finance-tracker-3-slice-1/plugin-review/`):
  79 launches for one slice; the fixer caused about a quarter of the
  actionable findings; chunk-level Lows were mostly churn (H2.5 dropped
  them). The chunk reviewers and the six slice reviewers all missed the
  exchange-once seam that one whole-module cold read found and confirmed
  by execution.
- The three-run Opus check (`.synthesis/cold-read-check/README.md`): one
  cold, whole-module read per run found every load-bearing
  data-integrity bug on runs 1 to 3's recorded lists and confirmed each by
  running it; it missed input-handling and tooling bugs, which a
  checklist pass catches. So the slice-level cold read is where the real
  bugs are found, and the checklist second pass is for the rest.
- What the per-chunk reviews earned in run 3 was early routing: chunk 3's
  review raised a `needs-decision` that became security decision S18
  before five more chunks were built on the wrong assumption. A structural
  mistake is cheap at the chunk that makes it and expensive six chunks
  later.

## The orchestrators we looked at

### Gas Town (Steve Yegge)

- Repository: https://github.com/gastownhall/gastown (the official home;
  `github.com/steveyegge/gastown` redirects there; a hosted version by
  Kilo at https://blog.kilo.ai/p/gas-town-by-kilo).
- Roles: the Mayor (the primary coordinator with full workspace context),
  per-rig Witnesses (watch Polecats and the Refinery, detect stuck agents,
  trigger recovery, never implement), the Deacon (a background supervisor
  patrolling every rig, dispatching Dogs for maintenance), Polecats
  (worker agents, persistent identity, ephemeral sessions, one task each,
  finishing with `gt done`), the Refinery (the per-rig merge queue).
- Review: none per task by a model. The Refinery batches pending merge
  requests, "runs verification gates on the merged stack", merges on
  pass, and on fail bisects to isolate the failing request and merges
  the good ones (a Bors-style queue). The README does not say what the
  gates contain; polecats never push to main.
- What to take from it: the per-task check is mechanical and batched; the
  humans and the Mayor review outcomes, not diffs. Its answer to "a bad
  chunk built on" is the bisecting queue, not an early review.
- Read again for: how the gates are defined per rig; what the Witness
  counts as stuck; how work is tracked in git (the beads tracker);
  whether anything reads the code before merge. Secondary reads: heise's
  write-up
  (https://www.heise.de/en/background/Full-Control-Gas-Town-Orchestrates-Ten-or-More-Coding-Agents-11178824.html?seite=2),
  the Codex-side account
  (https://codex.danielvaughan.com/2026/04/08/gas-town-multi-agent-factory/),
  and Gas Town's own framework survey, which was unreachable on
  2026-11-06 (https://gastown.dev/docs/research/w-gc-004-agent-framework-survey).

### Fan-out with review as each diff lands

- Superset (https://superset.sh/agent-orchestration): a large task split
  into independent subtasks, one agent per subtask, the diffs reviewed as
  they land. The common default in this space.
- The `agent-orchestrator` skill
  (https://skills.sh/mrclrchtr/skills/agent-orchestrator): dispatches a
  review subagent when an agent reports done, sends findings back to the
  same agent or a fresh one, loops until the review passes; a fresh
  implementer per cluster and a two-stage review (spec compliance first,
  then code quality).
- This is our shape today, minus the bisecting queue. Read again for the
  two-stage split, which maps to our criteria pass and cold pass in the
  other order.

### Milestone gates, one review at the end

- Addy Osmani, "The future of agentic coding: conductors to
  orchestrators" (https://addyosmani.com/blog/future-agentic-coding/):
  the orchestrator does not see every intermediate step; it ensures the
  final outcome meets the requirements.
- Unblocked's platform comparison
  (https://getunblocked.com/blog/ai-agent-orchestration-platforms-compared/):
  milestone gates where the tool handles retries and CI failures and a
  human steps in at PR time. It also reports, citing Google Research,
  that centralized coordination held error amplification to about 4.4x
  while independent parallel agents amplified errors 17.2x, and that
  multi-agent gains are up to 81% on parallelizable work and fall 39 to
  70% on sequential work. The number argues for keeping a mechanical
  gate per chunk even where the model review goes.
- Read again for: where the milestone sits (per feature, per PR), and
  whether anything structural is checked before the end.

### Agent review as necessary but not sufficient

- "The end of code review?"
  (https://codex.danielvaughan.com/2026/06/17/end-of-code-review-monperrus-crab-trust-calibrated-codex-cli-review-workflows-auto-review-subagent/),
  a secondary read of three June 2026 papers: on the c-CRAB benchmark
  agent review covers about 40% of what matters; it recommends tiered
  human review, essential for security-sensitive changes, API contract
  changes and infrastructure mutations.
- What to take from it: one final model review is not the whole answer;
  H5's mutation pass and the criteria second pass are the rest. Read the
  papers themselves before relying on the 40%.

Not found on 2026-11-06, worth a later search: anything specific on the
"Ralph loop" pattern, Devin's review cadence, and Anthropic's own agent
teams guidance on review frequency.

## What we decided

Not a redesign: a third policy arm, measured the way lite was (G2 in
`evals/TODO.md`):

- Per chunk, keep what is mechanical and cheap: the gate (typecheck,
  lint, suite, coverage, scope, Done-when names) and the smoke run. Drop
  the per-chunk model review and its fix round.
- Review at two points: once after the chunk that lands the seam (the
  structure is set and still cheap to change; the one place a
  `needs-decision` is worth a launch), once at D with the cold protocol,
  one fix round each.
- Measure before building: run 3's sidecar and records hold every chunk
  finding; classify each r0 finding as "local, D would have caught it
  the same" or "structural, it shaped a later chunk". If the structural
  bucket is one or two findings at the seam chunk, the arm is justified
  before a launch.
- Order: slice 2 runs the loop as it is (H5 is a clean comparison of
  lite's tests, and changing the review cadence at the same time would
  confound it). The light loop is the plugin PR after H5; slice 3 runs on
  it; the same sidecar measures compare the two.
