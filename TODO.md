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
- Skill wording is tried on one or two cases at single runs. The full
  three-run gate runs once, at the end.
- Bars are recorded (`record_thresholds.py --gate-only`, the case list
  through `xargs`) from three-run results only, then `--stale` once more.
- **No single pass of every affected case, and no cost-per-pass or
  re-run-rate figure** (the owner: three-run results only). The write-up
  gives the three-run counts, the bars that moved, and the gate's total
  cost from the result files.
- A rule a skill states in several places survives the removal of one: a
  known-bad reference removes every place.
- The code commit is pushed alone for the external reviewer (its limit is
  300,000 characters); the evidence, bars and generated tables follow.
  A fix it asks for that would stale a batch of cases is weighed first,
  and deferred to that group's next pull request unless it is a defect.
- `docs/flow-map.html` is updated in the same pull request as any change
  to a stage, a launch or a script.

## PR 1: the loop's fixes (0.15.1)

Files: `skills/chunk-runner`, `skills/orchestrator` and its scripts,
`skills/delivery`, the loop fixture, two tools. About 48 cases at the
gate; the two `chunk-runner` replay histories are captured again once,
from a real `kad` session on the library fixture.

The chunk runner (one edit to its text):

- [ ] G1 **The runner hands back while its builder is still working.**
  One run of seven of `chunk-runner-waits-for-handback` ended on "The
  chunk 1 builder is running. Next I'll wait for its report". Done when:
  the cause is read from that run's trace
  (`evals/results/gate-20261114T222734-rerun-chunk-runner-waits-for-handback-run2.trace.jsonl`),
  the skill's wait rule is changed for it, and
  `hand-back-is-one-line-for-what-ran` passes ten runs of ten. **Due
  before slice 3.**
- [ ] G2 **The hand-back is not the one line in about a quarter of runs**
  (a paragraph before the line; 2 of 3 on 2026-11-16). First check
  whether the orchestrator reads its line past a preamble: that decides
  how much it matters. Done when: `hand-back-is-one-line-and-nothing-else`
  has a bar of 3 of 3 on `chunk-runner-one-fix-round`, and
  `skill_mutation.py run --case chunk-runner-one-fix-round --rule
  handback-one-line` exits 0.
