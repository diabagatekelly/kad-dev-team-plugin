# Open work

One thing is open: slice 3 on the first project, and what it needs from
the owner first. Everything else of the list written on 2026-11-16 is
done: PR 1 (#64, 0.15.1), PR 3 (#65, 0.16.0) and the final pull request
(#66, 0.16.1: H1, PR 2 and every loose end of the other two). Each one's
account (what was built, its counts, what it fails without, the bars
that moved, what no case holds) is in `evals/README.md` under "The
loop's fixes", "The screen-change check", "Why fixers regress" and "The
final list"; the items as they stood, with the owner's decisions, are in
`docs/todo-archive.md` (and the eval suite's own old list in
`docs/todo-archive-evals.md`), where each keeps its letter and number.

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

## Done: PR 1 (#64), PR 3 (#65), the final pull request (#66)

Nothing is left open by any of them. What the final pull request could
not show with a case, and what it proposes and did not build, is said in
`evals/README.md`, "The final list" ("Still not held by a case") and
"Why fixers regress" (four proposed changes, none built: they are the
next gated change to `tdd-implementation-lite` and to two of the
orchestrator's scripts, if the owner wants them before or after slice
3).

## Then: slice 3

**The test of 0.15 and 0.16: slice 3 on the first project** (reconnect a
lapsed login, its issue #14), which is UI-touching. PR 1, PR 3 and the final pull request are done. Before the slice starts, on the
first project, from the owner:

- [ ] the installed plugin updated to 0.16.1 (after #66 merges);
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
- [ ] a word on H1's four proposed changes (`evals/README.md`, "Why
  fixers regress"): built before the slice, or the slice run first as
  they stand.

H1 itself is done. The slice is the first real run of the
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
