# Open work

## 2026-11-20: kad is frozen at 0.19.0; the next plugin, one validated step at a time

**The owner's decisions, 2026-11-19 and 2026-11-20:** no slice 2 of the
comparison; the fourth project's pull request #3 is not merged; this
plugin is frozen at 0.19.0 (everything below this section is parked, not
cancelled); the next plugin is planned here, and "take our time and
really validate each step before we build on top of it".

**What the comparison and the table tests found** (the whole context and
the prompt to start a session: `.synthesis/handoff-next-plugin.md`;
evidence in the private audit repository, `take-4-comparison/`:
`README.md`, `frozen-method/RESULT.md`):

- Slice 1 of the fourth project, built twice from one plan: `light`
  22 on the cold read, 93.6% mutation kills, $64.78; `solo` 21, 80.9%,
  $38.02 with two Highs standing. `solo` failed all four lines of the
  bar. Neither build reached the bugs that matter: both took the plan's
  one-minute give-up and its "initial update complete" as given, and
  both were wrong about Plaid.
- Across the four projects' first slices, the scores stayed at 21 to 24
  while tests went from 619 to 38, and the same bugs came back (an item
  orphaned after a lost reply, a zero amount given a direction, dates
  with no year, a second connect). The cold-read total did not move
  with the number of tests (five builds, one reader each); within the
  fourth project more tests bought 12.7 points of mutation kills. More
  tests caught more code faults and none of the bugs that sit in what
  the plan assumed about the outside world.
- Five completeness tables (a dossier of each outside system, state x
  event, failure modes of each call, input partitions, lifecycle of
  each action), built before any code by a method frozen first
  (`.synthesis/frozen-table-method.md`, sha256 `8830988e…`), and scored strictly
  against the cold reads: 17 of 30 bugs named on the fourth project's
  plan (57%), 9 of 35 on the third project's four plans (26%), one
  run each, so the spread is unknown until V2. Six
  bugs over both were cells the plan had decided wrongly, which a table
  only records. The tables find gaps in a plan, not code faults and not
  wrong decisions, and they flag far more cells than they hit (13% to
  60% of the top 15).

**Audited 2026-11-20** by a second model before the next session
(`.synthesis/handoff-next-plugin.md`, "Audit of this analysis"): the
numbers, three key mutants and the Plaid facts hold; two claims were
corrected here. **Where the work goes** (the owner, 2026-11-20): the folder
`next-plugin/` in this repository, kad untouched at the root; each
step under `next-plugin/validation/V<n>-<name>/`. A repository of its
own is decided at V9.

**The rule for this list:** each step is a question with a measure and
a bar the owner sets before it runs. A step is built on only when its
result is read and the owner says it holds. A step that fails its bar
stops the list there, and the next move is the owner's. No plugin code
is written before step V7.

**Any product, any domain (the owner, 2026-11-20):** "We have to be
careful not to build the plugin to be specific to the accounting app.
It should be able to be used for building any product in any domain."
All 65 benchmark bugs come from two personal-finance projects built on
one provider's API, so every step tuned on them can overfit. Three
consequences for this list. (1) No frozen prompt, method or script
names a finance or API concept; a script checks each frozen text
against a list of such terms before its hash is taken. The list is a
word list kept beside the script and added to as leaks are found: it
catches the obvious term, not an assumption worded otherwise, which is
what V8's held-out product is for. A text frozen before this rule (the
table method of 2026-11-19, which names a provider's API) is used as it
stands wherever a step needs it unchanged (V2); the rule binds its next
version (V3) and every text frozen from now on. (2) What a step
reads about the world outside the product is "whatever the product
depends on that the team does not control": a provider's API, but as
much a fixed corpus or a body of domain knowledge (the owner's
examples: a tool to review the mutashabihaat of the Qur'an, flashcards
made from a surah); a parser of an API's specification is one optional
input, never the method. (3) Nothing is called validated on the
finance projects alone: V8 runs on a held-out product of another kind.

