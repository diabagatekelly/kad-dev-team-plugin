# Design: implementation flow v3, the chunk loop

Internal design, written 2026-10-24 before any skill changes, for the user to
read and approve. It replaces the quarantine/grade/combine/finalize/re-grade
procedure (v2) in `skills/orchestrator/SKILL.md`. Evidence and the seven
decisions it rests on are in the audit-docs repo:
`personal-finance-tracker-slice-1/plugin-review/2026-10-24-implementation-flow-review.md`.

## 1. What v2 got wrong, in one paragraph each

**The token sink was context growth, not reviewer count.** Two heavy-loop
instances cost $63 of the $94 quarantine session; the finalize instance's
input grew from 36k to 788k tokens over 364 turns because every test run,
edit and inline skill load stayed in context, and two fix rounds were sent
to the same instance by message. The 26 reviewer agents cost $18 and the two
judges $4.

**The judge was pure position bias and the second candidate was cheap.**
Each judge order picked the implementation shown first. The lite candidate
cost $5, found a different Critical than the heavy one and contributed two
ideas. The expensive part was running the heavy loop twice.

**The giant commit followed from two rules.** `tdd-implementation` says not
to invent a commit discipline, and the gate's baseline is the commit the
worktrees branch from, so no candidate could commit without breaking the
gate. Result: one 79-file, 7,313-line commit made by the orchestrator after
"commit and get out of here".

**Inline self-review bought little.** 85 per-cycle `test-quality-review`
calls inside the finalize instance missed the two High test-quality findings
a separate reviewer found minutes later.

**Nothing ran on the model the agent definitions name.** Every agent ran on
the session's model; the `model:` frontmatter is not applied in practice
(verified on Claude Code 2.1.304 and 2.1.310). The Agent tool's own `model`
parameter is the lever that works.

**The orchestrator authored too much.** A combine brief, two digests, a
hand-written map extractor and after-the-fact log edits produced four
orchestrator errors in one flow.

## 2. Decisions this design implements

| # | Decision (2026-10-24) |
|---|---|
| 1 | The implementer writes the chunk plan into the implementation report; the build starts without approval. |
| 2 | `tdd-implementation` (heavy) and `tdd-implementation-lite` both stay, chosen per slice by the policy question; `compare` is gone. Each runs inside a short-lived per-chunk agent. |
| 3 | Per chunk: test-quality, code and architecture review always; security, reliability and accessibility when the chunk touches their territory. All six once on the whole slice diff at the end. |
| 4 | Critical, High and Medium fixed per chunk by a fresh fixer, one round, re-validated. Lows filed as tracker issues at slice end. No open-ended rounds. |
| 5 | Sonnet 5.5 for implementer and fixer, Opus 5.5 for every reviewer, passed as the Agent tool's `model` parameter on each launch. |
| 6 | No candidates, no judge, no combine brief. |
| 7 | Chunks are committed locally on a slice branch; at slice end the orchestrator pushes, opens the PR without asking and files the Lows as issues; Sourcery's PR comments are then evaluated and addressed as Opus judges appropriate. |
| earlier | Sandbox check first, platform-agnostic, strong recommendation with a logged opt-out, never a hard stop. One question per turn via `AskUserQuestion`. Git, tracker and CI/CD skills designed here. Eval cases after the redesign. |

## 3. The Gas Town shape, kept and dropped

| Gas Town | Here | Kept? |
|---|---|---|
| Mayor coordinates, never codes | orchestrator skill, inline | kept; it also stops writing briefs and digests |
| Bead: atomic, git-backed unit of work | chunk: one entry of the chunk plan, one commit | kept |
| Convoy groups beads | slice branch | kept |
| Polecat: persistent identity, ephemeral session, own worktree, submits and goes idle | fresh implementer agent per chunk; the implementation report is the persistent identity | kept |
| Refinery: merge queue, gates before main, bisects a failing batch | per-chunk gate plus validators before the next chunk starts; the slice-end review before push | kept, without batching (one chunk at a time, nothing to bisect) |
| Witness: detects stuck agents, nudges or escalates | a stall rule on the implementer: `maxTurns`, and a one-message nudge before relaunch | kept, mechanical |
| GUPP: work on the hook runs without waiting for input | the implementer never asks; gaps go in the report | already the rule |
| Nudge and mail | `SendMessage` to a running agent | used only for the stall nudge, never for fix rounds (that is what grew the context) |
| Dolt-backed beads, seance, dogs | none | dropped: git and the report are enough at this scale |

## 4. The row's procedure

