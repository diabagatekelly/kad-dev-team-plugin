# Open work

Slice 4 (refresh on demand, the first project's pull request #92) ran on
2026-11-18 on kad 0.17.0, the first slice at the `light` cadence, and was
reviewed the same day with the comment round on #72:
`~/.claude/kad-audit/repo/personal-finance-tracker-3-slice-4/plugin-review/2026-11-18-slice-4-review.md`,
with the cold read, the mutation pass, cost by role and the test measures
beside it. Finding numbers below (`F<n>`) are that review's.

0.17.0 did what it was built for: the loop took 3 h 45 m against 7 h 35 m,
its mutation pass 12 m 45 s against 2 h 54 m, no gate failed on lint,
format or a count, fixers wrote 17% of the added lines against 38%,
$89.90. What did not move is the code: the cold read's scores are the
same for the third review running (4 / 3 / 4 / 4 / 3 / 3), each slice
ships four or five bugs in its new code at the edges of what the bank
does, the tests are 3.4 times the source and rising, and a fix costs a
slice (the pull request is 7,002 added lines: 3,753 of planning and
records, 2,450 of tests, 573 of source).

This list has three parts. Part 1 is the approved fixes: the scripts
are built, the skill changes parked. Part 2 is the order agreed with the
owner on 2026-11-18: keep planning, try the build a different way, and
compare the two on the same slice of a new project. Part 3 is what is
left of the review's findings, for the owner to place.
The lists before this one are in `docs/todo-archive.md`.

## The owner's decisions, 2026-11-18

1. **The review's four proposals are taken** ("Ok on all proposed"): its
   code findings posted on #92 as comments (done, six); `light` is not
   the default until the two `rounds_record.py` defects are fixed and the
   slice review's fixes under `light` go to a fresh fixer (the resumed
   builders regressed 7 of 22, 32%, against the cadence's own bar of
   25%); the first batch of fixes is built (part 1); the audit repository
   committed and pushed (done).