- [ ] **V0. Where a session runs (alongside V1, depends on nothing).**
  The owner, 2026-11-20: rethink the sandbox ("it's been a real pain"),
  likely a microVM; and, the same day, after the candidates were weighed
  on paper: "when someone runs the plugin, regardless of their OS, we
  should have a microVM that Claude can install for them with
  permission. Claude could run a script, then boot it and give it the
  default permissions and then go from there." So the plugin ships the
  launcher (this replaces the first proposal, that it carry no sandbox
  of its own and be launched from outside):
  - *The flow.* A script on the host checks for a working VM tool;
    without one, the session asks and then installs it; the script
    creates a VM for the project, clones the repository into it and
    applies a default allowlist (the model's API, the code host, the
    package registry; any other host only with the owner's approval); a
    new session starts inside the VM and does the work there with
    prompts skipped, the VM being the boundary. The session on the host
    only sets up, launches, copies the transcripts out and destroys the
    VM; it builds nothing.
  - *One contract, a backend per OS.* Create, allowlist, secrets, run,
    copy out, destroy: one small interface, with a backend for macOS
    first and Windows next (the owner works on both), Linux after. No
    one microVM runs everywhere.
  - *Credentials* are short-lived and scoped to the one repository and
    environment, typed by the owner into the host's secret store (never
    passed through the session) and added to requests outside the guest
    where the backend allows: code a dependency runs inside the VM can
    use whatever is inside it, and throwing the VM away does not undo a
    leak. A product that itself needs the host's secret store (the
    macOS Keychain) puts it behind an adapter: a file-backed or Linux
    store in the VM, one contract test for the real one on its OS.
  - *What a script cannot do alone,* once per machine, and so is the
    owner's: turning virtualisation on (admin rights, on Windows perhaps
    a reboot), signing in to the VM tool's account if it has one,
    signing the model in inside the VM, entering secrets.
  - No sandbox at all stays ruled out while sessions run on autopilot
    with live keys and push rights.

  *Weighed on paper, 2026-11-20* (vendors' documentation, nothing run):
  Docker Sandboxes is the only local candidate with a deny-by-default
  allowlist enforced outside the guest and secrets kept outside it, so
  it is the first backend tried; the cloud sessions are second (a
  locally developed plugin may not load there, and a transcript brought
  back loses its compacted messages); Apple's `container` has no
  allowlist or secret handling of its own; a hosted microVM costs by
  the second and its documented path puts the model's key in the guest.
  Docker Sandboxes on Windows and Linux was not verified.

  *The test, on the Mac first:* from a machine without the tool, the
  script brings up a VM and a session in it, counting every step the
  owner had to do by hand. That session runs the fourth project's
  existing suite, the headless browser walk, a `git push` to a scratch
  branch and the mutation pass. Then the controls themselves: a request
  outside the allowlist is refused, the session's credentials cannot
  reach anything beyond their scope, and nothing of the session is left
  after it ends. Then two sessions at once, each with its own scratch
  branch and its own audit path, so a push race or a shared usage limit
  is not read as a failure of isolation. Then the same contract on the
  owner's Windows machine. *Bar (proposed):* the script reaches a
  running session with only the hand steps listed above, no sandbox
  workaround needed, no step slower than under `srt`, every control
  check passes, and the two sessions share nothing inside the VMs (a
  failure that comes from the host's or the account's shared limits is
  recorded as that, not counted). V0 is done when the bar holds on both
  of the owner's systems.
- [x] **V1. The benchmark and its judge.** Turn the five labelled plans
  (the fourth project's slice 1, the third project's slices 1 to 4; 65
  bugs) into a frozen benchmark: each bug written once as a scenario
  (trigger, harm), the plan commit, the cold read it came from. Freeze
  the matcher's prompt. Measure the matcher: run it three times on the
  same tables and check it agrees with itself, and have the owner judge
  a sample of 15 of its calls by hand. *Bar (proposed):* the matcher
  agrees with itself on 90% of bugs and with the owner on 13 of 15. If
  not, the judge is fixed first; nothing after V1 is scored by a judge
  that has not passed.
  *Result, 2026-11-21 (`next-plugin/validation/V1-benchmark-and-judge/RESULT.md`):*
  the matcher's three runs agree on named or not for 63 of 65 defects
  and on the exact class for 58; the owner agreed on 11 of 15 sampled
  calls against the bar of 13, every difference on the line between
  named and part, and after reading the four said the judge holds
  ("I'm ok to call it a success"). This judge is stricter than the
  2026-11-19 scoring, so the baseline is now 10 of 30 named on the
  fourth project and 1 of 35 on the third (24 and 23 counting part),
  not 57% and 26%; later steps report both counts. Kept for a later
  pass, not blocking: split defects that have two parts, and show the
  owner full table rows with no commentary when a sample is next
  judged (the sheet now prints each cited cell's whole row). From the
  external review of #74, for the next version of the matcher and the
  next sample, not changed now because both are frozen with results
  read: the prompt's "outcome under a different trigger" is P while
  "no cell names the trigger" is X, and the tie-break can send such a
  case either way; and the sample's spread over plans slightly favours
  a plan with more defects.
- [ ] **V2. How much the method varies.** Build the tables three times on
  each of the five plans with the frozen method, unchanged. Report the
  spread of cells and of bugs named per plan. *Bar (proposed):* bugs
  named within plus or minus 10 points across the three runs. If the
  spread is wider, a single run measures nothing and the method needs a
  standard density (V3) before any comparison.
- [ ] **V3. A standard density.** The runs ranged from 171 to 675 cells,
  and more cells named more bugs. Write the rule that fixes what a
  complete table is (every state against every event, every call against
  every failure mode, every field against every partition, every owner
  action and long operation against every lifecycle column, and for the
  dossier every call carrying each required fact: inputs, outputs, side
  effects, documented errors, timings, retry safety, limits). The grid
  is generated, not checked afterwards (the owner, 2026-11-20, asking
  what can be deterministic): a script writes every empty cell with its
  id from the lists in the domain model and the dossier: states,
  events, calls, fields, owner actions and long operations (and, where
  the product has one, from a machine-readable specification of what it
  depends on). A dependency that is not a set of calls (a fixed corpus,
  a body of domain knowledge) gets dossier rows of its own: each fact
  about it the product relies on, with its source, its edition or
  version, what the source does not say, and its licence. The model
  fills only each cell's tag and consequence, and cannot add or drop a
  row. A second script regenerates the expected ids from the same lists
  and fails on any id missing from the filled grid or any cell left
  empty, and checks that each DECIDED quote stands at the plan line it
  cites and that each cited source holds the words quoted from it.
  Neither script uses a model; both have unit tests. Two things no
  script settles, said here so the checks are not read as more than
  they are: whether the lists themselves are complete (that is the
  review of the domain model and the dossier), and whether a quoted
  source really supports the cell's claim (that is the research step's
  reader, measured in V4). Re-run V2 on it. *Bar:*
  the spread meets V2's bar, and bugs named do not fall below the frozen
  method's.
- [ ] **V4. The dossier on its own.** The dossier is the cited facts
  about whatever the product depends on that the team does not control
  (a provider's API here; a corpus or a body of domain knowledge
  elsewhere). Build the tables twice per plan: with a dossier written
  first by a research step (each fact cited, what the sources do not
  say listed as open), and without. *Bar (proposed):* the dossier adds
  at least 10 points on the plans whose bugs sit at the boundary with
  what the product depends on, and costs under the owner's limit per
  dependency. On these five plans that boundary is one provider's API,
  so the result says nothing yet about a product without one: V8's
  held-out product is where that is read.
- [ ] **V5. A ranking the owner can act on.** Group open cells by root
  cause (the free tier's slot rule alone accounts for four in the fourth
  project's tables) and rank the groups. Measure how many questions
  reach the owner per slice and what share of the top groups hold a
  real bug. *Bar:* set by the owner before V5 runs, as the number of
  questions a slice may bring and the share that must be real; to see
  what a list looks like, the owner reads the top 15 the frozen method
  already produced on the fourth project, not V5's own output.
- [ ] **V6. The challenge to decided cells.** An adversarial pass that
  argues against each decision the plan made, aimed at the six bugs the
  plan decided wrongly (a merchant's rule that can never change, a new
  amount rule that never reaches rows already filled, a lapse
  after the first pull left out of scope, a forged completion judged
  harmless, the one-minute give-up, a stale tab refused only at the
  finish). Measure how many of the six it raises and how many decisions
  it disputes that were right. The challenge's prompt is written and
  frozen without the six in view, so it is not tuned to its own test.
  *Bar (proposed):* four of six, with fewer than one dispute in five on
  a right decision.
- [ ] **V7. The register and traceability, as scripts.** One register of
  requirements with ids, cut from the tables; each test names the ids it
  holds; a script checks both ways (every requirement held by a test,
  every test holding a requirement) and that no requirement is written
  twice. Deterministic, with unit tests; no model. *Bar:* the script
  run over the two fourth-project builds finds the two bugs the plan
  decided rightly and the builds missed, and the tests that hold no
  requirement are counted. A link says a test names a requirement, not
  that it would catch a break of it: that is measured by the mutation
  pass with its mutants keyed to requirement ids (a requirement whose
  mutants all survive is held by nothing, whatever its links say).
- [ ] **V8. One lean build from the register, on a held-out product.**
  Not the fourth project again (V2 to V6 are tuned on its plan): slice
  1 of a new product of another kind, one that leans on no provider's
  API and does depend on a fixed corpus or a body of domain knowledge,
  so that kind of dependency is exercised (the owner, 2026-11-20; the
  Qur'an review tool would fit, the product is the owner's choice). It
  is planned, then what V1 to V7 produced is applied to its plan frozen
  and unchanged (the matcher, the table method and its grid scripts,
  the dossier step, the ranking, the challenge, the register and
  traceability scripts: the tools, not those steps' own measurements,
  whose bars belong to the finance plans), then one builder builds it,
  with the probing review after the build as the main review. Its own
  cold read is the key: the matcher scores what the tables named
  against it, as on the benchmark, and because the matcher was only
  measured on finance defects it is measured again here the way V1
  did (three runs, a sample judged by the owner) before its count is
  read. Measured as the comparison measured
  the two arms (cold read, mutation pass, cost, wall clock, the owner's
  questions and stops), with the share of its bugs the tables named
  beside the benchmark's. The builder and every planning step never see
  the cold read. A product in a domain the model does not know needs
  someone who does to read its plan; who that is, is settled before the
  run. *Bar:* the owner writes it before the run; `light`'s 22, 93.6%
  and $64.78 are the nearest reference, on a different product, so
  they are a guide and not a like-for-like line.
- [ ] **V9. The new plugin.** Only after V8 holds: a design document
  (its stages, what is ported from kad with its tests and what is
  dropped, its evals: deterministic checks on documents, the benchmark,
  a real slice now and then), for the owner's review before any of it
  is written. Port list to weigh one by one: the gate, the mutation
  pass, the screen-change check, the map extractor, the cost tool,
  audit mode, the sandbox check, delivery's CI watch, the cold-read
  brief, the planning personas, and the lessons in `INCIDENTS.md`.

**Known and left alone while frozen:** the gate passes coverage through
`NODE_OPTIONS`, which Node 24 refuses under `pnpm test` (found by the
fourth project's `light` run, filed in the audit repository); it is fixed
in kad only if kad is used again, and is on the port list if the gate
moves.

---

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

5. **Step 2's choices, 2026-11-18** (pull request #68 merged the same
   evening as kad 0.17.1):
   - The loop **waits for the owner to merge the planning pull request**
     before it builds ("Wait"): the owner's checkpoint on the plan, and
     where a slice that is too broad is caught.
   - **No size threshold for a slice** ("No number"): the slice file
     carries its size line (criteria count, expected chunks) and the
     owner judges it at the planning pull request.
   - Taken as recommended, not asked: the domain model is the
     software-architect's, who asks the owner only about a state it
     proposes to leave unsupported; each state cites the provider's
     public documentation, or is marked to verify with the step that
     would confirm it.

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

- [x] Done 2026-11-18: pull request #68, merged as kad 0.17.1 (70
  runs, $53.64; `evals/README.md`, "The instruments after slice 4").

### Step 2. Planning (kept whichever arm wins)

**Built 2026-11-18 as kad 0.18.0 on branch `planning-0.18.0`; the gate
passed 2026-11-19 at the owner's word** (109 cases, 228 runs, $146.64;
`evals/README.md`, "The planning changes", which also says what the
trial of the new cases changed in `vertical-slicing` and
`accessibility-review`). How each was built, where it differs from the
lines below:

- **P1**: the trigger is mechanical. `requirements-refinement` writes an
  `## Outside systems and lasting things` section, and the orchestrator
  routes to `domain-model` when it names something `domain-model.md`
  has no table for. A requirements document written before the section
  existed asks for no model, so no existing fixture or project is
  routed there by surprise; the first project gets its model when asked
  for, or when a stage hands a missing state back. The slice file names
  the states it touches under `## Domain states`, and the readiness
  gate's twelfth check (`domain-states-modelled`) holds them against
  the model.
- **P2**: the slice file always holds the thinnest cut; a wider cut is
  asked after it is written and revises the file in place. `## Size` is
  one line, `Criteria: <n> functional; chunks expected: <k>`.
- **P3**: no stage edits the slice's size line (each may touch only its
  own pointer line): its count goes on the pointer line, `(<n>
  criteria)`, and the planning pull request's body adds them up.
- **P4**: applies only with a GitHub tracker and never to an issue fix
  or a slice whose build has started. The readiness gate runs in the
  planning row, before the pull request, and again at A.4. The A step
  still makes a small planning commit on the slice branch for what was
  written after the merge (the per-slice delegation file, the log).

Seven new cases: `domain-model-bank-phase1`, `domain-model-bank-phase2`,
`orchestrator-route-domain-model`, `vertical-slicing-thinnest-cut`,
`accessibility-review-design-notes`, `orchestrator-planning-pr-open`,
`orchestrator-planning-row`. No case holds: the A step's
own refusal (`flow not started: planning pull request not merged`,
reached only by asking for a build with no planning pull request open),
`delivery`'s "A planning pull request" past the push (the fixtures have
no network), a comment on a planning pull request routed back to its
document's owner, and `domain-model` reading a provider's documentation
(the eval sandbox has no web tool, so every source there is `to
verify`).

