# Open work

Slice 3 ran on 2026-11-17 as the first project's issue #14 (its pull
request #72, kad 0.16.1) and was reviewed the same day:
`~/.claude/kad-audit/repo/personal-finance-tracker-3-slice-3/plugin-review/2026-11-17-slice-3-review.md`,
with the cold read, the mutation pass, cost by role and the test measures
beside it. The code changes of 0.15 and 0.16 held (fixers wrote 38% of
the added lines against 58% and 52%, no Critical or High standing,
$105.94). The run's time and the owner's attention did not: 7 h 35 m by
the clock with about 4 h of waiting, three directions written into the
project's log in one day (its entries 109, 110, 111), and a dead end in
the slice's own code that six reviewers, the walk and the loop's cold
read passed.

This list is 0.17.0. It is grouped so each file group goes through the
gate once. Nothing here is built except where a line says so. The lists
before it are in `docs/todo-archive.md`.

## The owner's decisions, 2026-11-17

1. **A design or technical question that has a recommended option is not
   asked**: the recommendation is taken and logged with the alternatives,
   so the owner can overturn it afterwards. Product requirements (what the
   owner wants) and accepted risks (an advisory, a weakened check, a
   secret) stay the owner's. On 2026-11-17 the owner took the first option
   on 11 of 13 questions; 6 of the 13 were of this kind.
2. **The next slice runs `light`**, and **the per-chunk smoke run is
   dropped from it**: the browser is left to the slice review's walk. On
   slice 3 the smoke run was the dearest per-chunk check ($10.65, seven
   runs) and found nothing.
3. **H1's proposals are built** ("Why fixers regress", `evals/README.md`).
   Slice 3 repeated H1's finding: 5 of 7 review-fix rounds introduced a
   new problem and each needed a second round; 5 of the 8 distinct
   regressions were a test the fixer wrote or rewrote that cannot fail or
   checks less than its name.
