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

This list has three parts. Part 1 is approved and is built first. Part 2
is written for the owner to review before anything in it is built.
Part 3 is what is left of the review's findings, for the owner to place.
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

### 1a. Scripts, no skill text (script tests; the stale cases run once)

What each script's change makes stale, by `affected_cases.py`:
`rounds_record.py` 16 cases, `validation_gate.py` 20, `screen_check.py`
16; `cost_by_role.py` and `orchestrator_log_check.py` none (tools). The
deferred items of #67's external review ride with the same scripts, as
agreed then.

- [ ] **S1. `rounds_record.py`: a line outside the file is not
  pre-existing** (F2). A round 1 reviewer cited diff positions (line 305
  of a 139-line file) and `classify` filed two regressions as
  pre-existing; they became issues #89 and #90 after being fixed. A
  location past the end of its file at the fix's head is an error the
  recorder reports, and the finding is classed by its file alone
  (regression when the fix changed the file). Test: the slice 4 shape.
- [ ] **S2. `rounds_record.py`: a fix and a decline are recorded** (F3).
  All 79 rows of slice 4 have `fix` and `fixer` empty, so a round 0
  finding a fixer declined has no class and `--standing` cannot list it:
  a confirmed High left the count that way (F1). A `--fixed <sha>` and a
  `--declined <reason>` per finding, and `--standing` lists what was
  neither. Test: a declined High is standing.
