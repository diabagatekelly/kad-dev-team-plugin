# Open work

One list, ordered by pull request, written 2026-11-16 after kad 0.15.0's
first pull request (#62). Everything finished, with the owner's decisions
and the "done" notes, is in `docs/todo-archive.md` (and the eval suite's
own old list in `docs/todo-archive-evals.md`); the items here keep the
letters and numbers they had there.

**Why it is grouped this way.** What a pull request costs at the eval
gate follows the files it touches, not the number of items it closes: any
change under `skills/orchestrator/` sends that directory's 38 cases back
through the gate, the shared loop fixture 25, a review skill about 17.
#62 cost 626 runs and $231.92 over four usage windows. So the open work is
three gated pull requests, each touching one group of files once, and
nothing is fixed between them that would stale a group twice.

**Order, decided by the owner 2026-11-16:** PR 1 (the loop's fixes), then
PR 3 (the screen-change check) before slice 3; PR 2 (reviews and planning
skills) alongside, before or after the slice, since it changes how
findings are ranked and not what the loop does. Then slice 3.

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

## PR 1: the loop's fixes (0.15.1): done

Pull request #64, 2026-11-16. Every item is built; the counts, what
each fails without, the bars that moved, the cost ($225.78 over 286
runs) and what no case holds are in `evals/README.md`, "The loop's
fixes"; the items as they stood are in `docs/todo-archive.md` under the
same heading. Decided on the way, by the owner: under autopilot the
clock is the only cap; the last-fix review runs once per scope; two
autopilot rounds, then the owner; three runs where a bar can move and
one elsewhere. The two replay cases are dropped.

Left open by it, for the next change to each file group:

- [ ] F2 has no case that fails without its text: the run that left a
  regression as "no third fixer" was not reproduced by removing it.
- [ ] The autopilot round, the last-fix review at D and the autopilot
  question get cases in PR 3; a readiness correction taken without a
  question gets one in PR 2 (both listed there).
- [ ] `chunk-runner-fix-gate-fails` and
  `orchestrator-autopilot-counts-over` carry no known-bad reference
  (eight deletions and the autopilot text each survived).
- [ ] The slice-review state (`slice-review-r0`) has no gate output on
  its last commits, so the orchestrator ran `npm test` into a file of
  its own to have one to hand the reviewers.

## Before slice 3, no gate: why fixers regress

- [ ] H1 **Read why the fixers' regressions happen** (the owner,
  2026-11-16, on choosing two autopilot rounds: "we need to figure out
  how to reduce fixer regressions"). One in four actionable findings has
  been a regression a fixer introduced (incident 19), and every round
  autopilot adds is another fix on a fix. Nothing in the loop reduces
  them: the re-review and the last-fix review find them afterwards, and
  the light cadence (fixes by the chunk's own builder) is one experiment
  on a later slice. From the sidecars and the audit transcripts of the
  runs so far, sort each regression by cause (a neighbouring test or
  caller not read, a finding misread, a batch too large for one fixer, a
  fix that grew past its finding) with counts. No eval runs. Done when:
  the table is in `evals/README.md` with one proposed change per cause
  that has more than a handful, each named with the file group it would
  send through the gate (most likely `tdd-implementation-lite`'s
  handed-back path, its own gated change).

## PR 2: reviews and planning skills (0.15.x)

Files: the six review skills, `skills/map-update`,
`skills/architecture-design`, and case-only edits. About 40 to 45 cases.
Does not block slice 3.

- [ ] B7 **A review reports nothing above Low on a sound module.** On
  2026-11-16: `library-app-catalog-review` 2 of 3, `code-review-catalog`
  2 of 3, `test-quality-review-fines`' `no-false-alarm-exact-tests` 1 of
  3 and `no-false-alarm-fake-ledger` 2 of 3. The cases keep their bar.
  Done when: the four clean-module cases and those two graders pass
  three runs of three.
- [ ] B8 **A serious problem a review reads past is named and handed
  on**: one line at the top (what, where, the severity it appears to
  have, which review owns it), never rated down to fit the review's own
  categories, never ranked among its findings. Every review skill.
  `code-review`'s mocking rule becomes this rule, and
  `leaves-mocking-to-test-quality-review` is rewritten to pass the one
  line (1 of 3 on `code-review-fine-notices-pr`, 0 of 3 on its
  `-via-agent` twin). Done when: a case per review skill with a planted
  out-of-subject problem shows the line, and the mocking judge passes
  three runs of three.
- [ ] B9 **`map-update`'s changes section calls old edges and exports
  new.** The cause is `extract_map.py`'s `parse_prior`, which reads a
  prior row's names only between backticks (the full account is in the
  archive). **The owner, 2026-11-16: both halves.** It reads a plain
  cell too (commas, semicolons, `none`, a dash), and a prior row it
  still cannot read is named in the changes section instead of being
  diffed against nothing. Done when: `pre-existing-flags-not-new` passes
  three runs of three and a test of `extract_map.py` holds a bare-cell
  prior map and an unreadable row.
- [ ] B10 **What E7's gate runs showed**, as settled by the owner
  2026-11-16:
  - the four `-via-agent` twins get the cuts their direct cases got in
    E7, and `library-app-lending-review-via-agent` the corrected ORM
    wording (case-only);
  - the overlay `code-plants/reliability-review/portal-pay/`, which has
    had no case since E7, is deleted;
  - the owner-sheet cases (`architecture-design-`, `screen-design-`,
    `vertical-slicing-`, `requirements-refinement-owner-sheet`) grant
    `Bash`, so the skill can run `source_scan.py describe`; a planning
    skill's data rule is changed only if a case still opens the owner's
    file with the scan available (2 of 3 runs of two of them today);
  - `code-review` is not invoked in `code-review-days-left-pr` (8 of 13
    runs): read why from a trace, then the skill's description or the
    case;
  - `map-update` left the new module untiered one run of three;
  - `requirements-refinement`'s first turn asks what the sources answer
    one run of three;
  - `test-quality-review` calls the designated fake a mocking problem
    (with B7).
- [ ] C3 **The concurrency pass in `architecture-design`**: for a change
  about concurrency or more than one process, the interleavings are
  listed and answered before the decision is final (two starts at once,
  a crash at each step, a stop during each wait, a leftover removed by
  hand, a reused process number). Done when: case
  `architecture-design-concurrency-interleavings` passes.

## PR 3: the screen-change check (0.16.0): done

Pull request #65, 2026-11-16. C1 and the three cases are built; what
each is, its counts, what it fails without, the bars that moved, which
cases ran once and what no case holds are in `evals/README.md`, "The
screen-change check"; the item and the owner's six decisions as they
stood are in `docs/todo-archive.md` under the same heading. Decided on
the way, by the owner: the fixture's screen is the holds desk's notice;
a state's name is its mockup's file stem; the comparison is a copy of
the plugin's script in the project; one fixer at E writes a missing
capture; the threshold is `visual-ux/baselines/screen-check.json`; a
workflow in this repository runs a real browser on the fixture; and the
gate's dependencies are narrowed three ways (`evals/README.md`, "Eval
gate"), which took this pull request's stale list from 71 cases to 25.

Left open by it:

- [ ] The external reviewer's weekly budget was used up when the pull
  request opened: ask for its review (`@sourcery-ai review`) and triage
  it, weighing any fix that stales cases.
- [ ] `evals/loop_states_before.json` is read only while the base has no
  `loop_states.json`: delete it in the first change after the merge.
- [ ] `verify.sh` fails on the `monthly-statement` overlay (a `.ts`
  import path the TypeScript it installs refuses); not this change's.
- [ ] `baselines-adopted-by-the-script` and `autopilot-file-written` do
  not fail with their rule's text removed (the project's copy of the
  script, and the owner's own "yes", carry them).
- [ ] The orchestrator's steps rule is a bet (an edit in one step is not
  run against cases of another). If a miss turns up in a case that was
  not run, `tools/orchestrator_steps.json` is where that case gets the
  step added.

## Then: slice 3

**The test of 0.15 and 0.16: slice 3 on the first project** (reconnect a
lapsed login, its issue #14), which is UI-touching. PR 1 and PR 3 are
done; PR 2 may land before or after. Before the slice starts, on the
first project, from the owner:

- [ ] the installed plugin updated to 0.16.0 (after #65 merges);
- [ ] **the baselines from `main`**, as one small pull request on the
  project: `ci-pipeline`'s screen job (it finds the screen designs and
  writes `screens.yml`, the harness, the script's copy and the threshold
  file), a `screens/states.mjs` that drives the states of slices 1 and 2
  on made-up data (the project's `test/support/test-main.ts` start), one
  CI run (every capture is a first baseline while there is none), the
  artifact adopted with `screen_check.py adopt`, committed, green,
  merged. Which of the 25 mockup states get a capture is the owner's
  call: a state with no capture is not watched. The existing mockups
  live in per-slice folders and are numbered (`02-retrieving`); those
  stems are the state names;
- [ ] the autopilot question answered when slice 3's A step asks it
  (there is no `autopilot.md` on that project yet);
- [ ] H1 (why fixers regress), which is due before the slice. It is the first real run of the
gate checks' wiring and of the cold read inside the loop. Measured
against the issue fix and slice 2's fix round: the cold read's
readability and reliability scores (3 and 3 for three runs), the bugs
the audit's cold read finds that the loop's did not, findings per chunk,
the share of added lines written by fixers (58%), reviewer and fixer
cost, the owner's questions in the loop, and any screen difference
outside the slice.

The light cadence arm is measured on the slice after, so the two changes
are not measured at once (the owner, 2026-11-12).

## Not the plugin's

On the first project: issues #43 to #47 and #49 to #56, and pull request
#48 (records only) to merge or close.