- [ ] F2 **The fixer cap says whether a gate fixer counts**: a gate that
  fails after the r1 fix has no rule, and a runner that sent a gate fixer
  then left a regression unfixed under "no third fixer". The cap counts
  review fixers; each gate gets its one fixer. Done when: a
  `chunk-runner` case with a gate failure after r1 passes (the same new
  case as E2's, below).
- [ ] E2 **The `chunk-runner` deletion pass's proposals, all of them**
  (the owner, 2026-11-16; the table is `evals/README.md`, "Rule deletions
  on a skill"): five graders on cases that already run
  (`allow-list-not-widened` on `chunk-runner-gate-deviation`; "no report
  opened" on `chunk-runner-gap-handback`; the gate's `--protect`,
  `--expect-tests-from` and `--agent` on `chunk-runner-gate-deviation`;
  `"model": "sonnet"` on the fixer's launch in `chunk-runner-gate-outside`;
  `sandbox_check.py` run before that launch); the prompts that state
  the rule reworded to name the state; one new case for the first half
  of step 4 (round 0 recorded, findings standing, a gate failure after
  r1); two rules dropped from the skill ("Keep its agent id", "Read its
  last line; read the rest only on `FAIL`"). **The weak `--planning`
  reference is dropped.** **The two replay cases are kept only if G1's
  fix, removed, makes one fail**; otherwise they go. Done when: each is
  in, the deletions the reworded prompts were hiding are run again, and
  E2 is closed in the archive's terms (a survivors list where every
  survivor is a new grader, a dropped rule or an accepted gap).

The orchestrator and delivery:

- [ ] C2 **Autopilot.** A standing `planning/autopilot.md`, asked once
  per project like the delegation file: the loop takes its own
  recommendation and logs "taken as recommended" for a budget overrun
  caused by a relaunch, one extra review to verify a standing Critical
  or High after the last fix, one fixer for a finding that verification
  confirmed, and a readiness route that changes no decision. It always
  asks when the recommendation changes a number or decision the owner
  approved, deletes or rewrites committed work, pushes anything red, or
  touches scope or requirements. Planning forks that carry a
  recommendation stay questions. Done when: cases show one stop taken
  without a question and one always-ask stop still asked.
- [ ] F5 **Every commit that changes source or tests after a scope's
  last review gets one diff-scoped review** before delivery reports (a
  chunk's r2 fix, the slice review's last fix, a gate fixer's, a CI
  fixer's, a triage fix's; the owner, 2026-11-13: "any change should
  always be reviewed"). Designed with C2: that review's Critical and
  High stop for the owner or autopilot's one fixer, Mediums and Lows are
  filed, and a fix of its findings is reviewed the same way, capped.
  Done when: a case shows a last fix with a planted defect reviewed and
  the defect reported, and a clean last fix adding one review and no
  fixer.
- [ ] F6 **Delivery waits for an external review only where a bot has
  reviewed before**; otherwise it says so and returns. Done when: a case
  on the fixture's `gh` stand-in.
- [ ] F7 **The target-directory question takes the directory a project
  memory or `CLAUDE.md` names**, and says so. Done when: a variant of
  `orchestrator-asks-for-target` with the directory named in the
  project's memory takes it without a question, and the existing case
  still asks.
- [ ] **Two steps of 0.15.0 with no case** (the owner, 2026-11-16: one
  cheap, bounded case each): the A step's route back to
  `technology-bootstrap` when the project has no `gate-checks.json` and
  the bootstrap has no Gate checks section (no launch); and the slice
  review's round-0 launches, stopped at the hand-off after launching and
  graded on the launch text alone (the cold reader named with
  `cold-read` and handed no planning document; the test-quality reviewer
  handed the mutation report). The wiring launch itself is slice 3's.

Scripts under `skills/orchestrator/scripts/`, each with a tool test:

- [ ] F1 **The gate reads an absolute `--allow` inside the project as
  the path relative to it**; `--module-dir` and `--deviation-zone` the
  same way. Done when: a test in `validation_gate_test.py`.
- [ ] B4a The mutants file `changed` writes is created with private
  permissions and removed after the pass, also when the pass fails.
- [ ] B4b The mutation pass runs in a disposable clone or worktree, so a
  run killed between a mutant's write and its restore cannot leave the
  mutant in the project's tree.
- [ ] B5a `deferrals.py --out` creates the parent directory.
- [ ] B1a A `nosemgrep` note on `added_lines`' git call in
  `validation_gate.py`.

The loop fixture (`evals/fixtures/library-app/code-plants/loop/`; the
owner, 2026-11-16: both):

- [ ] The "why only the first hold is removed" comment is false by the
  code, and `code-review-comments-chunk` treats it as a comment that
  earns its place (`why-comment-is-not-flagged` fails 2 runs of 3 since
  reviewers probe it). Rewritten so it is true.
- [ ] The repeated block planted for `code-review-chunk-gate-covers` is
  needless code as well as repetition. Replaced by one that is
  reasonable on its own, so `duplication-left-to-the-gate` can read
  "repeated" in a title again.

No gate (tools under `evals/tools/`, which reach no case):

- [ ] F3 **The log checker reads an r2 fix of several commits** written
  with spaces between the hashes. Done when: a tool test.
- [ ] F4 **`cost_by_role.py --log` skips a session with no transcript**,
  names it and totals the rest. Done when: a tool test.

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

## PR 3: the screen-change check (0.16.0)

Its own pull request, after PR 1 and before slice 3 (the owner,
2026-11-16). Touches the orchestrator's D step, so its 38 cases run once
more.

- [ ] C1 **The screen-change check** (the owner, 2026-11-12: pixel diff,
  hands-off, one fixed environment). At D for a UI-touching slice: every
  state with a saved baseline is re-driven by a scripted browser on
  made-up data and compared; a difference in a state the screen design
  does not list as changed is a finding; listed states replace their
  baseline. Baselines are made and compared in CI on Linux only. Done
  when: on the fixture, a style change meant for one state that moves
  another is reported, and the intended change is not.

## Then: slice 3

**The test of 0.15 and 0.16: slice 3 on the first project** (reconnect a
lapsed login, its issue #14), which is UI-touching. It needs PR 1 (G1)
and PR 3 (C1, whose baselines are captured from `main` before the slice
starts); PR 2 may land before or after. It is the first real run of the
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
