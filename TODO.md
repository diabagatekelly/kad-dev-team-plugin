# Work list: implementation flow v4

Read first, in this order: this file; `.synthesis/implementation-flow-v4.md`
(the design: every item below cites its section); the audit that produced
it, `audit-docs/personal-finance-tracker-2-slice-1/plugin-review/2026-10-25-slice-1-review.md`
(the nested `audit-docs/` clone, or github.com/diabagatekelly/audit-docs);
then `.synthesis/implementation-flow-v3.md` for what v4 amends. The three
failures being fixed: not production quality, too costly ($346 for one
slice), too slow (14.5 h). The owner's two additions on 2026-10-25: comments
only when absolutely needed, the code self-documenting (§8, D8); the tests
fake too much and there are no integration tests (§6, D6, D13).

Rules for working this list: one PR per phase; every skill change gets its
eval case in PR 3, and v4 is not done (0.8.1 not used for slice 2, this
list not closed) until those cases and the evidence for every case the v4
edits reach are recorded and the gate passes (the owner merged PR 1 with
its eval-gate check red on purpose, 2026-10-26); keep the eval
playbook's rule (read every failure before re-recording a bar); nothing
here changes `evals/TODO.md`'s own items. Tick an item only when its
"done when" holds. Questions in §13 of the design are answered by the
owner, not guessed; until answered, the stated default applies.

## PR 1 — the loop (orchestrator, tdd skills, review skills, scripts)

Status (2026-10-25): built and committed on `implementation-flow-v4`
(`8033f43` scripts, `db17d28` skills and agents, `7fc4eab` docs and
version). Two things went in beyond the list because the loop needs them:
the five owning planning skills accept a delegation file as the owner's
approval for a mid-build decision (1.10 cannot complete without it), and
`release-engineer` is `background: false` since `repo-bootstrap` asks.
Open until PR 3: `cost_by_role.py` (the E line says `cost not measured`
until it exists) and the eval evidence the pre-push hook wants for every
case these skills touch.

### Orchestrator `skills/orchestrator/SKILL.md`

- [x] 1.1 A: one question per `AskUserQuestion`, in order settings → sandbox → policy → delegation (§3.A.2). Done when: the A step text names four separate calls and forbids bundling.
- [x] 1.2 A: the delegation question and `planning/delegation-slice-<nnn>.md` (what it covers, what it never covers, committed in the planning commit) (§3.A.2, D5).
- [x] 1.3 A: the budget line (`budget — 5h, 2 reviews/chunk, 1 fix/scope (+1 regressions), 8 consults`), counted at every chunk boundary, the flow ending at the boundary when exceeded (§3.A.3, D10).
- [x] 1.4 A: no git repository or no `origin` → `flow not started: no repository`, route to `release-engineer:repo-bootstrap` (§3.A.4).
- [x] 1.5 A.5: the design-readiness gate, run with `readiness_check.py`; each failed check a backward route entry to the persona it names; `readiness — PASS` on the A line (§5, D4).
- [x] 1.6 B: the plan check's fourth item, every chunk names a seam test (§3.B, D6).
- [x] 1.7 C.2: gate `--allow` = Files line + `--module-dir` for each design module; in-module off-list file = `scope: deviation`, recorded on the C line; out-of-module = FAIL to the fixer once. Delete the "add it to the plan entry" sentence (§3.C.2, D9).
- [x] 1.8 C.3: one combined reviewer (`code-reviewer`, Opus, invokes `code-review` + `test-quality-review` + `reliability-review` by Touches) and one smoke agent per round; never more than two launches (§3.C.3, §4, D1, D6).
- [x] 1.9 C.4: one fixer; regressions-only re-review on the fix diff; a second and last fixer for regressions; pre-existing findings standing; standing C/H stops the flow, standing M to the PR body (§3.C.4, D2).
- [x] 1.10 C.5: the gap step, `needs-decision (<persona>)` → one consult with the delegation file → persona commits its own document → one `decision <n> <sha> (<persona>)` line. Without the file: recommendation only, flow stops for the owner (§3.C.5, D5).
- [x] 1.11 C line fields: `deviations`, `smoke`, `standing`, `decision` lines, `budget`. Only `rounds_record.py` output reaches the log (§3.C.6, §4).
- [x] 1.12 D: Definition of Done before D's reviewers (`done_check.py`, one Sonnet fixer for the batch), then the six reviewers once with one fix round as C.4; Lows allowed at D only (§3.D, §7, D3, D7).
- [x] 1.13 E: nothing in the background; Lows to the PR body under "Known Lows" (grouped by theme), standing Mediums filed one issue each; PR body links, E line, `cost_by_role.py` total on the E line, audit sync, all in the same turn (§3.E, D11).
- [x] 1.14 "Pausing and resuming": the handoff file and the `Resumed` line (§3, last subsection).
- [x] 1.15 Log entry format: one bold line per step; indented plain bullets for decisions and corrections; never a second bold A/D/E line (§9).
- [x] 1.16 Delete: "every Low becomes an issue"; "until clean, capped at five"; the six-reviewer territory table; every orchestrator-writes-a-script path.

### `skills/tdd-implementation/SKILL.md` and `skills/tdd-implementation-lite/SKILL.md`