The `tdd-coach:tdd-implementation` row of the state table keeps its
trigger. What changes is what step 4 does for it.

### A. Start

1. **Sandbox check, first, before any question.** Run
   `sandbox_check.py --project <root>` inline. The `platform` check becomes
   descriptive: it reports which sandbox the platform has (Seatbelt on
   macOS, bubblewrap on Linux and WSL2, none on native Windows) and the
   script exits 2, not 1, when the platform has none. On a fixable `FAIL`
   (settings, deny lists) offer `--write-settings` once, as today. On exit
   2, or when the probes still fail after settings, ask once with
   `AskUserQuestion`: continue unsandboxed (the code-writing agents run
   with Bash and the Read deny rules only), or stop. The A line records
   `sandbox — PASS (<platform>)` or `sandbox — none on <platform>; owner
   opted to continue unsandboxed`. The deny-list half of the settings is
   still written on a yes, since `Read(...)` deny rules work on every
   platform. The check is repeated before every later launch; a change
   from PASS to FAIL mid-flow ends the flow as today.
2. **Policy question**, one `AskUserQuestion`, heavy or lite or not now.
   Compare is removed. Skip it when the user's message named one.
3. **Branch.** From the current commit, `git switch -c slice-<nnn>-<slug>`
   (the slug from the slice file's title). If planning documents are
   modified or untracked, commit them first on this branch as
   `Planning: slice <nnn> ready for implementation`; this is the only
   planning commit the flow makes, and the A line says so. The base commit
   (`git rev-parse HEAD` after that) is written on the A line; every gate
   and every reviewer diff in this flow is computed against it or against
   the previous chunk's commit, so no baseline file is needed.
4. **Log entry** written before step 1 (the entry records the route, as
   today); the A line is appended after step 3.

### B. Plan

Launch one implementer agent (`kad-dev-team:tdd-coach:AGENT`, `model:
"sonnet"`) whose task is: invoke the policy's skill first; read the slice,
the design, the criteria documents, the screen design if UI-touching, and
the unit's read context by path; consult `map-query`; write the **chunk
plan** into `planning/implementation-report-slice-<nnn>.md` and stop,
building nothing. The chunk plan is an ordered list of three to eight
chunks (four to eight until the first run on 2026-10-24, where the floor
of four made every planner pad the plan with a test-only chunk), each
with:

- a title (the commit's subject line, imperative, under 60 characters);
- the behaviour it delivers, as the acceptance or runtime-safety criteria
  it makes pass, verbatim identifiers from the slice;
- the files it creates or changes (the gate's `--allow` list for that
  chunk), tests included;
- its done check: the test names that must be green, plus anything
  runnable (a route answers, a screen renders);
- which reviewer territories it touches: adapter or secret, HTTP, storage,
  error handling, UI. This drives decision 3.

Rules the skill gives it: chunks are vertical (a behaviour end to end, not
"all the types" then "all the tests"); the first chunk is the thin path's
smallest observable step and includes the project's wiring if none exists;
a chunk must be buildable in one short agent session (a rule of thumb the
skill states: under 40 test runs); gaps in the design are escalated in the
report, not planned around. The orchestrator checks three things
mechanically and nothing else: the plan exists, every chunk names at least
one criterion and at least one file, no file is outside the slice's module
dirs as the design names them. It does not edit the plan. The B line lists
the chunk titles.

### C. Chunks, one at a time

For chunk k:

1. **Build.** Launch a fresh implementer (`model: "sonnet"`, `maxTurns`
   from the agent definition, see §6) with: the policy's skill to invoke
   first; the chunk's plan entry verbatim; the slice documents by path; the
   implementation report by path (its earlier chunk sections are the
   handover from the previous agent); the rule that it builds this chunk
   alone, commits when its done check passes, and reports. The skill tells
   it how: heavy or lite as today, then `git add` of the files it changed
   and `git commit` with the chunk title as subject and a body naming the
   criteria made green and any decided gap. It appends a `### Chunk k`
   section to the report (what it built, what it decided, what it
   escalated, the commit hash) as part of the same commit. It never
   pushes, never touches `planning/` except its report, never commits a
   file outside its plan entry; a file it needed that the plan did not
   name is committed and named in the report as a plan deviation, which
   the gate then judges.
2. **Gate**, inline, on the chunk's commit range:
   `validation_gate.py --project <root> --base <previous commit>
   --test-cmd <documented> --allow <chunk's files> --allow <report path>
   --protect <every other planning document> [--coverage]`. Suite green,
   change set non-empty, scope, protected, coverage as today. A `FAIL`
   goes to a fresh fixer (`model: "sonnet"`) once, as a named fix through
   the skill's handed-back path, which commits the fix; the gate runs
   again. A second `FAIL` ends the flow: the branch stays as it is, the C
   line says which checks failed, the report says what is built.
3. **Validate.** Sandbox check, then in parallel, `model: "opus"`,
   each handed the chunk's diff (`git diff <previous>..HEAD`, the report
   left out), the files it touched, and the slice's criteria and design by
   path, nothing of the flow's own state: `tdd-coach:test-quality-review`,
   `code-reviewer:code-review`, `software-architect:architecture-review`
   always; `devsecops-engineer:security-review` when the chunk's
   territories include adapter, secret, HTTP or storage;
   `devsecops-engineer:reliability-review` when they include HTTP,
   storage or error handling; `accessibility-engineer:accessibility-review`
   when they include UI (it drives the built screen, as today). No map diff
   per chunk: `map-update` runs once at D, and the architecture reviewer
   reads the diff.
4. **Fix rounds, until clean, capped at five** (§4e). Every Critical,
   High and Medium goes to one fresh fixer (`model: "sonnet"`) in one
   batch, as named fixes through the skill's handed-back path, one commit
   per fix or one for the batch, the fixer's call. Then the gate again on
   the fix range, and every reviewer that ran on the chunk re-runs on the
   files the fix touched. Findings the re-run raises start the next round;
   a round with no Critical, High or Medium is clean and the chunk is
   done. After the fifth round, a standing Critical or High stops the flow
   before the next chunk and is reported for the user to decide; a
   standing Medium is filed as an issue at E, never carried silently. Lows
   are appended to a `### Lows` list in the report with file and line,
   never fixed here.
5. **C line** for the chunk: title, commit hashes, gate result, reviewers
   run, findings by severity, fix commits, what is carried.

The orchestrator holds no digest and writes no brief: the reviewers'
reports are handed to the fixer verbatim (the finding text, file and
line), and the log line holds counts and hashes.

### D. Slice review

When the last chunk is accepted: `map-update` for real, inline, against the
tree (the persisted map); then all six reviewers (accessibility only if
UI-touching), `model: "opus"`, on the whole slice diff (`git diff
<base>..HEAD`, report and map left out), the map diff, and the slice
documents. Critical, High and Medium go through the same fix rounds as
C.4, until clean, capped at five, with all six reviewers re-running on
each fix's files. Lows join the report's list. A Critical or High still
standing after the cap is reported and the flow stops before delivery;
standing Mediums are filed at E. The D line carries every round.

### E. Delivery

1. `map-update` again if D's fix changed anything.
2. Push the branch (`git push -u origin <branch>`).
3. PR: `docs-writer:pr-writeup` writes the body from the report (what was
   built chunk by chunk, decided gaps, escalations, the Lows left, the
   model and tool provenance line); `gh pr create` opens it against the
   default branch. No question is asked.
4. Issues: each Low becomes one issue in the project's tracker, the one
   `user-story-writeup` recorded for this project (GitHub via `gh issue
   create` with a `tech-debt` label when that is the tracker), titled by
   the finding, bodied by its text, file and line, and linked from the PR
   body. If no tracker was recorded, the Lows stay listed in the PR body
   and the E line says so.
5. External review triage: wait for the PR's review checks to complete
   (poll `gh pr checks` and the PR's reviews until no check is pending, up
   to a bound the skill states). Read every review comment that is not
   from the plugin's own reviewers. Launch `code-reviewer:code-review`
   with `model: "opus"` and the skill `external-review-triage` (new, §5)
   to judge each comment against the code, the slice documents and the
   plugin's own findings: **fix** (a real defect or a cheap improvement
   inside the slice), **decline** (wrong, out of slice, or contradicts a
   decided document; the reason is posted as a reply), or **defer** (right
   but not this slice; filed as an issue like a Low). Fixes go through a
   fresh fixer, gate, push; replies and issues follow. Each push brings
   the external reviewer back, so its new comments on the fix start the
   next triage round: until a round has nothing to fix, capped at five
   rounds (§4a); comments that arrive after the cap are the user's.