4. **The owner's comments in the audit log are addressed**: the loop
   never stops for a mechanical failure (entry 109); the mutation pass's
   time (110); no artifact downloaded by hand (111); a failed capture
   reported as one, Chromium in the fence (the points-of-failure note of
   2026-11-17, slice 1's folder).

5. **From the review of this list, 2026-11-17:** `light` is asked for by
   the owner in the slice's message for now, not the default (C3); the
   test-quality reviewer getting the mutation report late is accepted
   (C1); a hung mutant counts as caught and is listed apart (A1); **one
   pull request for groups A to D, all of it before the next slice**;
   the review is pushed to the audit repository and its project findings
   are seven comments on the first project's pull request #72 (done).

## Rules for every gated pull request

From what #62 cost, and the owner's answers of 2026-11-16:

- A new case runs once and its trace is read before any three-run pass.
  Its first failures are read before the grader is believed.
- Skill wording is tried on one or two cases at single runs.
- **Three runs where a bar can move, one run elsewhere** (the owner,
  2026-11-16, on PR 1; it replaces "the full three-run gate"). At three
  runs, once, at the end: every new case, every case whose graders,
  prompt or state changed in purpose, every case of a skill whose text
  the change rewrote most (PR 1: all of `chunk-runner`'s), and every
  known-bad reference. Every other case the change reaches runs once
  against the bar it has (`gate.sh --stale`), and the gate re-runs at
  three any that lands under its bar. What this gives up, knowingly: a
  miss that happens one run in three passes a single run two times in
  three, so an occasional new miss in an unchanged case can go unseen
  until a later change.
- Bars are recorded (`record_thresholds.py --gate-only`) from three-run
  results only, **for the three-run cases by name**, never for the whole
  affected list: the tool takes each case's newest result, and a one-run
  result must not become a bar. Then `--stale` once more.
- **No cost-per-pass or re-run-rate figure.** The write-up gives the
  three-run counts, the bars that moved, which cases ran once, and the
  gate's total cost from the result files.
- A rule a skill states in several places survives the removal of one: a
  known-bad reference removes every place.
- The code commit is pushed alone for the external reviewer (its limit is
  300,000 characters); the evidence, bars and generated tables follow.
  A fix it asks for that would stale a batch of cases is weighed first,
  and deferred to that group's next pull request unless it is a defect.
- `docs/flow-map.html` is updated in the same pull request as any change
  to a stage, a launch or a script.

## Before the gate pass: done 2026-11-18, the pass not started

The cases are written and each ran once with its trace read; the new
wording was tried on the existing cases of every changed skill. 54 single
runs, $25.41 by the result files. No bar recorded, nothing pushed. `[~]`
below now means: tried on a case at one run, not gated.

**New cases (10), all tool-judged.** Held on its one run, by the trace,
unless said:

- B1 `tdd-implementation-lite-checks-before-commit`, with a known-bad
  reference (one run of the reference: its three graders fail).
- B2, B4 `tdd-implementation-lite-fix-test-renamed`. The run's tree was
  put through the real gate by hand: PASS with the declared rename,
  `FAIL tests` with the declaration taken out.
- C2 `chunk-runner-check-fail-second-fixer`, `chunk-runner-suite-fail-ends`.
- C3 `chunk-runner-light-no-review`.
- C4, D4 (design) `orchestrator-recommended-not-asked`.
- D1, D4 `reliability-requirements-refusal-phase1` and `-phase2` (a
  chain: phase 2 resumes phase 1's frozen history).
- D2 `cold-read-refusal-no-exit` (held after a rewording, below).
- D3 `reliability-review-criterion-no-exit`.

**Adapted, not added.** C1: `orchestrator-mutation-before-review` (the
pass started in the background with its bounds) and
`orchestrator-slice-review-launches` (the pass before any reviewer, the
test-quality reviewer after the others). C6:
`orchestrator-delivery-foreground` (the E line in the log the remote
holds). C4: `orchestrator-route-design`'s judge. B6:
`orchestrator-chunk-runner-handback`, `tdd-implementation-lite-one-chunk`.

**Wording changed after a trace, three places.** `cold-read`: two readers
of two ran three doors after the refusal and never placed the hold
again; the list is now the whole app's and names four doors. Next run:
all four. `tdd-implementation-lite` (B1): on a project where `tsc` is
not installed the builder handed its chunk back uncommitted; a `FAIL`
that is not the builder's no longer holds the commit and is said on the
hand-back. Next run: committed, and said. And the report's `Commit` and
`Fix` lines say `this commit`, literally (the owner, 2026-11-18): a
fixer had written a placeholder, committed, then put the hash in,
leaving the report modified and in no commit. Next run: the line
written before the commit, nothing edited after.

**Seen in a trace and not fixed** (none is in the 0.17.0 text):

- `delivery-ci-red-not-done`: the stand-in's canned CI log does not
  match the tree (other card numbers, a line past the file's end), and
  one run declined to brief a fixer on it. A fixture defect; its two
  judges have failed 5 and 2 of 20 runs before.
- Both fix cases skipped the four final reviewers as "my call" (the
  named-fix bar already has that grader at 0.33).
- C1: after launching the reviewers the orchestrator read the pass's
  output file once, which the skill calls a poll.
- A resumed phase cannot resolve the skill's own directory (the frozen
  history writes it as `<plugin-root>`): the D4 phase's prompt says to
  invoke the skill again for it.
- C4's other half (a question that is the owner's is still asked) is
  held by `orchestrator-route-reliability` and
  `orchestrator-autopilot-question`, not inside one flow with a taken
  decision: on the design row it showed in two of four runs (the
  slice's scope, a risk to accept) and is not graded there.

**Two judges turned into tool checks** (the owner left it to me,
2026-11-18), each tried on the kept outputs of its past runs.
`architecture-design-payfine-phase2`'s `decisions-show-approval` had
failed 20 of 26 runs: read against those 26 documents, one has a
decision with no approval recorded, and 11 say it once for the whole
section, which the judge did not credit. The check fails that one and
passes 25. `technology-bootstrap-phase2`'s
`asks-only-what-the-first-test-forces` had failed 8 of 28, the last two
on right replies: the check reads that no database, host, container, CI,
monitoring or auth product is named before the section that leaves them
open; all 28 kept replies pass. It does not read a choice made without a
product's name. Left as judges, and seen failing once each on a right
output: `technology-bootstrap-phase2`'s `recommends-ui-framework-and-waits`
and `recommends-the-built-in-default-set-once`.

**For the pass.** 112 cases affected (`affected_cases.py --base main`).
At three runs: the 10 new cases; the 37 known-bad references; the cases
changed in purpose (`orchestrator-mutation-before-review`,
`orchestrator-slice-review-launches`, `orchestrator-delivery-foreground`,
`orchestrator-route-design`, `orchestrator-chunk-runner-handback`,
`tdd-implementation-lite-one-chunk`, `technology-bootstrap-phase2`); the
8 cases whose frozen history was captured again (the phase 2 and 3 cases
of reliability-requirements, architecture-design and
technology-bootstrap); `architecture-design-payfine-phase2` (its grader); and the rest of
`chunk-runner`'s and `tdd-implementation-lite`'s cases (the owner,
2026-11-18: both count as mostly rewritten). Everything else once, with `--stale`. After it:
`affected_cases.py --record-scripts`, the bars by name, the README
write-up. A wording change to reliability-requirements,
architecture-design, technology-bootstrap or the orchestrator stales the
histories again (`history_stale.py`).

## Group A: scripts, no model (script tests only)

Each is a defect or a gap in a script, with a script test. A case is
stale only for the scripts it ran: say how many before the gate runs.

- [x] **A1 `mutation_pass.py`** (entry 110: 2 h 54 m for 40 mutants).
  Built 2026-11-17 (27 script tests). Timed on the first project at
  `9d225c4`, the loop's own base and 40 operator mutants: **13 minutes**
  (baseline 36 s, a caught mutant 17 s at the median, 38 caught, 2
  survived, none hung), against 2 h 54 m in the loop. Also: a baseline
  that fails is tried three times and the tests that failed are named as
  unsteady and never count as a catch (the project has one); `changed`
  leaves out configuration and capture files. The pass: a mutant's suite is ended after three times the
  baseline's own time (at least 60 s; the default was 1,800 s, and three
  hung mutants cost 84 minutes); the command runs in its own process
  group and a timeout ends the whole group (36 orphaned test processes
  were left); a hang is `HUNG`, counted as caught and listed apart; a
  test node reports as `cancelled` is a catch (it was read as a runner
  error, and its name was listed beside other tests' counts);
  `--first-failure` ends a mutant's suite at its first failing test;
  `--budget` lists what was not started as not run; each line shows
  `<i>/<n>` and the seconds. Not built: resuming a stopped pass. Not
  established: why the loop's mutants took 2½ to 3½ minutes each where
  the same script took 50 s here (the fence is not it: 53 s inside, 41 s
  outside).
- [x] **A2 `cost_by_role.py --log`** totals every chunk-loop entry of the
  log ($422.10 on slice 3's E line; the slice was $105.94). It takes the
  last chunk-loop entry's sessions only.
- [x] **A3 `screen_check.py`**: `compare` reads `capture-errors.json` and
  the full state list, and a state with no capture is `MISSING` whether
  or not it has a baseline (`FAIL` outranks `OWED`); `adopt` refuses
  while a driven state has no capture. Two states that threw were one
  step from being adopted as 23 of 25.
- [x] **A4 `audit_sync.py`** refused a whole copy for an expired signed
  download link in a transcript. A signed link is redacted and the copy
  goes on; a refusal is kept for what `source_scan.py` calls a secret.
- [x] **A5 `rounds_record.py`** (H1, cause 1): a round-1 finding is a
  regression only when the fix wrote the line's content; a line it moved
  is `pre-existing`; a report from a reviewer with no round-0 report in
  the scope is `first-seen`.
- [x] **A6 `validation_gate.py`**: reads `renamed <old> → <new>` on a
  `Fix` line so a fix may rename a plan's test (H1, cause 4: chunk 1's
  gate fixer restored a name the next review then faulted); exempts the
  capture file E.2's own fixer writes from changed-line coverage; and a
  `--checks-only` mode a builder can run before it commits (B1).
- [x] **A7 `orchestrator_log_check.py`** reads the 0.17 log: the `cold`
  field where `stranger` was, `(reg, pre, first)`, `smoke none` and
  `review none` under `light`, and says an owner's direction written as
  an entry splits a loop. On slice 3's log it also finds what the review
  missed: two bold D lines (the mutation result written as its own), a
  D line with `DoD` where `done` belongs, and an E line whose green
  commit is not the pushed one.
- [x] **A8 `bin/kad`** (entry 111; the owner, 2026-11-17: the narrow
  hosts, and the download moved outside the fence only if that fails).
  It did not fail: GitHub publishes its Actions storage hosts by name
  (`gh api meta`, 140 of them), so the fence allows each name and the
  results receiver, never `*.blob.core.windows.net`; the approved set
  records the pattern, so the owner is asked once. A project with
  `screens/package.json` also gets Playwright's two download hosts and
  `PLAYWRIGHT_BROWSERS_PATH` inside the project, excluded from git.
  Tried for real on the first project's last screens run: the artifact
  download fails in the old fence and works in the new one. `gh run view
  --log` also needs `XDG_CACHE_HOME` on a writable folder (C11 says so in
  `delivery`). Not tried: whether the downloaded Chromium starts inside
  the fence.
- [x] **A9 `ci-pipeline`** section 3 adds the copied files to the
  project's formatter and linter ignore files, and its workflow writes
  the capture's state list first (for A3). Shipping `capture.mjs` in
  Prettier's defaults was dropped: the first project's own width is 140,
  so a default-formatted copy fails there too. `ci-pipeline`'s cases are
  stale by this text and run with group C's.

## Group B: `tdd-implementation-lite` (builders and fixers), one gated change

B1 to B5 are written in the skill (2026-11-17) and **not yet tried on a
case or gated**: `[~]` below. B6 waits for group C, since the runner and
the log read the same line.

- [~] **B1 The gate's checks run before the commit.** A builder and a
  fixer run the commands of `gate-checks.json` (A6's `--checks-only`)
  and report the counts. On slice 3 a gate fixer ran on 5 of 6 chunks
  (461 added lines, 16% of everything added; chunk 6's gate fix was
  larger than its build), and 5 of 7 review fixes failed the gate, every
  one but one by a count one or two over its baseline.
- [~] **B2 Each test a fix adds or rewrites is shown failing** (break the
  line the fix wrote, see that test fail, restore; the `Fix` line names
  the test and the break), and a rewritten test keeps every assertion it
  had or its `Fix` line names the one dropped and why (H1, cause 5).
- [~] **B3 A finding's suggested fix is the reviewer's guess**; the
  finding is its "What's happening" (H1, the pattern under cause 5).
- [~] **B4 A test whose behaviour a fix changes is renamed**, the rename
  on the `Fix` line (H1, cause 4; with A6).
- [~] **B5 The plan path:** captures and baselines are delivery's, not a
  chunk's (plan check 1 failed on this and a second planner ran).
- [~] **B6 Shell edits and turns are counted, not reported**: builders
  reported 21 of 88 shell edits, and two chunks' turn counts were `?`.
  The report's line is dropped and the count the runner already takes is
  the only one.

## Group C: the orchestrator, the chunk runner, delivery, one gated change

C1 to C11 and B6 are written in the skills (2026-11-17) and **not yet
tried on a case or gated**: `[~]` below. One change from the list as
reviewed: under C1 the test-quality reviewer starts when the mutation
pass ends (at most 15 minutes after the others) and so still reads its
report at round 0, where a survivor is fixed; getting it at round 1
would have classed every survivor as pre-existing, never fixed.

- [~] **C1 The mutation pass at D** runs beside the reviewers (it works
  in its own clone), with `--first-failure`, the default timeout and a
  budget, and its progress in a file the owner can be shown. The
  reviewers no longer wait for it; the test-quality reviewer is handed
  the report when it lands, or reads it at round 1.
- [~] **C2 A gate failure that is only lint, format or a count check gets
  a second fixer** before anything stops (entry 109; chunk 2 stopped the
  loop 25 minutes for an unused import). The stop is kept for a failing
  test or typecheck after its fixer.
- [~] **C3 `light` without the per-chunk smoke run** (decision 2): per
  chunk, build and gate only. How the next slice is told to run `light`
  stays the owner's word in the message; whether `light` becomes the
  default is decided after that slice.
- [~] **C4 Recommended questions are not asked** (decision 1): in the
  orchestrator's own questions and in every skill that asks one (the
  design skills, `technology-bootstrap`'s gate check set, `ci-pipeline`'s
  state list). Each is logged `taken as recommended: <what>, over
  <alternatives>`.
- [~] **C5 `autopilot.md` names what is never taken alone**: a changed
  requirement, an accepted risk (the loop tried to record an advisory as
  accepted on its own and the harness refused the launch), deleted or
  rewritten committed work, a push while red, a secret.
- [~] **C6 The log's last lines are in the last pushed commit**: the E
  line is written before the final records commit (the third run that
  left the tree dirty; the first project's pull request #48 was this).
- [~] **C7 After the context is summarised the skill is invoked again by
  name**, not read by path with the shell (the owner asked why a skill
  "in a different repo" was being read).
- [~] **C8 An owner's direction in the middle of a loop** is a bullet
  under the loop's entry, not a new entry that splits its A to E lines.
- [~] **C9 The format check, and every command CI runs, is a gate check**:
  `technology-bootstrap`'s set includes them (reviewers raised format
  failures as High on two chunks; the first project's pull request #57
  went red on it).
- [~] **C10 The wiring fixer at A.5 runs the project's audit command**,
  and a tool that brings an advisory is put to the owner with the set
  (`knip` brought one; CI went red at delivery).
- [~] **C11 `delivery`'s screens check** reads `capture: <n> of <n>`
  before `BASELINES OWED` is treated as clean (with A3), and fetches
  logs and artifacts itself (with A8).
- [ ] **C12 The runner's wait** (not built, and no rule proposed): one
  runner of nine handed back while its smoke agent ran. The rule is
  already in the runner's text three ways and the stall rule recovered
  it for one relaunch; under `light` the runner launches one agent, so
  the case cannot arise there. Whether the harness can refuse a
  hand-back while a child runs is not known.

## Group D: planning and review skills, one gated change

D1 to D4 are written in the skills (2026-11-17) and **not yet tried on a
case or gated**: `[~]` below.

- [~] **D1 `reliability-requirements`: every refusal says whether it can
  be permanent, and what the person can still do.** That is a criterion,
  or an "out for now" that names what the person is left with. Slice 3's
  R36 made a dead end correct: a marked bank whose login Plaid refuses to
  restart can never be logged in again, tried again, or connected again.
- [~] **D2 `cold-read`: after any action that is refused, every remaining
  action on that state is listed and run**; a state where all are closed
  is a finding. The loop's reader ran the refusal and one of the four
  closed doors and reported the wording.
- [~] **D3 `reliability-review` at the slice review** reports a criterion
  that leaves a state with no exit, even when the code meets it.
- [~] **D4 The planning skills check their own readiness**:
  `reliability-requirements` (numbers on waits, the unusable-reply row)
  and `architecture-design` (criteria homed, failure paths homed) run
  `readiness_check.py` for their own checks before saving. The same two
  checks failed after planning on three runs in a row.

## Then: the next slice on the first project, under `light`

Measured against slice 3: the loop's wall clock and how much of it is
waiting, the owner's questions and stops, gate fixers per chunk, fix
rounds that need a second round, the mutation pass's time, the cold
read's scores and what it finds that the loop did not.

Before it, on the first project (not the plugin's): pull request #72 to
merge or fix first (the cold read's first bug, the dead end, is in it,
with the review's seven comments of 2026-11-17); the log's uncommitted E
line; issues #73 to #77.

## Proposed cases (the review's list)

Written 2026-11-18: see "Before the gate pass" above. Script tests, no
model: A1 (a suite that hangs, a cancelled test), A2, A3 (a first run
with a state that throws), A4.

## Not the plugin's

On the first project: issues #43 to #47 and #49 to #56, and pull request
#48 (records only) to merge or close.
