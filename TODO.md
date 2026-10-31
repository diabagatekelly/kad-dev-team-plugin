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
eval case in PR 3, and v4 is not done (0.7.0 not used for slice 2, this
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
Node 24 is needed for the fixture's test flag (`evals/tools/mac-gate.sh`
puts Homebrew's on the path). The first calibration pass (2026-10-31, one
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
chunk-loop, delegation-with-file and tdd cases are recorded from WSL; the
scripts gained a working-git fallback so the gate and the recorder at
least run there. Bars recorded from the Mac: the six planning and review
cases (K2 in `evals/TODO.md`); the rest wait for the WSL run.

- [ ] 3.1 Cases 1–12 on `evals/fixtures/library-app/`, each with graders, per `evals/README.md`; bars recorded with `record_thresholds.py` after calibration.
- [x] 3.2 `evals/tools/cost_by_role.py` (copy from `audit-docs/personal-finance-tracker-2-slice-1/plugin-review/tools/cost_by_role.py`; per-model prices; prints the E-line total).
- [x] 3.3 Rewrite or retire the v3 cases that assume six reviewers per chunk or "until clean" rounds; the two routing cases' A step gains the delegation question and the readiness gate.

## After the PRs

- [ ] 4.1 Run `personal-finance-tracker-2` slice 2 on 0.7.0 with the budget line; audit it the same way (`audit-review` skill; the audit-docs tools); compare the E-line cost and the §10 estimate.
- [ ] 4.2 Decide D9 phase 2 (a chunk-runner agent per chunk) on the orchestrator's measured context from 4.1 (> ~250k tokens → build it).
- [ ] 4.3 Open items from run 2, in the project not the plugin: PR #2's issue-links placeholder, the untracked `pr-r1-comments.json`, the missing E line, the three suspected bugs in repo 2 (orphaned vault row before the record write; `complete()` without a held claim; the year missing from the date column), repo 1's single-account rule and cursor persistence.
