# Handoff: kad frozen at 0.19.0, the next plugin validated step by step (written 2026-11-20)

This file is the whole context a new session needs for the work after
kad 0.19.0. Read it first, then `TODO.md`'s top section (steps V0 to V9),
then only what a step points at. The prompt to start a session is at the
end.

## The owner's decisions (2026-11-19 and 2026-11-20)

1. No slice 2 of the two-arm comparison.
2. The fourth project's pull request #3 (`personal-finance-tracker-4`,
   the `light` build of slice 1) is **not merged**. Neither arm's branch
   is merged; the tags `light-arm-end` and `solo-arm-end` mark them.
3. kad is **frozen at 0.19.0**. Everything in `TODO.md` below its top
   section is parked, not cancelled. No kad skill, script or case changes
   unless the owner reopens it.
4. A new plugin is planned, and the owner's rule for it is: "take our
   time and really validate each step before we build on top of it".
   Each step of `TODO.md` V0 to V9 has a question, a measure and a bar
   the owner sets before it runs. A failed bar stops the list; the next
   move is the owner's. No plugin code before V7.
5. The sandbox is rethought (V0): likely a microVM per session, the
   actual microVM picked later; the new plugin carries no sandbox of its
   own. No sandbox at all is ruled out while sessions run on autopilot.
6. Planning personas are kept "even in a new plugin" (2026-11-18); the
   tests and the build are where a radically different approach is
   wanted.

## What was measured, and what it says

The evidence is in the private audit repository (the clone at
`~/.claude/kad-audit/repo`), folder `take-4-comparison/`: `README.md`
(the comparison), `frozen-method/RESULT.md` (the table tests),
`frozen-method/method.md` (also here as `.synthesis/frozen-table-method.md`,
sha256 `8830988e…`), every table, every matcher's scoring, both cold
reads, the mutation report and its logs (`mutlogs.tgz`), the probes, and
the scripts that cut cost and time from the transcripts (`timecost.py`,
`gaps.py`). In the cold reads A is `solo` and B is `light` (`key.txt`);
in the mutation report X is `solo` and Y is `light`.

### 1. The two-arm comparison (fourth project, slice 1, kad 0.19.0)

Both arms from the merged plan `5e1aef2`, compared at the end of their D
step (`light` at `f9def1b`, before delivery's CI files; `solo` at
`2d43502`, where it stopped on two walk Highs).

| Line of the bar | `light` | `solo` |
|---|---|---|
| Cold read (six areas) | 22 (4/4/4/4/3/3) | 21 (4/4/3/4/3/3) |
| Mutation kills, 47 shared mutants | 93.6% | 80.9% |
| Confirmed High standing | none | A6 (focus), A2 (contrast) |
| Cost / active time | $64.78 / 2 h 37 m | $38.02 / 2 h 18 m |

`solo` failed every line. But neither arm reached the bugs that matter:
both built the plan's one-minute give-up and its "initial update
complete" as written, and both were wrong about Plaid. `solo` lost its
mutation pass (a baseline failure no later run reproduced) and its first
browser walk (the sandbox) to the environment. Both arms ran at the same
time on one machine, sharing the sandbox, Chrome and the usage limit.

### 2. Across the four projects' first slices

Cold-read totals 22.5, 21, 24, 22 and 21 (of 30) while tests went 372,
619, 184, 105 and 38, and implementation cost fell from $328 to $38 to
$65. The same bugs came back in project after project (an item orphaned
after a lost reply, a zero amount given a direction, dates with no year,
a second connect). The cold-read total did not move with the number of
tests, but that is five builds of differing scope with one reader each.
Within the fourth project more tests did buy something: 12.7 points of
mutation kills (reproduced in the audit below). What holds: more tests
caught more code faults and none of the bugs that sit in what the plan
assumed about the outside world.

### 3. The completeness tables

Five tables built from a plan and the outside systems' documentation,
before any code: a dossier of each external system, state x event,
failure modes of each call, input partitions, lifecycle of each action.
Scored by a fresh matcher with strict rules against the cold reads (N
named, plan silent or contradicting the docs; D named, plan decided
right, build missed it; W named, plan decided wrongly; P part; X not
named).

| Run | Bugs | N+D (fully named) | W | Top-15 cells that hit a bug |
|---|---|---|---|---|
| Fourth project, columns written knowing its bugs | 33 | 22 (67%) | 1 | 9 of 15 |
| Fourth project, frozen method | 30 | 17 (57%) | 2 | 5, plus 4 partial |
| Third project slices 1 to 4, frozen method | 35 | 9 (26%) | 4 | 8 of 60 |

What it says: the frozen method named roughly half of the fourth
project's bugs and a quarter of the third's. How much of the 67% was
the bug-aware columns is **not established**: one run each, and the
same key was split into 33 defects in one scoring and 30 in the other,
so the 10-point gap may be noise until V2 measures the spread. The gap
between the projects plausibly follows the plan (the fourth project's
thinner plan left more gaps; the third project's remaining bugs were
code faults and wrong decisions); that too is one sample. The tables find gaps in a plan, not code faults and not
wrong decisions, flag far more than they hit, and vary in size from 171
to 675 cells by run. The best hits came from the provider's documentation
(Plaid's "initial update" covers about 30 days; a first pull can take
"2 minutes or more"; on the free tier, removing an item does not free
its slot).

### 4. Other orchestrators (searched 2026-11-20)