6. The E line: pushed hash, PR number, issue numbers, external comments by
   verdict.

Then step 5 as today: report, and stop at the terminal row.

### Stall rule (the Witness)

Each implementer and fixer launch sets `maxTurns` (agent definition, §6).
An agent that returns at its turn limit without a commit is nudged once by
`SendMessage`: commit what passes its done check, report the rest as not
built. If it returns again without a commit, the orchestrator records the
stall on the C line, discards nothing (the working tree is left as it is),
and launches a fresh implementer for the same chunk with the stalled
agent's report as handover. A second stall on the same chunk stops the
flow.

### The log entry

```markdown
## <n>. <date> — slice ready for implementation

**Routed to:** chunk loop
**Artifact:** see sub-entries below
- **A. Start:** sandbox — `<PASS (<platform>) | none on <platform>; owner opted to continue unsandboxed | FAIL: <checks>; flow not started>`; policy — `<heavy | lite>`; branch — `<name>`; base — `<sha>` (`<planning commit sha, if one was made>`)
- **B. Plan:** `<k>` chunks — `<title 1>`; `<title 2>`; … (in `<report path>`)
- **C. Chunk <k>/<n>:** `<title>`; `<model>` `<turns>`t `<min>`m; commits `<sha…>`; gate `<PASS | PASS after <sha> | FAIL: <checks>; ended>`; reviewers `<initials, e.g. tq co ar se re ac>`; r0 `<C/H/M/L>`; r1 fix `<sha>` → `<C/H/M/L>` (reg `<r>`, pre `<p>`); r2 …; `<clean r<i> | cap: <standing>>`; L `<count>`
- **D. Slice review:** map `<path>`; reviewers `<initials>`; r0 `<C/H/M/L>`; r1 fix `<sha>` → `<C/H/M/L>` (reg `<r>`, pre `<p>`); …; `<clean r<i> | cap: <standing>>`
- **E. Delivery:** CI `<present | added <sha>>`; pushed `<sha>`; PR `<#>`; issues `<#…>` (L `<n>`, M `<m>`, deferred `<x>`); ext r1 `<n>`c: fix `<f>` (`<sha>`), decline `<d>`, defer `<x>`; r2 …; `<clean r<i> | cap: <open>>`; audit `<sha>`
```

## 4a. Fix rounds: until clean, capped at five, and logged for the audit

Decided 2026-10-24, to be re-evaluated after the first slices run on
smaller chunks: in loops 2, 3 and 4 a fix is re-reviewed, and whatever the
re-review raises is fixed in the next round, until a round raises no
Critical, High or Medium (loop 4: no comment to fix), with a hard cap of
five rounds per stage. The alternative considered, a one-round rule with
regressions-only Mediums, is the fallback if the churn the 10-20 session
showed (13, 7, 6 Mediums in three rounds) returns on small chunks.

What one round is:

1. The fixer gets every finding of the previous round in one batch,
   verbatim (reviewer, severity, file, line, text), and commits.
2. The gate runs on the fix's commit range.
3. Every reviewer that ran on this chunk (or the slice, at D) re-runs on
   the files the fix touched, with the fix's diff, nothing of the earlier
   rounds. Not only the reviewers that raised the findings: a fix one
   reviewer asked for is what another reviewer objects to (the error-cause
   trade-off in the real run).
4. The orchestrator classifies each new finding mechanically before it
   logs it: **regression** if its line is inside the fix's diff hunks,
   **pre-existing** otherwise. Both are fixed in the next round under this
   rule; the classification is recorded so the audit can tell churn (a
   reviewer finding new things in old lines on each read) from fixes that
   break things.

What is logged, so the rule can be judged later:

- On the C, D and E lines: one segment per round with the fix commits, the
  counts by severity, the regression/pre-existing split, and how the
  stage ended (clean after round *i*, or the cap).
- In the implementation report, a `### Rounds` table per chunk and for the
  slice review: round, reviewer, severity, finding title, file:line,
  regression or pre-existing, fix commit, and the fixer's agent id and
  turn count. The E section gets the same table for external comments
  with the triage verdict.