- [x] 1.17 Chunk plan: Done-when names the seam test; Touches drives `reliability-review` (§3.B).
- [x] 1.18 Building one chunk: the seam test first in the Test List (through the real composition root, real adapters and local store, only the external service faked at its wire boundary); port fakes only for a branch the seam test cannot reach, each named with its branch (§6, D6, D13).
- [x] 1.19 Comments: the §8 writing rule in GREEN and REFACTOR; never cite a planning document, decision number or criterion in code (D8).
- [x] 1.20 Deviations named in the report section; the plan entry never edited by the builder or fixer (§3.C.2).
- [x] 1.21 Reporting: `Fix r<i>` lines directly after `Commit`; no `### Lows` section (§9).

### Review skills

- [x] 1.22 The shared report format stated identically in `code-review`, `test-quality-review`, `reliability-review`, `security-review`, `architecture-review`, `accessibility-review`, with `needs-decision (<persona>)` as a severity value (§4).
- [x] 1.23 `code-review`: the combined-review paragraph (three skills in turn, one report, ≤ 8 findings, C/H/M only per chunk); WHAT-comment and planning-reference comments Medium; function > 80 lines / file > 300 lines a finding at D (§4, §8, D8, D14).
- [x] 1.24 `test-quality-review`: the seam check (all tests fake at the port → High); the fake inventory per chunk (own-code fake with a real local equivalent → High; hand-rolled DOM harness → High pointing at D7.4); padding measures at D (test/src ratio, share of tests asserting on source text / package.json / script bodies, > 10% Medium) (§6, §7.9, D13).
- [x] 1.25 `accessibility-review`: the smoke-run mode (start the app, drive the chunk's Done-when, check the chunk's criteria, shared format); the full design-time review at D only (§6).

### Scripts `skills/orchestrator/scripts/`

- [x] 1.26 `validation_gate.py`: `--module-dir` (repeatable) and the deviation line; run `typecheck` and `lint` from the manifest when present; report comment density (comment lines / non-blank, `src/`), files > 300, functions > 40, lines at depth ≥ 4 (report-only) (§3.C.2, §8, D14).
- [x] 1.27 `rounds_record.py` (new): review/smoke report in the shared format → sidecar rows (`class` by hunk against a range) → C-line counts; `--standing` (§4, D9).
- [x] 1.28 `readiness_check.py` (new): the eight §5 checks over the planning directory → PASS or failing checks with the persona each routes to.
- [x] 1.29 `done_check.py` (new): the nine §7 checks (README sections; lint and formatter config present and clean; typecheck; code-in-strings scan; planning-reference scan; comment density; "Kept for later slices" columns exist; env defaults not production; test padding figures).
- [x] 1.30 `sandbox_check.py`: exit-2 `--write-settings` writes `permissions.deny` and `sandbox.filesystem.denyRead` only, never `sandbox.enabled`/`failIfUnavailable`, and says so (D9).
- [x] 1.31 `skills/map-update/scripts/extract_map.py` for TS/JS and Python; the "no extractor" rule in `map-update` SKILL.md (§9, D9).

### New skills and agents

- [x] 1.32 `release-engineer:repo-bootstrap`, smallest form: `git init`, default branch, `.gitignore`, `gh repo create` private, first push, decided with the owner, recorded in the technology-bootstrap doc (§3.A.4).
- [x] 1.33 `docs-writer:readme`: README from manifest + design + slice (§7.1); never invents a command the manifest lacks; the smoke agent follows it on a clean clone in D's last round.
- [x] 1.34 `agents/code-reviewer/AGENT.md`: the combined-review launch; `agents/accessibility-engineer/AGENT.md`: the smoke role; `agents/tdd-coach/AGENT.md`: `maxTurns` 120 builders / 160 D fixer, passed on launch (§9).
- [x] 1.35 README "The chunk loop", PERSONAS (Orchestrator paragraph → v4; `release-engineer` + `repo-bootstrap`; `docs-writer` + `readme`); version 0.7.0.

## PR 2 — planning (from the two planning reviews, §9 "Planning skills", D12)