- [ ] **S3. `validation_gate.py`: the shell-edit count** (F7). On a fix
  gate, count only writes the `--agent` transcript made (the catch-all
  runs over the agent's own commits, not `base..HEAD`); a shell write
  whose result is a permission denial is not counted. Slice 4's lines
  add up to 22; 3 ran. Tests on transcript fixtures.
- [ ] **S4. `validation_gate.py`: name the failing test** (F16). "suite
  exit 1, summary fail count 1" cost two suite runs; print the first
  failing names from the runner's output.
- [ ] **S5. `validation_gate.py`: the two deferred items of #67**
  (`capture_file` narrowed to the capture's two files; the rename map
  read from the chunk's section).
- [ ] **S6. `screen_check.py`: a capture of another size** (F15). 27 of
  28 changed states read "100% of pixels" with no difference image
  because the page grew 18 px. Compare over the shared area, report the
  size change beside the percentage, write the difference image. Its
  verdict says "not captured" for a listed state that failed, not "not
  listed". With the deferred patch of #67
  (`~/kad-gate-0170/screen-check-deferred.patch`).
- [ ] **S7. `cost_by_role.py`: "Slice 4 review: security" is a
  reviewer** (F13), "second fixer" and "screen captures" are fixers.
- [ ] **S8. `orchestrator_log_check.py`: four misreads of the slice 4
  log** (F14): a cadence changed under B; `reviewers tq co ar se re ac`;
  `r1 … ; r2 fix` after `fixes builders`; checks green on the
  `baselines` commit of the same line. And the "0.7.0 loop" label.

### 1b. Three skill changes (gated, by the rules above)

- [ ] **G1. The cadence is read from a standing file** (F19, the owner's
  decision 2 of 2026-11-17, which 0.17.0 encoded as a word the owner had
  to say). `autopilot.md` gains a `cadence` line the owner sets once;
  the A step takes it, names the cadence in the first line of its
  report, and a message that names one still wins. One loop-state case,
  tool-judged.
- [ ] **G2. Under `light`, the slice review's fixes go to one fresh
  fixer per round**, not to the resumed builders (decision 1). One case
  (loop state at D with findings across chunks), and the regression
  rate of the next slice is the measure.
- [ ] **G3. The builder's pre-commit run covers what the gate fails on**
  (F20). All four gate fixers of slice 4 were for a Done-when test name,
  changed-line coverage or scope, none of which `--checks-only` runs.
  `--checks-only` takes the chunk's Done-when names and its range and
  runs the name check and the changed-line coverage too;
  `tdd-implementation-lite` says so. One case with a known-bad
  reference. With it, F21 (a route in backticks is read as a test name:
  the plan names tests in `seam "…"` form only) and F22 (the planner's
  report names the directories its chunks touch, and B takes the module
  list from it; slice 4's one stop came from the orchestrator's guess).

## Part 2: proposed, for the owner's review before any of it is built

Seven changes aimed at what the review did not see move: the code's
score, the size of a fix, the amount of test. Each is a proposal of
mine, with what it costs.

- [ ] **Q1. A domain model, once, before slicing.** The dead ends of
  slices 1, 3 and 4 are one unanswered question: what states can a bank
  connection be in, how is each entered, what can the user do in each,
  and which are deliberately unsupported. Slice 1 shipped and a lapsed
  login was unrecoverable (#14, which became slice 3); slice 3's review
  found a bank that can never be restarted (#78); slice 4's own review
  met the same dead end from Refresh; its control found accounts added
  after the connect. `reliability-requirements` lists how a call fails,
  not the life of the thing. A new stage after the scope map (one
  document per external system or long-lived entity: a state table),
  read by `vertical-slicing`, `architecture-design` and
  `reliability-requirements`, and by the readiness check ("every state
  the slice can leave a thing in has a way out or is listed as
  unsupported"). A new skill and its cases; on the first project it is
  written once, late, for Plaid.
- [ ] **Q2. A fix lane.** An issue that changes no requirement and no
  design decision does not run the planning spine: no new planning
  document, one builder with the issue and the code, the gate, one
  combined reviewer, one fix round, a pull request with a size the
  owner sets (proposed: 300 added lines of source and test). Anything
  that needs a decision leaves the lane for the spine. Several issues of
  one module may share a lane run. Today #33 was 5,628 lines and #14
  9,963; 53 issues are open on the first project because fixing one
  costs a slice. Orchestrator routing, a short loop, cases.
- [ ] **Q3. Records out of the slice's pull request.** 54% of #92 is
  planning documents, reviewer reports, gate outputs and the log. The
  planning documents stay (they are the design); the loop's records go
  to the audit repository (or a `records/` branch), with a link in the
  body. Delivery, the runner, `rounds_record.py` paths.
- [ ] **Q4. The breadth of a slice is the owner's.** Slice 4 took
  corrections, withdrawals, pending-to-posted and the month turn in one
  cut, "taken as recommended". `vertical-slicing` offers the thinnest
  cut first and asks when it recommends more than it (scope is not a
  technical question), and the slice file gets a size line (criteria
  count, expected chunks); over a threshold the owner sets it is split
  or confirmed.
- [ ] **Q5. One level per behaviour.** The plan requires a full-app
  test for every criterion and the test-first contract adds module
  tests beside them (56 and 52 of slice 4's 108). `tdd-implementation-
  lite`: the seam test holds the criterion; a module test is written
  only for a branch the seam cannot reach, and is named with that
  branch (the rule the skill already has for fakes). Exact wording is
  held by one table test per message module.
- [ ] **Q6. A redundancy lens in `test-quality-review`.** Its findings
  are all "no test holds X"; none asks whether a test is needed. Add:
  a behaviour held at two levels, exact-prose assertions outside the
  message table, a helper rewritten across files (27 on the first
  project). Reported, not fixed in the round.
- [ ] **Q7. The test-to-source ratio on the C and D lines**, per chunk
  and for the slice, so growth is seen; no cap until Q5 has run once.

Left out on purpose: paying down the complexity ratchet's 74 frozen
violations (it would make fixes larger).

**The control that is missing (my proposal, with Q1 to Q7).** Nothing
measures the plugin against no plugin on a whole piece of work: the
with-and-without pass (E6) was on single skills. One chunk-sized piece
of the first project (an open Medium, and one small criterion) built
twice from the same commit, once through the plugin and once by a bare
session given the issue and "write it test-first, run the checks", each
then read by the same cold read and mutation pass. It answers whether
the weight buys anything, and it is the measure Q2 and Q5 are judged
by.

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