- The reviewer reports themselves, per round, under `KAD_AUDIT_DIR` as
  today's hooks keep them, and in the audit repository after `audit_sync`
  (§4d), named by chunk and round.
- `orchestrator_log_check.py` learns the round segments and reports, per
  slice, rounds per chunk, how often the cap was hit, and the share of
  regressions, so the next review of a real run has the churn figure
  without re-deriving it.

**Keeping the record cheap.** Writing a log line costs its output tokens
once; what cost money in the real run was what re-entered an agent's
context and was re-read every turn: the 26 reviewer reports handed back
verbatim into the orchestrator (about 100k tokens re-read for the rest of
the session), the orchestrator's digests, and the report and log every
later agent read as input. So the full record goes where no agent reads it,
and agents exchange pointers and counts:

1. **Reviewers write their report to a file and hand back five lines.**
   The task names the path (under `KAD_AUDIT_DIR`, by slice, chunk and
   round); the hand-back is the counts by severity and the path. The fixer
   reads the file itself, once. This applies to every reviewer launch in
   the flow, not only the fix rounds.
2. **The audit detail lives in a sidecar no agent reads by default.** The
   rounds table (finding, reviewer, severity, file:line, regression or
   pre-existing, fix commit, fixer agent id and turns) is
   `.git/kad-audit/rounds-slice-<nnn>.jsonl`, one line per finding, read
   by `orchestrator_log_check.py` and the cost scripts, copied by
   `audit_sync`. The implementation report, which every chunk agent reads
   as handover, keeps five to ten lines per chunk: built, decided,
   escalated, commits, round count. No rounds table in the report.