Kiro (AWS) writes requirements in EARS form, derives property-based
tests from them and keeps a requirement-to-task-to-test trace: prior art
for V7. GitHub Spec Kit runs spec, plan, tasks and implement, with specs
written by judgment. BMAD is persona roles, like kad. None found builds
completeness tables from a provider's documentation, challenges the
plan's decisions, or scores a planning method against real bugs. On
isolation, the field is moving to a microVM per session (Docker
Sandboxes, E2B on Firecracker, Apple's `container`; cloud sessions in
remote VMs); Claude Code's docs say to run inside a container, a VM or
the sandbox runtime when prompts are skipped. A macOS guest is capped at
two VMs per Mac.

## Audit of this analysis (2026-11-20, a second model)

The comparison and the table tests were orchestrated by Opus 5.5; the
owner had meant Fable to do it, so Fable 5.2 audited the conclusions
before the next session. Checked and holding: the scores and mutation
counts recounted from the raw files; three key mutants re-run on both
builds (unescaped HTML, partial rows after a failed save, the cursor not
advanced: all survive in `solo`, all killed in `light`); the Plaid facts
read directly in Plaid's documentation (30 days at the initial update,
"may take 2 minutes or more", ten Trial Items and removal "will not
allow you to create more", institution outages as HTTP 400, restart on
the pagination error); nine of the matcher's calls sampled against the
tables. The cold readers and matchers ran on Opus because
`evals/tools/cold_read.md` names it, which keeps the scores comparable
with earlier reviews.

Corrected in this file and in `TODO.md`: the "about 10 points of bias"
and "test volume does not track quality" claims (see sections 2 and 3).
Softer than they read: of the bar's four lines only the kill rate and
the cost are solid (the score line is one point from one reader per
build; the Highs line was hit by the sandbox costing `solo` its first
walk), so "do not adopt `solo` as it stands" holds and "`solo` cannot
work" was never shown; the third project's slice 1 was scored against a
wider key than the others (on numbered bugs only, 7 of 28, 25%: the
same conclusion). New: both builds' connection-limit codes
(`ADDITION_LIMIT`, `ITEM_LIMIT_EXCEEDED`) are probably wrong; the
documentation names `TRIAL_CONNECTION_LIMIT`.

## Where the new plugin lives (the owner, 2026-11-20)

**Decided for now:** a new folder in this repository, `next-plugin/`,
"so there's clear separation"; kad stays where it is at the root, and
nothing is moved to an archive folder. Each step's work goes under
`next-plugin/validation/V<n>-<name>/` (its `README.md` has the rules).
Whether the plugin itself gets a repository of its own is decided at
V9. What was weighed, for that later call: a new repository was
recommended over moving the present code to `archived-plugin/`. Reasons: this
repository's root is the installed plugin (`.claude-plugin/plugin.json`
and `marketplace.json` with `source: "./"`), so moving its code breaks
the installed kad and every path the eval suite, the hooks and the
gate's dependency map name; the new plugin needs a clean history, its
own name and version line, and none of the 160 cases; and what is
ported is copied across one item at a time with its tests (V9), which
keeps provenance. A plugin needs little: `.claude-plugin/plugin.json`
(name, description, version), then any of `skills/<name>/SKILL.md`,
`agents/`, `hooks/hooks.json`, `commands/`, and to install it a
marketplace (`.claude-plugin/marketplace.json`, in the same repository
or a separate one listing both plugins). None of it is created before
V9's design is read; V0 to V8 produce scripts, prompts and results,
which go in `next-plugin/validation/`.

## Lessons from running these tests (keep them)

- **Blind every reader.** Cold-read clones were neutral (`arm-A`,
  `arm-B`, tags and branches removed), and table builders saw only the
  plan folder with `implementation/`, the orchestrator log and the
  delegation files removed. The one unblinded step (my own columns and
  my own matching) gave 19 of 21 where the strict matcher gave 22 of
  33 on the same tables.
- **The matcher is a separate, fresh agent with strict rules** ("when in
  doubt, pick the less favourable class"; a generic cell counts only if
  it names the trigger). Never score your own method.
- **Freeze a method before the run that tests it,** with its hash, and
  change it only after the result is read.
- **One run measures nothing about variance** (V2 exists for this).
- **Two fenced sessions on one Mac collide** (the audit push raced; the
  browser walk failed under the fence until the owner approved a proxy).
- **A known kad bug, left alone while frozen:** the gate passes coverage
  through `NODE_OPTIONS`, which Node 24 refuses under `pnpm test`.
- **Cost by phase from transcripts:** `cost_by_role.py` totals whole
  sessions; cutting at a commit's time needs `timecost.py` (in the
  evidence folder). Commit dates can be rewritten by a re-author; use
  transcript timestamps.
- **The plugin repository is public; the audit repository is private.**
  As every earlier `TODO.md` and handoff has done, this repository holds
  summaries: project names, scores, costs, pull-request numbers and a
  bug named in a phrase. Anything that quotes a project (its code, plan
  text, tables, cold reads, probes, transcripts or data) goes to the
  audit repository. If the owner wants the summaries private too, they
  move with the rest; that is the owner's call, raised on #71.

## Prompt for the next session

Paste this to start:

> Read `.synthesis/handoff-next-plugin.md` in full, then the top section
> of `TODO.md` (steps V0 to V9). kad is frozen at 0.19.0: change no kad
> skill, script or eval case. We are validating, one step at a time, the
> pieces of a new plugin before building any of it; a step is built on
> only when its result is read and I say it holds, and its bar is set by
> me before it runs. Start with V1 (the benchmark and its judge) and, if
> I agree, V0 alongside it. First, without running anything: tell me in
> a few lines what V1 will do, what it will cost, and the bar you
> propose, and wait for my answer. Keep every reader blind, score with a
> fresh strict matcher, keep each step's work in
> `next-plugin/validation/V<n>-<name>/`, and put anything that quotes my projects (code,
> plan text, tables, cold reads, probes, data) in the audit repository,
> never in this public one; summaries (names, scores, costs) may stay.