Status (2026-10-26): built and committed on `implementation-flow-v4-pr2`
(`8cfa1e0` 2.1, `ce099af` 2.2–2.7, `9743da6` 2.8). The §13 defaults were
applied as stated (one question per `AskUserQuestion`; indented outcome
bullets allowed under any entry; report after every step and ask only
when the next row needs an owner decision). 2.8's done-when holds: the
checker on the run-2 log with its three sessions and their 243 subagent
transcripts reports 5 errors (entries 4 and 11's Artifact lines, and
entry 28's three real deviations: repeated A/D/E lines, chunk 6 with no
`commits` field, no E line) and none of the 76 "no log entry written
before it in this session" false positives; the run-1 log reports the
same 13 errors as before; a v4 entry written from the orchestrator's
template parses with 0 errors. One fix outside the list, made with 2.8
because the same rule produced it: a stage redone after a backward route
(entry 22) is no longer "goes back without saying". Left out, from the
planning review's finding 12 and not on this list: `vertical-slicing`
re-consulting `acceptance-criteria` when a revision rewrites a
criterion. Open until PR 3: the eval evidence the pre-push hook wants for
every skill these commits touch. Pushed as PR #24 (2026-10-26, hook
bypassed at the owner's direction, evidence check red on purpose).
External review round 1 (Sourcery, 13 findings): 12 fixed in `f7e891d`
(owed v4 follow-up rounds, the loop's allowed subagent skills, exact
`none (<reason>)`, the E line closing only its own loop, the sidecar
read inside the project and per slice with the same C/H/M filter as the
log, added log lines must be indented bullets, "in place" as a backward
declaration, problem-framing asks for every unanswered section, "via
AskUserQuestion" changes how not whether); 1 deferred as issue #25 (a
non-UI slice's accessibility placeholder has no row that fills it).

- [x] 2.1 `requirements-refinement`: the full question pass before writing ("a question not yet asked is owed, not Not yet confirmed"); walk the problem doc's Open questions; revise in place while the document is still yours, supersede once a later stage has built on it. Same revise-in-place wording in `scope-map`, `adr`, orchestrator step 3; `vertical-slicing`: revised in place, never `-v2`; three placeholders (security, reliability, accessibility).
- [x] 2.2 `architecture-design`: every criterion and placeholder failure path has a structural home or an Open question with owner and re-entry note; "Kept for later slices" line; a consequence that changes a confirmed requirement is a hand-back to `product-manager`; "informed by a consult" names the Skill call and records the answer.
- [x] 2.3 `reliability-requirements`: a number on every retry/wait/poll/give-up/stale or "unbounded, owner approved"; read the security file first, reconcile or escalate overlaps; the unusable-reply row; a routed question is answered or re-routed with a reason, never to the implementer.
- [x] 2.4 `screen-design`: every state the security, reliability and accessibility files name gets a mockup; omitting a declared shell element is a proposal to `design-system`.
- [x] 2.5 `security-requirements`, `reliability-requirements`, `accessibility-review`: replace the slice's placeholder line with a one-line pointer and edit nothing else; the story is `docs-writer`'s; a narrowed criterion is a finding for `product-slicer`; consult answers as visible text under `## Consult answer`.
- [x] 2.6 `problem-framing-doc`: gather through `AskUserQuestion`, one question per section. `map-query`: emit the header for "no map" after checking the path.
- [x] 2.7 Orchestrator steps 3–5: Skill arguments say where to save and nothing about other stages' documents; "via `AskUserQuestion`" passed to every routed skill; re-inspect without asking; reports as visible text; one entry per owner and one continue prompt for a fact that ripples requirement → slice → story; the outcome-bullet rule per §13's answer; non-routed entry shape (`Routed to: none (<reason>)`, one Artifact path).
- [x] 2.8 `evals/tools/orchestrator_log_check.py`: Agent launches under an open entry across sessions; sidecar for round counts; clean rounds without a split; `Policy:`/`policy —`; parentheticals; consult-tagged Skill calls (`NARROW CONSULT`/`INLINE CONSULT`) under the latest entry; the v4 fields. Done when: on the run-2 log it reports none of the ~60 false positives and all three real deviations (§11 case 11).

## PR 3 — evals (§11)

Status (2026-10-31): built on `implementation-flow-v4-pr3`. Cases 1–12
are seventeen case directories plus one script check, all on the
library-app fixture: the chunk loop's states come from
`evals/fixtures/library-app/code-plants/loop/state.sh` (eleven states,
each the git history, gate files, sidecar and handoff a previous session
would have left; its README and `answer-key.md`'s `L` and `P` rows list
the plants), three planted planning sets under
`evals/fixtures/library-app/planning/`, and `cost_by_role.py` under
`evals/tools/`. Case 11 is `evals/orchestrator-log-format/check.sh`, no
model: the v4 template entry parses clean, and the run-2 part runs when
the private log is given (verified 2026-10-26 under 2.8). Case 7's
builder half is three graders on `tdd-implementation-one-chunk`; the
seam test is a grader on both chunk-plan cases. 3.3: no remaining v3 case
assumed six reviewers per chunk or "until clean" rounds (J5 had rewritten
them on 2026-10-24); the two routing cases' graders gained the delegation
question and the readiness gate. Found on the first local run (a Mac,
after Windows and WSL): `sed -i` without a suffix in two scripts and a
`slice-fixed` snapshot verify.sh type-checked without its base, fixed;
Node 24 is needed for the fixture's test flag (`evals/tools/gate.sh`
puts Homebrew's on the path on a Mac). The first calibration pass (2026-10-31, one
run each, the Mac) found: the recorder read a smoke report whose
`**Severity:**` sat in a list item as zero findings and printed `smoke
PASS` (fixed: a list marker is tolerated, and a smoke report with no
parsed finding must say `PASS` or the script exits 1); the E step never
committed the log, so `delivery`'s clean-tree rule stopped every real
delivery (fixed: E.1 commits the log and removes the handoff as
`Records: slice <nnn> delivery`); the handoff file is committed with the
records, so the fixture's states now commit it; the gap state lacked the
reliability document its planted review cites; the scope-consequence
criterion was vacuous for an in-memory queue (now it needs the other
holds to survive the restart); the readiness case ran the whole loop once
the gate passed, as the skill says, so its prompt now hands off at the A
line. What the Mac cannot measure: inside the eval sandbox `git` by name
is Apple's shim and fails (see the evals README's gate section), so the
chunk-loop, delegation-with-file and tdd cases could not be measured
until a `git` shim in Homebrew's `sbin` was found to be reachable there
(`gate.sh` checks for it); the scripts gained a working-git fallback as
well. All seventeen bars are recorded from the Mac (K3 in `evals/TODO.md`,
2026-10-31); the second pass over the loop cases found and fixed two more
defects (the gate command never allowed the loop's own uncommitted log;
a handoff naming E was resumed by invoking `delivery` directly). K4, the
stale re-record of every case the skill edits reach, is done (68/68 with
evidence, 2026-10-31; four history chains re-frozen after PR 2 on the
way); PR 3 is pushed as PR #26 (2026-11-01), the evidence check green.