The eleven frozen histories that carried the old text of four skills
were captured again before the pass.

- [x] **P1. A domain model, once, before slicing.** The dead ends of
  slices 1, 3 and 4 are one unanswered question: what states can a bank
  connection be in, how is each entered, what can the user do in each,
  and which are deliberately unsupported. A new stage after the scope
  map: one document per external system or long-lived entity, a state
  table, read by `vertical-slicing`, `architecture-design` and
  `reliability-requirements`, and held by the readiness check ("every
  state the slice can leave a thing in has a way out or is listed as
  unsupported"). A new skill and its cases.
- [x] **P2. The breadth of a slice is the owner's.** `vertical-slicing`
  offers the thinnest cut first and asks when it recommends more than
  it; the slice file carries a size line (criteria count, expected
  chunks); no threshold: the owner reads the line at the planning
  pull request (decision 5).
- [x] **P3. Fewer, sharper criteria.** Slice 4 had 35 for one button,
  and each became a test. The security, reliability and accessibility
  stages add a criterion only for a behaviour a user or an operator
  could observe going wrong; wording, logging detail and announcement
  phrasing are design notes, not criteria. The measure is the count per
  slice on the size line of P2.
- [x] **P4. Planning lands as its own pull request, before the build.**
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

**Built 2026-11-19 as kad 0.19.0 (branch `solo-0.19.0`); the gate
passed the same day at the owner's word** (25 cases, about $76;
`evals/README.md`, "The solo cadence"). How each was built, where it
differs from the lines below:

- **The cadence** is taken at A from the owner's message (the word
  `solo`, or "one builder for the slice") or from a line `cadence:
  solo` in `<target>/autopilot.md`, written there only when the owner
  says it holds for later slices. G1 (the standing file for `light`)
  stays parked.
- **L1**: step S of the orchestrator, in place of B, C and D. One
  `tdd-coach` on Opus with a new skill, `slice-build` (not a branch of
  `tdd-implementation-lite`: the other arm's text and cases are
  untouched, and the loser is one removal). The log reuses the C line
  as chunk 1 of 1 and the D line, so the log check and the delivery
  step read it as they read any slice.
- **L2**: `slice-build`'s "One test per criterion". The level is the
  outermost the project's suite can drive; a fault is injected at the
  design's port. The report's first table has one row per criterion.
- **L3**: the same scripts with the same arguments. The gate runs once
  on the whole build, with the design's module directories as its
  scope and no per-chunk test list.
- **L4**: five kinds are confirmed (a failing check, a bug the cold
  read reproduced, a criterion the walk failed, a survivor the builder
  calls real when asked by message, a Critical or High of the review
  that a verify agent reproduces). One fresh fixer on Opus, the gate,
  then the reproductions run again by the verify agent (the cold
  reader's probes do not outlive its clone). No reviewer reads the
  fix, no second fixer follows, and the autopilot round does not run:
  a Critical or High that still reproduces stops the flow.
- **L5**: one `code-reviewer` on Opus applying five review skills in
  one read. Its findings go to `slice-findings.md` and from there to
  the pull request's body ("Review findings", `delivery`); none is
  filed as an issue.
- **L6**: six cases, all tool-judged: `orchestrator-solo-from-message`,
  `orchestrator-solo-from-standing-file`,
  `orchestrator-solo-build-launch`, `orchestrator-solo-confirmed-only`,
  `orchestrator-solo-nothing-confirmed`, `slice-build-cancel-hold` (on
  Opus). One known-bad reference holds (step S without its
  confirmed-only rule). Two written with the cases did not fail and
  were removed: the A step without its `solo` paragraph, `slice-build`
  without its one-test-per-criterion rule (`evals/README.md`, "The
  solo cadence").

No case holds: the hand-back check of S.1 (a criterion
with no row), the gate's one fixer at S.2, the builder asked about
survivors, the verify launch for a Critical or High, the reproductions
run again after the fix and the stop when one still reproduces, the
review's line after a fix, `delivery`'s "Review findings" part,
`slice-build`'s wording table (the fixture slice has no screen) and its
"A fix handed back", and the standing-file line being written from a
message. The first real run of all of them is the comparison.

The gate pass (the owner's to start): 25 cases, the six new at three
runs and nineteen at one (the A step's text and `delivery`'s reach
them); ten known-bad references at three runs, the three new among
them; no frozen history is stale. About 67 runs before re-runs.

- [x] **L1. One builder for the slice**, on the strongest model, given
  the slice, the design, the domain model and the criteria. No chunk
  plan, no runner, no per-chunk agents. It commits in steps of its own
  choosing.
- [x] **L2. One light test rule**: each criterion held by one test at
  the level that reaches it (the running app where it can), written
  first and seen failing; a module test only for a branch that test
  cannot reach; exact wording held in one table per message module.
- [x] **L3. The mechanical checks, unchanged**: the gate with every
  check, the mutation pass on the changed lines, the cold read by
  execution, the criteria walk for a slice with a screen, CI and the
  screen-change check at delivery.
- [x] **L4. Only what was confirmed gets fixed**: a failing check, a
  surviving break the builder agrees is real, a bug the cold read
  reproduced, a criterion the walk failed. One fresh fixer, the gate,
  and the cold read's probes run again.
- [x] **L5. One combined review, reported and not fixed**: its findings
  go to the pull request's body by severity, for the owner. A Critical
  or High it raises is verified by execution first and fixed under L4
  if confirmed.
- [x] **L6. Cases** for the mode: the A step takes it from the standing
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