3. **Log lines are terse pointers.** A round segment reads
   `r1 fix a1b2c3d → 0/1/2/3 (reg 1, pre 2)`, about 25 tokens; hashes,
   round numbers and file names locate the detail, and the transcripts the
   hooks keep are the complete record, so nothing is restated for
   completeness.
4. **The orchestrator does not echo.** One paragraph per event in the
   chat, no digests, no restated findings; it reads the gate's output with
   a tail unless the result is `FAIL`, and opens a reviewer's file only to
   decide something (a standing finding after the cap).

Per chunk this comes to about 200 output tokens of logging and nothing
re-read, against the quarantine flow's 1,500-word entry and the reports it
carried in context.

Cost: one round is one Sonnet fixer and three to six Opus re-reviews, about
$3. The worst case for a six-chunk slice is five rounds on every chunk plus
five at D, about $100 more than the one-round shape; the real run's rounds
shrank each time, so the expected case is one or two rounds per chunk.

## 4b. Where the loops are, and what each one looks like

Five loops, each with a fixed bound (the fix rounds' bound is the cap of
five, §4a).

```
orchestrator (inline, session model)
│
├─ A  start: sandbox → policy → branch → log
├─ B  plan agent ──────────────────────────────▶ chunk plan in the report
│
├─ C  for each chunk k (loop 2, bounded by the plan's length)
│     ├─ build agent (Sonnet) ── loop 1 inside it: heavy RED→GREEN→REFACTOR→self-check
│     │                           per Test List entry, or lite tests→stub→code→break check;
│     │                           bounded by the chunk's done check and maxTurns
│     │                           → commit(s)
│     ├─ gate on the commit range ── FAIL → fixer (Sonnet) once → gate again → FAIL ends the flow
│     ├─ validators (Opus, 3 to 6, parallel) → findings
│     ├─ C/H/M → one fixer (Sonnet), one batch → commit(s) → gate → all the chunk's reviewers on the fix's files
│     │     new C/H/M → next round … until a clean round, cap 5
│     │     after the cap: standing C/H → stop and report;  standing M → filed at E;  L → report's list
│     └─ C line (one segment per round)
│
├─ D  slice review: map-update, six reviewers on base..HEAD → fix rounds as C, cap 5 → D line
│
└─ E  delivery: CI if absent → push → PR (pr-writeup body) → Lows and standing Mediums as issues
      → wait for external checks → triage agent (Opus) → fix / decline+reply / defer-as-issue
      → push → new comments → next triage round … until none to fix, cap 5; later comments are the user's
      → audit sync → E line

stall (loop 5, orthogonal): an agent at its turn cap with no commit → one nudge → one relaunch with handover → stop
```

What the user sees in the terminal is the orchestrator's own voice between
launches, one short paragraph per event, the same as today's quarantine
flow but with hashes: "Chunk 2 of 6 (record posted transactions only):
committed a1b2c3d; gate PASS; test-quality, code and architecture reviewed;
1 Medium fixed in d4e5f6a, 2 Lows listed; starting chunk 3." Between those
paragraphs the session is quiet while an agent works; the orchestrator does
not narrate the agent's turns. A stall, a gate failure that survives its fix
round, or a standing Critical or High is the only time the flow stops to
talk to the user mid-slice; everything else waits for the step 5 report.

Where the loops are **not**: no reviewer watches an implementer type; no
agent is resumed by message for a fix round (each fix is a fresh agent on a
short context); no round without a cap and a log segment.

## 4c. CI, local checks and infrastructure

Three layers, each the same commands, run in three places:

| Layer | When | What runs | Who provides it |
|---|---|---|---|
| Local, per chunk | the gate, after each chunk commit and each fix commit | the project's documented test command (the full suite), typecheck and lint when the project documents them, coverage thresholds, scope and protected-document checks | `validation_gate.py`, already there; it learns to run the documented `typecheck` and `lint` scripts when `package.json` (or the stack's equivalent) names them |
| Local, per commit (optional) | a git pre-commit hook in the project | typecheck and lint on staged files, never the full suite | `release-engineer:repo-bootstrap` (phase 2) offers it as a project decision; the chunk loop does not install hooks on its own |
| Remote, per PR | GitHub Actions (or the host's equivalent) on every push to the PR branch | install with a frozen lockfile, typecheck, lint, the full suite with the coverage thresholds, a dependency audit; pinned action SHAs, least-privilege `permissions`, no secrets | `release-engineer:ci-pipeline` |

**When CI gets set up.** `technology-bootstrap` deliberately defers
infrastructure ("ahead of need"), and a PR with no checks is the first real
need. So `ci-pipeline` runs inside E of the **first slice whose delivery
finds no CI configuration in the repo**: before the push, it writes the
workflow for the project's stack, mirroring the gate's commands so local
and remote agree, commits it on the slice branch (its own commit, "CI:
test, typecheck and coverage on pull requests"), and the PR that follows
exercises it. The orchestrator's E line records that CI was added. On later
slices the step is skipped because the configuration exists; a change to
the gate's commands (a new lint script, say) is a `ci-pipeline` re-run the
delivery step offers in its report, not something it does silently.
`ci-pipeline` hands its result to `devsecops-engineer:operational-readiness`
for review only when a deployment path exists; a test-only workflow needs
no readiness review. This moves `ci-pipeline` from phase 2 into the
delivery PR (build step 5), since the first delivery needs it;
`repo-bootstrap` stays phase 2.

**Deployment (CD) and infrastructure** stay deferred until a slice's own
documents call for an environment (a slice whose acceptance criteria
cannot be met locally, or a user story that names a deployment). That is a
`release-engineer:deployment` skill for phase 2, reviewed by
`operational-readiness`; nothing in the chunk loop assumes one exists.
Sourcery is not CI: it is an external reviewer the triage step reads, and
its check's green is not a gate the flow waits on except to know the
comments are in.

## 4d. Audit mode and the audit repository

Audit mode today (`hooks/audit.sh`, `KAD_AUDIT=1`) logs calls and keeps
transcripts under `~/.claude/kad-audit`. Nothing yet puts the audit
material where the user wants it: a separate repository (currently
`github.com/diabagatekelly/audit-docs`), cloned inside the project,
invisible to the project's own git, easy to update and push. This design
adds it:

- **`KAD_AUDIT_REPO`** (a clone URL) joins `KAD_AUDIT` and `KAD_AUDIT_DIR`
  as the audit mode's third setting. When set, the `SessionStart` hook
  (new; today only `SessionEnd` and the tool matcher exist) checks the
  project for `audit-docs/`: if absent, it clones the repository there and
  appends `audit-docs/` to `.git/info/exclude`, so the project's
  `.gitignore` is untouched and nothing about the audit shows in the
  project's history. Not a git submodule: a submodule records a gitlink in
  the parent, which is exactly what must not appear.
- **`audit_sync.py`** (`skills/orchestrator/scripts/`, also runnable by
  hand): copies, for the current slice, the planning documents, the
  orchestrator log, the implementation report, the persisted map, the gate
  outputs and reviewer reports the flow kept (per-agent transcripts from
  `KAD_AUDIT_DIR`), and the session transcripts, into
  `audit-docs/<project>-slice-<nnn>/` under the layout the first slice
  established (`planning/`, `implementation-docs/`, `plugin-review/`),
  then commits in the clone and pushes. It greps what it copies for
  credential-shaped strings first and refuses on a hit, the same check the
  2026-10-24 copy did by hand.
- **When it runs:** at the end of E (delivery) in the chunk loop, and on
  request ("sync the audit docs"). The E line records the audit commit.
  The `SessionEnd` hook keeps doing what it does; the sync reads from what
  it kept.
- `audit-review` reads from the clone when it exists (the reviews this
  design rests on were written there by hand), and its proposed fixes and
  eval cases are written as `plugin-review/<date>-….md` in the same place.

Build order: the hook and the sync land with `delivery` (step 5).

## 5. What changes where

### `skills/orchestrator/SKILL.md`

- The "Quarantine, grade, combine" section is replaced by "The chunk
  loop" (§4). The policy question loses compare. The sandbox wording
  changes from "the flow runs in a WSL2 session" to the platform-agnostic
  check with the logged opt-out. The row's log format is §4's.
- Step 4's text "the quarantine flow invokes this skill behind a sandbox
  check" and every "candidate", "judge", "combine brief" reference goes.
- The orchestrator never writes a brief, a digest or a map extractor. If
  `map-update` has no tool for the project's language it says so and the
  reviewers go without a map diff; the orchestrator does not write one.

### `skills/tdd-implementation/SKILL.md` and `tdd-implementation-lite/SKILL.md`

- New section **Chunk plan**: when the task asks for the plan, write it
  (format and rules in §4.B) into the report and stop.
- New section **Building one chunk**: when the task names a chunk, build
  that chunk alone; the Test List (heavy) or the tests (lite) come from the
  chunk's criteria; the done check decides when to stop; then the commit.
- The commit paragraph replaces "If the project already commits as part of
  this work … Don't invent a commit discipline": under the orchestrator's
  chunk loop the chunk is committed as §4.C.1 says; invoked directly, the
  old rule stands (commit only if the task or the project says so).
- The report gains `### Chunk k` sections and a `### Lows` list; the
  heavy skill's per-cycle `test-quality-review` call stays (decision 2) but
  the skill says in one line that it is a self-check and the separate
  reviewer after the commit is the review.
- "FINAL REVIEW — unless the orchestrator grades it" stays for direct
  invocation; under the chunk loop the task says the orchestrator reviews.

### `skills/orchestrator/scripts/`

- `sandbox_check.py`: `platform` reports the platform's sandbox and exits
  2 when there is none; the README's settings block is unchanged.
- `validation_gate.py`: unchanged in function; `--base` is now the normal
  path and `--record-baseline`/`--baseline` stay for direct use. Its
  docstring's first paragraph is rewritten for the chunk loop.
- `pairwise_judge.py` is deleted here. `evals/tools/pairwise_judge.py`,
  the eval suite's own judge, is a different file and stays.

### Agents

- `agents/pairwise-judge/` is deleted.
- `agents/tdd-coach/AGENT.md`: `maxTurns` set (a per-chunk cap; start at
  120 and tune from the next real run, where the lite candidate needed 65
  turns for a whole slice and the heavy one 254); `autoCompactWindow:
  200000` as a backstop; the `model:` line stays as documentation with a
  comment that the orchestrator passes the model on launch.
- Every reviewer agent definition gets the same comment. No persona
  changes otherwise.

### New: `release-engineer` persona (phase 2 except `delivery`)

The roster has no owner for repo creation, pipeline config or delivery
(PERSONAS.md "Post-implementation gaps"). `devsecops-engineer` holds the
"never writes pipeline config" boundary on purpose, so this is a new
persona, not an extension:

- `delivery` (**built with this redesign**): push the slice branch, open
  the PR with `pr-writeup`'s body, file the Lows and deferrals in the
  recorded tracker, run the external-review triage loop (§4.E). Owns the
  git and `gh` mechanics; never decides what to build.
- `repo-bootstrap` (phase 2): create the repository and remote, the
  default branch, `.gitignore`, branch protection; decided with the user,
  recorded in the technology-bootstrap document.
- `ci-pipeline` (**built with this redesign**, see §4c): write the CI
  configuration the project's stack needs (install with a frozen lockfile,
  typecheck, lint, the suite with its coverage gate), hardened (pinned
  action SHAs, least-privilege permissions); runs inside the first delivery
  that finds no CI; hands the result to
  `devsecops-engineer:operational-readiness` for review once a deployment
  path exists, which keeps that persona's boundary intact.
- `deployment` (phase 2): CD and infrastructure when a slice's documents
  first call for an environment; reviewed by `operational-readiness`. The `flexion-ai-devops-tools:ci-pipeline-setup`
  skill installed on this machine is a reference for the hardening rules,
  not a dependency.

### New: `code-reviewer:external-review-triage`

Judge each comment an external reviewer (Sourcery, a human, another bot)
left on a PR against the code as it is, the slice's documents and the
plugin's own findings on the same files. Three verdicts, fix, decline with
reason, defer to an issue. Never applies a fix itself; never declines a
comment because the plugin's reviewers missed it; a comment that
contradicts a decided planning document is declined with the document
named. Reports a table the orchestrator acts on.

### README and PERSONAS

- README: "Implementation policy" loses compare; "Running the quarantine
  flow: the sandbox" becomes "Running the chunk loop: the sandbox", with the
  platform table and the opt-out; a short "Delivery" paragraph.
- PERSONAS: the Orchestrator section's v2 paragraph is replaced by a v3
  paragraph pointing at §4; the "Post-implementation gaps" list records
  which gap `release-engineer` closes and which wait.
- `evals/README.md`: the quarantine cases are retired or rewritten (below).

## 6. Launch table

| Launch | Agent | `model` | Context given | Returns |
|---|---|---|---|---|
| Plan | tdd-coach | sonnet | policy skill, slice docs, unit read context, report path | chunk plan in the report |
| Chunk build | tdd-coach | sonnet | policy skill, chunk entry, slice docs, report path | commit(s), report section |
| Fixer | tdd-coach | sonnet | policy skill (handed-back path), findings verbatim, files | fix commit(s) |
| Chunk validators | tdd-coach, code-reviewer, software-architect, devsecops-engineer ×2, accessibility-engineer | opus | the chunk's diff, files, criteria and design by path | findings report |
| Slice reviewers | the six | opus | the slice diff, map diff, slice docs | findings report |
| Triage | code-reviewer | opus | PR comments, code, slice docs, own findings | verdict table |

Every launch passes `model` explicitly. The orchestrator runs inline on the
session's model. Nothing is launched with `isolation: "worktree"`: the slice
branch in the real tree is the worktree, and one agent writes at a time.

## 7. Cost model, against the real run

The slice 1 quarantine session ran about $94 and the follow-on review
session $41. For a six-chunk slice under this design, at list prices:

| Item | Count | Each (est.) | Total |
|---|---|---|---|
| Plan agent (Sonnet) | 1 | $1 | $1 |
| Chunk builds (Sonnet, short context) | 6 | $1.50 | $9 |
| Fixers (Sonnet) | ~6 | $0.75 | $4.50 |
| Chunk validators (Opus, 3 to 6 per chunk) | ~26 | $0.50 | $13 |
| Slice reviewers (Opus) | 6 | $0.70 | $4 |
| Triage (Opus) | 1 | $1 | $1 |
| Orchestrator (session model) | | | $8 |
| **Slice** | | | **about $40** |

The saving is almost entirely the implementer's context: a chunk agent
starts at roughly 40k tokens and ends under 200k instead of 788k. Reviewer
spend goes up slightly (per-chunk validators) and is the part of the budget
that found the Criticals last time.

## 8. Eval cases to build after the skills land

1. Chunk plan: the plan is vertical, three to eight entries, each with
   criteria, files and a done check; a plan of "types, then tests, then
   UI" fails.
2. One chunk only: an implementer handed chunk 2 does not build chunk 3's
   behaviour, and commits once with the chunk title.
3. Gate on a chunk: a commit touching a file outside the chunk's list is
   caught; the fixer's commit clears it.
4. Validator selection: a chunk touching only the strategic core runs
   three reviewers; one touching the adapter runs five.
5. Fix rounds: Critical, High and Medium are fixed, a Low is listed, not
   fixed; a re-review that raises a regression starts round two; a clean
   round ends the stage; the fifth round ends it with the standing
   findings reported, and every round is on the log line with its
   regression/pre-existing split.
6. Sandbox opt-out: on a platform with no sandbox the question is asked
   once, the choice logged, nothing hard-stops.
7. Delivery: the PR body comes from the report; each Low is one issue in
   the recorded tracker; no question is asked.
8. Triage: a wrong external comment is declined with a reason, a right one
   is fixed, an out-of-slice one is deferred to an issue.
9. Stall: an implementer that hits its turn cap without a commit is nudged
   once, then replaced with handover.
10. The log entry: A to E lines in order, chunk lines with hashes, no
    after-the-fact edits (`orchestrator_log_check.py` learns the new
    format).

The two routing cases that expect the quarantine flow,
`evals/orchestrator-route-implementation/` and
`evals/orchestrator-route-implementation-prenamed/`, are rewritten for the
chunk loop's A step (sandbox check first, policy question, branch, log
entry); nothing else in the suite exercises candidates, the judge or the
combine brief.

## 9. Build order

1. This document, approved.
2. `tdd-implementation` and `tdd-implementation-lite`: chunk plan, one
   chunk, commit, report sections.
3. `sandbox_check.py` platform change; orchestrator A step with the
   opt-out and the one-question rule.
4. Orchestrator B, C, D: the loop, the gate per chunk, the validators,
   the fixer, the log format; pairwise-judge removed; README and PERSONAS.
5. `release-engineer:delivery` and `ci-pipeline`,
   `code-reviewer:external-review-triage`, orchestrator E; the audit-mode
   `SessionStart` hook, `KAD_AUDIT_REPO` and `audit_sync.py` (§4d).
6. `orchestrator_log_check.py` for the new format; eval cases 1 to 10;
   version bump.
7. Phase 2: `repo-bootstrap`, `deployment`, the optional pre-commit hook.

Steps 2 to 4 are one PR; 5 is a second; 6 a third; 7 later.