- [x] 3.1 Cases 1–12 on `evals/fixtures/library-app/`, each with graders, per `evals/README.md`; bars recorded with `record_thresholds.py` after calibration.
- [x] 3.2 `evals/tools/cost_by_role.py` (copy from `audit-docs/personal-finance-tracker-2-slice-1/plugin-review/tools/cost_by_role.py`; per-model prices; prints the E-line total).
- [x] 3.3 Rewrite or retire the v3 cases that assume six reviewers per chunk or "until clean" rounds; the two routing cases' A step gains the delegation question and the readiness gate.

## After the PRs

- [x] 4.1 Run slice 2 on 0.8.1 (v4 complete: PR 1 to PR 3, the launcher and the no-screen slice rule, #23, #24, #26, #27, #29) with the budget line, in a fresh repository for a one-to-one comparison, started with `bin/kad` (the sandbox runtime, audit mode and the audit repository set up by it); audit it the same way (`audit-review` skill; the audit-docs tools); compare the E-line cost and the §10 estimate. Done as run 3, slice 1 of a fresh repository on 0.9.2 (the comparison is in the review below); the E-line cost covered the planning session only (H1.4). Slice 2 itself is the next run, on the version that carries H1 to H3, not on 0.8.1.
- [x] 4.2 Decide D9 phase 2 (a chunk-runner agent per chunk) on the orchestrator's measured context from 4.1 (> ~250k tokens → build it). Decided 2026-11-08: slice 2 measured about 427k cache-read tokens per call; build it (`.synthesis/handoff-slice2.md` P3.1).
- [x] 4.3 Won't do (owner, 2026-11-08). Open items from run 2, in the project not the plugin: PR #2's issue-links placeholder, the untracked `pr-r1-comments.json`, the missing E line, the three suspected bugs in repo 2 (orphaned vault row before the record write; `complete()` without a held claim; the year missing from the date column), repo 1's single-account rule and cursor persistence.

## After run 3 (2026-11-01)

Run 3 (`personal-finance-tracker-3` slice 1, 0.9.2) is reviewed; 4.1's
comparison is done in `audit-docs/personal-finance-tracker-3-slice-1/plugin-review/`.
The work list that came out of it is `.synthesis/handoff-run3.md`: audit
and measurement that failed silently (H1), the loop (H2, including the cold-read
protocol for every reviewer), planning (H3), the project's own open bugs
(H4), the slice 2 audit of the lite policy's tests (H5) and two questions
for the owner (H6). Slice 2 runs on the version
that carries H1 to H3.

Status 2026-11-03: H1 merged as PR #34 (0.10.0: the audit clone before the
fence, a sync after every records commit, failures on the line, transcript
snapshots, Chrome under the fence, no browser owed); H2 as PR #35 (0.11.0:
the cold pass first for every round-0 reviewer, decided by a three-run Opus
check, deviation zones, the fixer's rename and shell-edit rules, no chunk
Lows, the README's CI line); H4 filed on the project as #6 to #13, all
still open; H3 is PR #37, 0.12.0 (built-ins by default approved once in
`technology-bootstrap`, the readiness check reading Strategic and Tactical
headings by name and the design template naming them, the design's tests
line saying what lite's seam rule says, `reliability-review`'s
created-then-timeout-then-retry row with the refund overlay planting it;
Sourcery's eleven comments triaged, five fixed and six declined), merged
2026-11-06. H6's budget and heavy-policy questions decided and built as
0.13.0 (8 h for a UI slice, 5 h otherwise; `tdd-implementation` retired
with its five cases, lite the only implementation skill); D9 phase 2
waits for slice 2's measurement; the review cadence is a policy arm for
after H5 (`.synthesis/review-cadence-survey.md`). Next: H4's fixes in the
project (issues #6 to #13 on personal-finance-tracker-3, on 0.13.0, the
first real `bin/kad` session with audit on since H1), then slice 2 under
`bin/kad --chrome` with audit on (after `kad --reset`: the stored audit
repository is the project's own origin), whose audit is H5. Two eval bars were re-recorded for drift under Claude Code
2.1.316 (the handoff's H2 note): a directly-invoked reviewer skipping
`why-comments`, a directly-invoked heavy builder skipping its reviews; a
candidate agent-file fix, not scheduled.

## After slice 2 (2026-11-08)

Slice 2 (`personal-finance-tracker-3` PR #20, 0.13.1) is reviewed in
`audit-docs/personal-finance-tracker-3-slice-2/plugin-review/`. The work list
that came out of it, with everything left from `.synthesis/handoff-run3.md`
and the owner's decisions of 2026-11-08, is `.synthesis/handoff-slice2.md`:
start (the launcher as the one way in, Chrome always, no questions), screen
checks (the acceptance criteria walked in a real browser), the loop (the
chunk runner, the light cadence arm with the builder as fixer, deferred
decisions as blockers), planning data (nothing of the owner's by value) and
audit. 4.2 is decided there (build the chunk runner); 4.3 is dropped.
P1 shipped as 0.14.0 (PR #41) and P2 with P3 as 0.14.1 (PR #42, merged
2026-11-09): the chunk runner, the criteria walk, the data rule, the
open-work routing, the triaged deferrals, the counted shell edits and the
light cadence arm (measured at slice 3). P4 (planning data) shipped as
0.14.2 (PR #44, merged 2026-11-09): the "described, never quoted"
rule in five planning skills, `source_scan.py` behind the readiness
gate's tenth check, the chunk gate's `sources` check and delivery's scan
before a push, and delivery's removal procedure. P5 (audit and
measurement) shipped as 0.14.3 (PR #47, merged 2026-11-10): transcripts
by session id, withheld when they hold a listed source's value, the
sync's lock, the cold-read brief and the mutation runner for the slice
reviews. The list is done. Next: slice 2's fix round on
`personal-finance-tracker-3`, then slice 3, both under `kad` with 0.14.3
installed. The handoff's first section, "Where the list stands", is the
current state.

## After slice 2's fix round (2026-11-12)

The fix round ran 2026-11-10 on 0.14.3 (PR #20 round 1) and was reviewed the
same day; its review's fixes merged as 0.14.4 (PRs #49 and #50: the mutation
runner's reporters, the source scan's one-word cells and tab column, the
Definition of Done's README list, a structural size finding as the architect's
decision, the anchoring pass with `INCIDENTS.md`). Next: slice 3 on 0.14.4
under the light cadence, as `.synthesis/handoff-slice2.md` "After this list"
says; nothing of the fix round is left to run.

## Work list: 0.14.5 and 0.15.0 (written 2026-11-12, after the issue #33 fix)

The sixth run (issue #33 on `personal-finance-tracker-3`, kad 0.14.4, PR #42)
was reviewed 2026-11-12: `~/.claude/kad-audit/reviews/2026-11-12.md`, and in
the audit repository as
`personal-finance-tracker-3-slice-1/plugin-review/2026-11-12-issue33-fix-review.md`
with the cold read (4/3/4/4/3/4) and the mutation pass (39 of 44). The finding
numbers below are that review's. The tooling behind phase B is surveyed in
`.synthesis/quality-tooling-survey.md`. Slice 3 has not run; it is the test
of 0.15.0 below, not the next thing to do.

Rules as before: one PR per phase; every skill change gets its eval case on
the library fixture, never the project's content; the gate passes before the
PR opens (a usage window sustains about 100 to 120 cases); Sourcery's
comments are triaged without being asked. Tick an item only when its "done
when" holds.

### Phase A, 0.14.5: what broke the run

- [x] A1 **A runner waits, and a result is only a hand-back** (finding 1).
  `chunk-runner`: waiting is ending the turn with no tool call; never a
  background command, a poll or a monitor to wait; an agent has returned
  only when its hand-back message is there; a hash is real only when `git
  cat-file -e` says so; the stall rule applies to a hand-back message,
  never to an empty `git log`; never hand back while a launched agent has
  not returned. `tdd-implementation-lite`: a skill invoked inside a build
  (the map query) is a note, the turn goes on, the only final message is
  the hand-back. The orchestrator checks every hash on a runner's line
  before it writes the line or asks the owner anything built on it. Done
  when: cases `chunk-runner-waits-for-handback` and
  `orchestrator-runner-handback-unverified` pass and fail without the
  change.
- [x] A2 **Red CI is not done** (finding 2, the owner's draft of
  2026-11-12). A "CI watch" section in `delivery`, called by the
  orchestrator's E step after every push and by step 1b for an open pull
  request with red checks: wait bounded by the workflow's timeout plus 5
  minutes (no result is never green); green goes on to the comments; red
  reads the failing job (`gh run view --log-failed`, then the job page in
  Chrome, then the owner with the URL), writes the failing tests to
  `<records>/pr-ci-r<i>.md`, one fresh fixer told the platform difference
  and that the failing tests are not weakened, the gate, the push, the
  watch again; three rounds at most; the report leads with the CI state
  and the E line needs `CI green <sha>`. Done when: case
  `delivery-ci-red-not-done` passes.
- [x] A3 **The gate does not fail scope on the flow's own records**
  (finding 8): `validation_gate.py` exempts the orchestrator log and the
  sidecar. Done when: a tool test shows it and a real out-of-scope file
  still fails.
- [x] A4 **An issue fix has a convention and a scoped readiness gate**
  (findings 4b and 5): records prefix `issue<n>-`; `readiness_check.py`
  checks the documents and criteria the fix revised, lists older gaps as
  INFO and the orchestrator files them once as one issue; the
  numbers-on-waits check stops matching a button label. Done when: case
  `orchestrator-issue-fix-records` passes and the readiness tool tests
  cover the scoped mode and the false match.

Built 2026-11-12 on branch `phase-a-0.14.5`. The gate: 53 cases reached,
all with current evidence. Against main's skill text the four new cases
fail (0.88, 0.86, 0.77, 0.30 against bars of 0.97, 1.00, 0.97, 0.97), with
two limits to know: `chunk-runner-waits-for-handback` and
`orchestrator-runner-handback-unverified` fail there on the hash check
alone (the old orchestrator also declined to write the C line from a line
whose commit was missing, without the check), and no case can make a
runner wait, since a launch blocks under the eval (E2's replay case).
`delivery-ci-red-not-done` stops before the fixer.

**Test of 0.14.5: one issue fix on `personal-finance-tracker-3`, before any
of phase B is built.** Issue #49 (stopping soon after connecting waits the
full 10 s and leaves the claim), with #54 and #40 if the owner wants them
in the same fix. It is the right size and shape: it needs a design
decision, it touches the close and a wait (so the runner is exercised on
the code that tripped it), and its tests must pass on Linux. Measured
against the issue #33 run: no result named before its hand-back, no stall
message to a working agent, no readiness route about an untouched
document, the pull request never reported as built while a check is red,
and the owner's questions in the loop (7 last time). About $30 to $60.

**Run and reviewed 2026-11-13** (`~/.claude/kad-audit/reviews/2026-11-13.md`;
$33.17, 1 h 28 m to green CI, 34 launches). Held: no runner named a result
before its hand-back or started anything to wait (12 launches, five
wake-ups that were not the hand-back, one of them a 12-minute platform
stall); no stall message; no readiness route about an untouched document;
the pull request reported only after `CI green`; no owner question in the
loop; every record prefixed. **Not exercised, so not shown:** the stall
rule (no agent stalled), a false hash refused (none appeared), the CI
watch's red path (CI was green), older gaps filed as one issue (there
were none). The cold read's reliability score went from 3 to 4.

### After the issue #49 fix (2026-11-13), from its review

Small and mechanical, for the next plugin change that reaches each file:

- [ ] F1 **The gate reads an absolute `--allow` inside the project as the
  path relative to it** (finding 1): two of three runners passed the
  records directory as handed, absolute, and the gate failed scope on the
  run's own records; `--module-dir` and `--deviation-zone` the same way.
  Done when: a tool test in `validation_gate_test.py` shows it.
- [ ] F2 **The fixer cap says whether a gate fixer counts** (finding 4): a
  gate that fails after the r1 fix has no rule, and a runner that sent a
  gate fixer then left a regression unfixed under "no third fixer".
  Proposed: the cap counts review fixers; each gate gets its one fixer.
  Done when: a `chunk-runner` case with a gate failure after r1 passes.
- [ ] F3 **The log checker reads an r2 fix of several commits** written
  with spaces between the hashes (finding 5). Done when: a tool test.
- [ ] F4 **`cost_by_role.py --log` skips a session with no transcript**,
  names it and totals the rest (finding 6, second run). Done when: a tool
  test.

Decided by the owner 2026-11-13 (all three yes), to build with 0.15.0:

- [ ] F5 **A last fix that changes behaviour gets one diff-scoped review**
  (finding 2): the slice review's last fix is read by nobody, and the cold
  read's three unknown bugs and two of four mutation survivors were in
  it. Proposed as one more stop on C2's autopilot list: when the last fix
  touches a source file no finding handed to it names, or changes an
  exported signature; its findings are reported, not fixed in the loop.
  **The owner, 2026-11-13: yes, and "any change should always be
  reviewed".** So not conditional: every commit that changes source or
  tests after a scope's last review (a chunk's r2 fix, the slice review's
  last fix, a gate fixer's, a CI fixer's, a triage fix's) gets one
  diff-scoped review before delivery reports. Still to design, with C2:
  how the chain ends (proposed: that review's Critical and High stop for
  the owner or autopilot's one fixer, Mediums and Lows are filed, and a
  fix of its findings is reviewed the same way, capped). Done when: a
  case shows a last fix with a planted defect reviewed and the defect
  reported, and a clean last fix adding one review and no fixer.
- [ ] F6 **Delivery waits for an external review only where a bot has
  reviewed before** (finding 3; the owner ended a fifteen-minute wait on
  a repository with no review bot). Otherwise it says so and returns.
  The owner, 2026-11-13: yes.
  Done when: a case on the fixture's `gh` stub.
- [ ] F7 **The target-directory question** offers guesses as its options
  (finding 7): take the directory a project memory or `CLAUDE.md` names,
  and say so. The owner, 2026-11-13: yes. Done when: a variant of
  `orchestrator-asks-for-target` with the directory named in the
  project's memory takes it without a question, and the existing case
  still asks.

### Phase B, 0.15.0: the review rebalance (finding 10)

- [ ] B1 **Gate categories, picked per stack.** The plugin names the
  categories (type-aware lint, stricter compiler flags, complexity and
  length limits, duplication, unused code, changed-line coverage, test
  timeouts and random order, secret and workflow scans);
  `technology-bootstrap` picks the tool for the project's language from
  the survey's lists (a) and (b) and records it; the gate runs what the
  manifest names. Existing code is taken as the baseline so only new
  violations fail. Done when: the library fixture carries the checks, a
  planted violation of each category fails the gate, and a clean chunk
  passes.
- [ ] B2 **The chunk reviewer's brief is narrowed.** `code-review`,
  `test-quality-review` and `reliability-review` in the combined chunk
  review say what the gate already covers and do not report it; what is
  left is behaviour, names and comments that tell the truth, and the
  design. Done when: a case with a planted duplication and a planted
  behaviour bug gets the bug reported and the duplication left to the
  gate.
- [ ] B3 **The cold read inside the slice review.** D's stranger test
  becomes the full `cold_read.md` brief (whole app, no planning document,
  every suspicion probed by execution), plus one instruction: for each
  thing the slice adds, name the older code it runs alongside or depends
  on and probe the pair. Its confirmed bugs go to D's fix round. The
  audit's own cold read stays as a second reader. Done when: a case on the
  fixture with a planted bug where new code meets old code is found by
  execution.
- [ ] B4 **Mutation on the changed lines at D**, with the plugin's own
  `mutation_pass.py` (the survey could not verify Stryker on this stack);
  the test-quality reviewer reads the survivors and says which matter.
  Done when: a planted unguarded rule on the fixture comes back as a
  survivor and a D finding.
- [ ] B5 **Deferred items listed once, by a script**, in the pull
  request's body; the security, reliability and architecture reviewers
  stop restating them (25 of 83 findings last run). Done when: a case
  shows none restated.
- [ ] B6 **CI on a second operating system** in `ci-pipeline` (Linux and
  macOS), since the gate runs on one. Done when: the generated workflow
  has the matrix and the case passes.

**Check of B1 without a run:** apply the picked checks to
`personal-finance-tracker-3` at `main` on a scratch clone and record how
many violations each finds. This sets the baseline and shows whether the
readability findings of the last two cold reads (long functions, wide
lines) are what the limits measure. No tokens beyond the session.

### Phase C, 0.15.0: new capabilities

- [ ] C1 **The screen-change check** (finding 9; the owner 2026-11-12:
  pixel diff, hands-off, one fixed environment). At D for a UI-touching
  slice: every state with a saved baseline is re-driven by a scripted
  browser on made-up data and compared; a difference in a state the
  screen design does not list as changed is a finding; listed states
  replace their baseline. Baselines are made and compared in CI on Linux
  only. Done when: on the fixture, a style change meant for one state
  that moves another is reported, and the intended change is not.
- [ ] C2 **Autopilot** (finding 3, and finding 6's standing-finding
  verification; the owner 2026-11-12: as recommended). A standing
  `planning/autopilot.md`, asked once per project like the delegation
  file: the loop takes its own recommendation and logs "taken as
  recommended" for a budget overrun caused by a relaunch, one extra
  review to verify a standing Critical or High after the last fix, one
  fixer for a finding that verification confirmed, and a readiness route
  that changes no decision. It always asks when the recommendation
  changes a number or decision the owner approved, deletes or rewrites
  committed work, pushes anything red, or touches scope or requirements.
  Planning forks that carry a recommendation stay questions. Done when:
  cases show one stop taken without a question and one always-ask stop
  still asked.
- [ ] C3 **The concurrency pass in `architecture-design`** (finding 4a):
  for a change about concurrency or more than one process, the
  interleavings are listed and answered before the decision is final (two
  starts at once, a crash at each step, a stop during each wait, a
  leftover removed by hand, a reused process number). Done when: case
  `architecture-design-concurrency-interleavings` passes.

**Test of 0.15.0: slice 3 on `personal-finance-tracker-3`** (reconnect a
lapsed login, #14), which is UI-touching and so exercises B and C1
together. Baselines for C1 are captured from `main` before the slice
starts. Measured against the issue #33 run and slice 2 round 1: the cold
read's readability and reliability scores (3 and 3 for two runs), the
bugs the audit's cold read finds that the loop's did not, findings per
chunk, the share of added lines written by fixers (58%), reviewer and
fixer cost, the owner's questions in the loop, and any screen difference
outside the slice.

The light cadence arm, decided by the owner 2026-11-12: slice 3 runs on
0.15.0 under the normal cadence, and the light arm is measured on the slice
after, so the two changes are not measured at once.

### The eval suite itself (the owner, 2026-11-12: both agreed)

Asked while phase A's gate ran: how do we know the suite is not garbage,
too little or overkill. The chunk runner had six cases at 1.00 when two
real runners invented their agents' results, because a launch blocks under
`claude plugin eval` and runs in the background in a real session.

Decided by the owner 2026-11-12: no overhaul before the work list goes on
and no second eval folder; the suite is changed in place. The order:
phase A merged and tested on issue #49; E1; E2 on `chunk-runner` and
`delivery` with the replay case; phase B, its new cases written with a
known-bad reference and a regression-or-capability tag; suite tiers and
judge calibration after 0.15.0. Not taken from the survey: whole-loop
fixture runs per release (the audited real runs are that) and trajectory
matching against a reference path.
(Revised 2026-11-14, below: the `delivery` pass is no longer in this
order; E4 to E7 come after `chunk-runner`'s E2 and before phase B.)

- [x] E1 **Which cases have ever failed.** From the results history (the
  flat `gate-*.json` files and the archive), per case: runs, failures since
  its bar was recorded, and the graders that failed. A case that never
  failed is a candidate to merge or drop; no model time. Done when: the
  table is in `evals/README.md` and the candidates are listed for the
  owner.
  Done 2026-11-13: `evals/tools/case_history.py` writes the table
  (`evals/README.md`, "Which cases have ever failed"): of 164 cases, 78
  have failed since their bar, 60 never have, 26 have not failed in
  under six completed runs. Nothing is merged or dropped before E2's deletions have run.
- [ ] E2 **Mutation on the skills.** Delete one rule at a time from a
  skill and run the cases the skill reaches: a rule no case notices is
  unguarded, a case no deletion fails is dead weight. Start with
  `chunk-runner` and `delivery` (short, recently changed). Costs gate
  runs, so one skill per usage window. Each deletion that a case catches
  is kept beside that case as its known-bad reference (the skill with
  the rule removed must fail it), so "fails without the change" is a
  property the suite keeps. The owner, 2026-11-12: three runs per
  variant stay; a replay case for the runner's wait may be captured from
  a real `kad` session on the library fixture, outside the eval (never
  from a project's transcripts), and resumed with `history_file`. Done when: both skills have a
  survivors list and each survivor is a new grader, a dropped rule, or an
  accepted gap.
  `chunk-runner`, 2026-11-14: run. `evals/tools/skill_mutation.py` (rule
  deletions on a scratch copy, known-bad references, a free `check` in
  the pull-request workflow); 76 deletions on 101 deletion-case pairs at
  three runs: 6 caught and kept as 7 references, 1 half noticed, 69
  survivors, listed by why they survived with a proposal for each group
  in `evals/README.md` ("Rule deletions on a skill"); the proposals wait
  for the owner (changed prompts, five new graders, one new case with
  F2's, two rules to drop, two judges to turn into regexes). Two replay
  cases from a captured runner history ("Replay cases"): a replay cannot
  hold the wait, since the harness tells a resumed session its agent did
  not finish. Dead-weight candidates listed, none merged or dropped.
  **The owner, 2026-11-14: the `delivery` pass is not next.** The
  `chunk-runner` pass cost 309 runs and three usage windows, and most of what it taught
  holds for the whole suite without another run: a prompt that states
  the rule cannot test it, a judge on a one-line reply is noise, a rule
  whose state no case reaches is unguarded, the wait cannot be tested in
  the eval. E4 to E7 below come first; `delivery` gets a deletion pass
  only if they leave a gap there. Done when, as it now stands:
  `chunk-runner` has its survivors list (done), and the owner has
  decided the three questions PR #54 left open, none decided yet: which
  survivor proposals to apply, what to do with the weak `--planning`
  reference (it fails 4 runs of 6), whether the two replay cases stay
  (no deletion fails them).
- [x] E3 **What others do.** Survey of how comparable orchestrators and
  the wider field evaluate skills and agents:
  `.synthesis/eval-methods-survey.md`; its recommendations are for the
  owner to pick from before E2 is built.
  Done: the survey was written 2026-11-12, and the owner's picks from it
  are the decisions of 2026-11-12 above and of 2026-11-14 below.

Decided by the owner 2026-11-14, after E2 on `chunk-runner`: the suite is
still changed in place (no new eval directory). Every skill keeps cases;
where a tool can judge the output a tool does, where it takes reading a
judge stays, and each skill has to be shown to add something the bare
model does not: a skill that adds nothing is one to think about keeping.
At the end a pass of the suite should be cheaper and faster. The measure:
one run of every case, $54 at list prices on 2026-11-14 (139 cases seen
since 2026-11-10; 88% of the cost is the agent's own run, 12% the judges;
the 61 never-failed cases among them are $16 of it), reported again after
each step. (Corrected by E4 the same day: that figure counted the judges
twice. The measure is $45.70 for the same 139 cases, 82% agent and 18%
judges; E5 to E7 report against it.) Not taken: a run checker over real runs' records (the owner
was not convinced), and whole-loop fixture runs, as before.
What this plan does not yet give: `orchestrator` and `delivery` have had
no deletion pass and E6 does not apply to them, so their proof is owed
and not scheduled. E4 says, from reading their cases, which of their
rules a grader could notice; a deletion pass on those alone is decided
after it.

- [x] E4 **Sort the cases.** No model time. Per case: its graders by
  kind (judge, or a tool: regex, tool call, file), which judges a tool
  could replace and which take reading, whether the prompt states the
  rule it grades, what a run costs, whether it has ever failed (E1) and
  whether a deletion failed it (E2, where run). Done when: the list is in
  front of the owner, with the count of cases whose prompt needs
  rewording and the expected saving beside each proposed change.
  Done 2026-11-14: `evals/tools/case_sort.py` writes the table
  (`evals/README.md`, "The cases sorted") from the cases, the results
  history and `evals/tools/case_reading.json`, which holds the reading
  of all 166 cases and is the file to correct. 471 judges, 51 a tool
  could decide (about $0.77 a pass, an estimate; 72 runs failed on them
  alone); 9 prompts state the rule they grade and 23 state part of it;
  7 cases have never failed and cost $0.40 or more a run ($3.39 a pass).
  **The baseline is $45.70, not $54**: a run's cost already includes its
  judge cost and the $54 added the two (agent 82%, judges 18%). The
  proposals, the order for E5, the skills E6 should take first, which
  `orchestrator` and `delivery` rules a grader could notice, and the
  grader findings (none fixed) are in that section; all wait for the
  owner.
- [ ] E5 **Judges a tool can replace become tool checks.** Starting with
  the two hand-back judges that fail correct lines
  (`stops-with-the-decision-on-the-line`, `hand-back-is-the-one-line`).
  If the eval's grader kinds cannot hold a check, the gate runs a
  per-case script on the run's kept folder and counts its result with
  the graders (to verify against the CLI's documentation first). Prompts
  that state the rule they grade are reworded here. Done when: every
  judge E4 marked replaceable is replaced, each changed case has its
  gate run, and the re-run rate of the gate and the cost of one run of
  every case are reported before and after.
- [ ] E6 **With and without the plugin, skill by skill.** `--ablation
  with-without` at three runs, for the review, requirements and design
  skills; not for `orchestrator`, `chunk-runner` and `delivery`, where a
  bare model cannot know the protocol and rule deletion is the proof.
  One skill or family per usage window (about 1,000 runs for the whole
  suite). The CLI scores each arm against the same graders and never
  compares the two outputs, so equal scores are not yet "adds nothing":
  before a skill is listed as matched, its paired outputs are read side
  by side with `evals/tools/pairwise_judge.py`, and that judge's cost is
  counted. Done when: each such skill has its difference recorded per
  case with the pairwise verdict, the skills the bare model matches are
  listed for the owner to keep, cut down or drop, and the cost of one
  run of every case is reported again.
- [ ] E7 **Retire or merge what guards nothing.** From E1, E2, E4 and
  E6: a case that has never failed, that no deletion fails and that the
  bare model passes as well. Each candidate is named with the evidence
  that exists for it: a deletion result only where its skill has had a
  pass (`chunk-runner` so far), a bare-model result only where E6 ran;
  a case with neither is not a candidate yet. Nothing is dropped without
  the owner's word. Done when: the suite's full-pass cost is reported against the
  $54 baseline and each retired case is named with its reason.

Phase B's new cases are written after E4: the prompt names the state and
leaves the action to the skill, a tool grades what a tool can, and each
carries a known-bad reference and a regression-or-capability tag, as
decided 2026-11-12.

### Open on the project

Issues #49 to #56 from this review (filed 2026-11-12); #43 to #47 from the
fix itself; pull request #48 (records only) to merge or close.