2. **The owner's concerns, in their words**: "a bit bummed out we're not
   seeing improvement on some of the metrics"; "we keep going down rabbit
   holes that spin out new user stories, which end up being huge PRs,
   when ideally they should be small fixes"; "I am concerned by the
   amount of tests"; and whether the plugin writes worse code than a
   less heavy-handed approach would. Part 2 is the answer proposed to
   these; the owner asked for it as a list ("Yes go ahead and make the
   list").
3. **Planning is kept; the build and the tests are tried a radically
   different way** (the owner: "When it comes to tests and actually
   writing code, that's where we might want to take a radically
   different approach"), on a new fourth project started from scratch
   where slice 1's planning and building are compared side by side. The
   order of part 2 was put to the owner and taken ("Go ahead"): fix only
   what both arms share, park the heavy arm's build-side changes, build
   the light arm as a mode, plan once and build twice, the bar written
   first, the loser's path deleted.
4. **Planning documents stay in the project's repository**, in their
   own pull request before the build; the loop's records do not (my
   answer to the owner's question; step 2, P4 and P5).

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

## Part 1: approved, built first

### 1a. Scripts, no skill text: built 2026-11-18 on `part1a-scripts`, script tests green, not pushed

What each script's change makes stale, by `affected_cases.py`:
`rounds_record.py` 16 cases, `validation_gate.py` 20, `screen_check.py`
16, 42 in all since they overlap; `cost_by_role.py` and
`orchestrator_log_check.py` none (tools). The
deferred items of #67's external review ride with the same scripts, as
agreed then.

- [x] **S1. `rounds_record.py`: a line outside the file is not
  pre-existing** (F2). A round 1 reviewer cited diff positions (line 305
  of a 139-line file) and `classify` filed two regressions as
  pre-existing; they became issues #89 and #90 after being fixed. A
  location past the end of its file at the fix's head is an error the
  recorder reports, and the finding is classed by its file alone
  (regression when the fix changed the file). Test: the slice 4 shape.
- [x] **S2. `rounds_record.py`: a fix and a decline are recorded** (F3).
  All 79 rows of slice 4 have `fix` and `fixer` empty, so a round 0
  finding a fixer declined has no class and `--standing` cannot list it:
  a confirmed High left the count that way (F1). A `--fixed <sha>` and a
  `--declined <reason>` per finding, and `--standing` lists what was
  neither. Test: a declined High is standing.
- [x] **S3. `validation_gate.py`: the shell-edit count** (F7). On a fix
  gate, count only writes the `--agent` transcript made (the catch-all
  runs over the agent's own commits, not `base..HEAD`); a shell write
  whose result is a permission denial is not counted. Slice 4's lines
  add up to 22; 3 ran. Tests on transcript fixtures.
- [x] **S4. `validation_gate.py`: name the failing test** (F16). "suite
  exit 1, summary fail count 1" cost two suite runs; print the first
  failing names from the runner's output.
- [x] **S5. `validation_gate.py`: the two deferred items of #67**
  (`capture_file` narrowed to the capture's two files; the rename map
  read from the chunk's section).
- [x] **S6. `screen_check.py`: a capture of another size** (F15). 27 of
  28 changed states read "100% of pixels" with no difference image
  because the page grew 18 px. Compare over the shared area, report the
  size change beside the percentage, write the difference image. Its
  verdict says "not captured" for a listed state that failed, not "not
  listed". With the deferred patch of #67
  (`~/kad-gate-0170/screen-check-deferred.patch`).
- [x] **S7. `cost_by_role.py`: "Slice 4 review: security" is a
  reviewer** (F13), "second fixer" and "screen captures" are fixers.
- [x] **S8. `orchestrator_log_check.py`: four misreads of the slice 4
  log** (F14): a cadence changed under B; `reviewers tq co ar se re ac`;
  `r1 … ; r2 fix` after `fixes builders`; checks green on the
  `baselines` commit of the same line. And the "0.7.0 loop" label.

### 1b. Parked until the comparison is read (part 2, step 6)

These change the build side of the loop as it is today, which the
comparison may retire. None is built or gated before its result. The
heavy arm of the comparison runs as 0.17.0 does, with `light` named in
the owner's message.

- [ ] **G1. The cadence is read from a standing file** (F19).
  `autopilot.md` gains a `cadence` line the owner sets once; the A step
  takes it and names it in the first line of its report.
- [ ] **G2. Under `light`, the slice review's fixes go to one fresh
  fixer per round**, not to the resumed builders (7 of 22 regressed).
- [ ] **G3. The builder's pre-commit run covers what the gate fails on**
  (F20: Done-when names, changed-line coverage, scope), with F21 (a
  route in backticks read as a test name) and F22 (the module list from
  the planner's report).
- [ ] **G4. The wording that now trails the scripts of 1a**: the fix
  step calls `rounds_record.py --resolve` after each fixer (until it
  does, S2 changes nothing in a run); the screens verdict's two new
  forms in `delivery` and the orchestrator's word-for-word lines;
  `--standing` lists declined findings; the shell-edit count's meaning
  in `chunk-runner` and the orchestrator; a re-reviewer cites file line
  numbers, never positions in a diff; the D line's template for the
  light form the log check now accepts. Whichever arm wins needs the
  `--resolve` call and the verdict forms: those two are built with
  step 3 or step 6, not dropped.

- [ ] **Deferred from the external review of #68** (2026-11-18; each
  with the next change to the same script, since a change to
  `screen_check.py` stales 16 cases):
  - `screen_check.py`: when one image is wider and the other taller, the
    corner neither has is counted as changed and drawn blue (the capture's
    width is fixed, so no real run reaches it).
  - `rounds_record.py --resolve`: a declined title that two reviewers'
    reports of one round share exactly is refused, not resolved for both
    (with G4, which is where the fix step first calls `--resolve`).

## Part 2: the order agreed with the owner, 2026-11-18

The owner keeps the planning side and wants the build and the tests
tried a radically different way, measured side by side on the same
problem, on a new project started from scratch (a fourth
personal-finance-tracker). Nothing on the build side of today's loop is
improved before that result.

### Step 1. What both arms share: the instruments

- [ ] Part 1a's 42 stale cases, one run each (`gate.sh --stale`), the
  loop states recorded, the write-up in `evals/README.md`, the pull
  request. The owner starts the pass.

### Step 2. Planning (kept whichever arm wins)

- [ ] **P1. A domain model, once, before slicing.** The dead ends of
  slices 1, 3 and 4 are one unanswered question: what states can a bank
  connection be in, how is each entered, what can the user do in each,
  and which are deliberately unsupported. A new stage after the scope
  map: one document per external system or long-lived entity, a state
  table, read by `vertical-slicing`, `architecture-design` and
  `reliability-requirements`, and held by the readiness check ("every
  state the slice can leave a thing in has a way out or is listed as
  unsupported"). A new skill and its cases.
- [ ] **P2. The breadth of a slice is the owner's.** `vertical-slicing`
  offers the thinnest cut first and asks when it recommends more than
  it; the slice file carries a size line (criteria count, expected
  chunks), and over a threshold the owner sets it is split or
  confirmed.
- [ ] **P3. Fewer, sharper criteria.** Slice 4 had 35 for one button,
  and each became a test. The security, reliability and accessibility
  stages add a criterion only for a behaviour a user or an operator
  could observe going wrong; wording, logging detail and announcement
  phrasing are design notes, not criteria. The measure is the count per
  slice on the size line of P2.
- [ ] **P4. Planning lands as its own pull request, before the build.**
  The documents (370 lines on slice 4) and the mockups (1,114) are
  merged first, which is also where the owner approves the plan before
  build money is spent; the build's pull request is then source, tests
  and screens (about 3,200 lines on slice 4, not 7,002).
- [ ] **P5. The loop's records leave the project's repository.**
  Reviewer reports, gate outputs and the findings file (2,167 lines on
  slice 4) go to the audit repository, linked from the body. The
  orchestrator log moves with them only once the orchestrator reads it
  from there: the next session finds the flow's place in it. Built with
  the winner (step 6); for the comparison both arms write records as
  today.

### Step 3. The light arm, as a mode of this plugin

Not a second plugin: it reuses the gate, the mutation pass, the cold
read, the criteria walk, the screen-change check and delivery. New is
only the build and what gets fixed.

- [ ] **L1. One builder for the slice**, on the strongest model, given
  the slice, the design, the domain model and the criteria. No chunk
  plan, no runner, no per-chunk agents. It commits in steps of its own
  choosing.
- [ ] **L2. One light test rule**: each criterion held by one test at
  the level that reaches it (the running app where it can), written
  first and seen failing; a module test only for a branch that test
  cannot reach; exact wording held in one table per message module.
- [ ] **L3. The mechanical checks, unchanged**: the gate with every
  check, the mutation pass on the changed lines, the cold read by
  execution, the criteria walk for a slice with a screen, CI and the
  screen-change check at delivery.
- [ ] **L4. Only what was confirmed gets fixed**: a failing check, a
  surviving break the builder agrees is real, a bug the cold read
  reproduced, a criterion the walk failed. One fresh fixer, the gate,
  and the cold read's probes run again.
- [ ] **L5. One combined review, reported and not fixed**: its findings
  go to the pull request's body by severity, for the owner. A Critical
  or High it raises is verified by execution first and fixed under L4
  if confirmed.
- [ ] **L6. Cases** for the mode: the A step takes it from the standing
  file or the message; the builder's test rule with a known-bad
  reference; a finding that was not confirmed is not sent to a fixer.

### Step 4. The comparison, on the new project

- [ ] **C1. Slice 1 planned once**, with step 2's planning. The domain
  model is checked against what the third project met: a login that
  lapses, a bank whose login can never be restarted, accounts added
  after the connect, a pending charge that posts. If the model does not
  name these before any code exists, P1 is not done.
- [ ] **C2. Built twice from the planning commit**, one branch per arm:
  the heavy arm as 0.17.0 `light`, the light arm as step 3. Same
  machine, same fence, neither sees the other's branch.
- [ ] **C3. Measured the same way**: `evals/tools/cold_read.md` and a
  hand-written mutation pass on each (the same mutants where the code
  allows, written per arm where it does not), cost by role, wall clock,
  the owner's questions and stops, added lines of source and of test,
  the test measures, findings and regressions from the sidecar.

### Step 5. The bar, set before the run

The light arm replaces the heavy one when all four hold on slice 1:

1. the cold read's six scores add up to no less than the heavy arm's,
   and no single area is lower by more than one;
2. the mutation kill rate over the slice's files is within five points;
3. no confirmed Critical or High stands in it that the heavy arm does
   not also have;
4. its cost and its wall clock are each at most half.

If 1 to 3 hold and 4 does not, or the scores differ by one point either
way, slice 2 is built both ways before anything is deleted. One slice
is one sample.

### Step 6. After the result

- [ ] The winner's build path is kept and the other is deleted, with
  its cases (two paths would double every gate).
- [ ] If the heavy arm stays: 1b's G1 to G3, and its test weight: one
  level per behaviour in `tdd-implementation-lite`, a redundancy lens
  in `test-quality-review` (a behaviour held at two levels, exact prose
  outside the message table, helpers rewritten across files), the
  test-to-source ratio on the C and D lines.
- [ ] Either way: G4's two items, P5, and **the fix lane**: an issue
  that changes no requirement and no design decision runs no planning
  spine: one builder with the issue and the code, the mechanical
  checks, a pull request under a size the owner sets (proposed: 300
  added lines of source and test); anything that needs a decision
  leaves the lane. On the third project #33 was 5,628 lines and #14
  9,963, and 53 issues are open because fixing one costs a slice.

Left out on purpose: paying down the complexity ratchet's 74 frozen
violations (it would make fixes larger).

## Part 3: the rest of the review's findings, to be placed

Not in parts 1 or 2; each is small. Grouped by where it would be built.

- **The orchestrator at D and E**: a High a fixer declines gets the
  verify round or stands (F1, the rule exists; S2 makes the count
  right); `needs-decision` against "no reviewer restates an accepted
  deferral" (F4, two skills disagree); the Definition of Done's comment
  path cut short (F5); a gate that fails after the fix round has no
  step (F10); a handed-on finding has no owner (F26); the cap on
  mutants is not on the D line (F31); the E line's two sentences
  disagree (F33); issues filed before the pull request exists (F12);
  CI rounds and triage verdicts are not in the sidecar (F11).
- **Screens**: the capture code cannot be run before CI, and a
  server-HTML check is not named (F24); `BASELINES OWED` is adopted
  with nobody looking (F25).
- **The comment round**: no regressions round after its fixer (F27);
  no tracker state for "High, decided: later" (F28); a records-only or
  planning-only push gets the full CI watch (F29).
- **Builders and runners**: the map consult skipped by two builders and
  source before a test by one (F6); the shell for break and restore
  (F8); a hung run found by one builder is not handed to the next
  (F30); each runner rebuilds the gate command (F32); turn counts are
  `?` because the harness has no `maxTurns` (F18).
- **Carried from 0.17.0**: C4's log bullet (the owner: not fixed, watch
  it; slice 4's log check raised nothing on it); C9 has no case.

## Not the plugin's

On the first project: pull request #92 to merge or fix first (six
review comments of 2026-11-18; the suite goes red on 1 December); #78
(High, the owner: later, in set entry 5); #89 and #90 were fixed before
they were filed and can be closed; 53 open issues.
