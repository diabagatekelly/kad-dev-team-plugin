# Design: implementation flow v4 — design done before the build, one review that earns its cost, production-grade done

Internal design, written 2026-10-25 after the audit of the first real run of
v3 (the chunk loop) on `personal-finance-tracker-2` slice 1. It amends
`implementation-flow-v3.md`; what v3 says and this document doesn't change
still stands. The work list that implements it is `TODO.md` at the repo
root. Status: proposal, for the owner to approve item by item; §13 lists
the questions only the owner can settle, with the default this design
assumes for each.

Evidence is in the audit-docs repo, `personal-finance-tracker-2-slice-1/plugin-review/`:
`2026-10-25-slice-1-review.md` (consolidation), `-implementation-flow-review.md`
(rule-by-rule), `-implementation-churn.md` (numbers), `-planning-review-entries-1-16.md`
and `-17-27.md`, `-code-assessment-repo1-…` and `-repo2-…`, `-cost-by-role.md`.
Block numbers, commit hashes and per-finding proposed wording are there; this
document only carries what is needed to decide and to build.

## 1. What the first v3 run showed

Three failures were named by the owner: not production quality, too costly,
too slow. One paragraph of evidence each, then the finding underneath all
three.

**Too costly: $346 against $147 for run 1, for a slice about 1.2× the
size.** The role breakdown: reviewers $184 (53%: 219 Opus runs, six
reviewers × 31 rounds plus three pre-work accessibility reviews),
orchestrator $70 (20%: a long-lived session whose context reached 563k
tokens, mostly cache reads of its own record-keeping), Sonnet builders and
fixers $52 (15%), consults $16, Low filing $24 (four Opus agents triaging
452 Low lines into 203 issues). Three of the six reviewers (architecture,
security, accessibility) produced 28 actionable findings in 93 runs and 239
Lows: about $80 for 0.3 actionable findings per run. Decision 5 of v3 held
(Sonnet built, Opus reviewed); the saving it produced was spent several
times over on review volume.

**Too slow: 14.5 h wall clock (2 h planning, 12.6 h implementation; 8 h 20 m
net of a 3 h 38 m context-clear pause) against 7 h.** Of the 10.5 h chunks
and slice review took, about 4 h was six reviewers running in parallel,
about 2 h fixers and gates, about 1.5 h mid-build design consults, the rest
builds and record-keeping. Fix rounds averaged 3.4 per scope (v3 said
"until clean, capped at five"; its own §4a named a one-round fallback "if
the churn returns": it returned). Every round re-ran all six reviewers on
the chunk.

**Not production quality: both repos score the same on an independent
read (architecture 4, tests 4, security 4–4.5, reliability 3, developer
experience 3 of 5).** Each has two or three real bugs the reviewers missed,
and in both repos the worst one sits at the same seam: the use case and the
adapter each do the right thing alone and the wrong thing together (repo 2
stores the encrypted token before the connection record, so a failed record
write orphans a vault row and "nothing stored when connecting fails" is
false; repo 1 lets the API create a second connection the UI merely hides).
619 tests did not see it because every test either fakes the feed at the
port or tests the adapter alone; six reviewers did not see it because each
reads one side of the seam. The rest of "not production" is the absence of
boring things no step owns: no README, no linter or formatter, ~520 lines of
browser JavaScript inside TypeScript template strings, 17% of src lines are
comments (522 of 3,028, mostly WHAT-comments: "The owner stopped loading
history."), 15 comments cite "decision 7" or a planning file a reader of
the code cannot resolve, and repo 1 throws away the cursor and transaction
id the next slice needs.

**The churn the fix rounds generated.** 40% of actionable findings (79 of
196) were raised against fix commits, and 68% of those were classed as
regressions: the fixer is the second-largest source of defects after the
builder. Fixes wrote 46% of all code lines ever added and 44% of the lines
surviving at HEAD; 31% of src lines written on the branch were later
deleted; `src/index.tsx` had 276 lines written for 28 that remain. Chunk 2
went from 18 actionable findings to 19 after its first fix. Fix rounds
added 16% of the tests but 35% of the test code (test/src ended at 2.52
against repo 1's 1.10). Lows never converged: each "clean" round still
raised 3–34, one `live-status.ts` Low was re-raised six times unchanged.

**The design gaps the build had to fill.** About twenty decisions were
made during C and D: the claim lifecycle (6), the pull as its own request
(7, 7b), an unusable Plaid reply (8), history status (9), institution
errors (10–13), every reliability number (poll, give-up, retries, stale),
six screen states, ~22 accessibility criteria. The planning reviews show
most were knowable at planning time: security and reliability contradict
each other on the approved-but-not-exchanged window (decision 6); the
per-request budget question was routed design → reliability → bootstrap →
"the implementer" and nobody owned it (decision 7); the reliability skill's
own "a dependency lies" item was not applied (decision 8); "retry a few
times" carried no number; two failure states the criteria name had no
mockup (states 9/9b/9c). v3 has no step for a mid-build design decision;
the orchestrator invented consult → apply → log → commit, and when
`software-architect` correctly refused to write a decision on an agent's
word, the orchestrator became the scribe for 17 planning commits (~110
edits), 12 plan-widening commits, a map extractor and eight helper
scripts: the one thing v3 said it must never be.

**The finding underneath.** Paying 2.3× for 7× the review volume bought no
measurable quality tier. The determinant of quality was the model's base
capability plus test-first discipline; the review volume converted into
Lows and churn, not into better code. So the money has to move: upstream
into design completeness (planning cost $19 of the $346), and to the seam
and the finish (integration tests, running the app, README, lint). The
review loop keeps only what the data says earned its place: the two
code-level reviewers, one round.

## 2. Decisions this design implements

| # | Decision (2026-10-25, proposed) | Replaces in v3 |
|---|---|---|
| D1 | **One reviewer per chunk round**, an Opus agent that invokes `code-review` and `test-quality-review` always and `reliability-review` when the chunk's territories include HTTP, storage or error handling, and reports one findings file. Architecture, security and accessibility review run **once, at D**, on the whole slice. | Decision 3 (three to six reviewers per chunk) |
| D2 | **One fix round per scope, regressions-only re-review.** The re-review reads the fix diff only; a pre-existing finding it raises is recorded as standing, never fixed in this scope. A standing Critical or High stops the flow for the owner; standing Mediums are listed in the PR body. | Decision 4 / §4a (until clean, capped at five) |
| D3 | **Lows are not collected per chunk.** Per-chunk reviewers report Critical, High and Medium only, at most eight per report. The D reviewers may report Lows; they go in the PR body under "Known Lows", grouped by theme, and are not filed as issues unless the owner says so (§13). | Decision 4's Low list and Decision 7's "files the Lows as issues" |
| D4 | **A design-readiness gate before B.** Mechanical, orchestrator-run, from the planning documents: every acceptance criterion and every failure path a placeholder names maps to a component the design names; every retry, wait and give-up has a number; every state the security, reliability and accessibility files name has a mockup; no open question is routed to "the implementer". A failed check is a backward route to the owning persona before any builder launches. | nothing (new) |
| D5 | **A mid-loop design step with a delegation file.** When a round's findings disagree over a rule no planning document states, the orchestrator launches the owning persona with the findings by path and `planning/delegation-slice-<nnn>.md`; the persona writes its own document in place and commits; the orchestrator logs one line. The delegation file is written at A on the owner's say-so and is what lets a persona honour "decide with the owning agent, don't ask me". | the orchestrator applying personas' edits itself |
| D6 | **Every chunk includes a seam test, and the loop runs the app once per chunk.** The chunk plan's Done-when names at least one test that goes through the real composition root with the real adapters, faking only the external service at its wire boundary (HTTP, not the port). The gate runs it with the suite. The one browser-driving step per chunk (today accessibility-review's) becomes the smoke run: start the app as the owner would, drive the chunk's Done-when, report what broke. | nothing (new) |
| D7 | **A Definition of Done at D, production-grade.** Before D's reviewers run: README that takes a stranger from clone to running; linter and formatter configured, clean, in the gate and in CI; typecheck in the gate; no application code inside string literals; no comment that cites a planning document or decision number; comment density reported; everything the next slice needs persisted (named by the design). Each is a mechanical check or a one-line reviewer question; a failure is a named fix. | nothing (new; `operational-readiness` stays for the deployment path) |
| D8 | **Comments: zero by default, for writers as well as reviewers.** `tdd-implementation` and `-lite` adopt `why-comments` as a writing rule; a comment is written only for what the code cannot say (a non-local constraint, an external bug, an invariant a future edit could break). `code-review` rates a WHAT-comment Medium, not Low. The gate reports comment density per commit (report-only, threshold in §8). | `code-review`'s Low for "a comment that's redundant but not false" |
| D9 | **Ship the orchestrator's tooling and bound its context.** `rounds_record.py` (reviewer report → sidecar → counts), typecheck/lint/comment-density in `validation_gate.py`, a map extractor per language in `map-update`, `sandbox_check.py --write-settings` never sets `sandbox.enabled` on exit 2, a named pause/resume procedure. Phase 2, if the orchestrator still exceeds ~250k tokens on a slice after D1–D3: a chunk-runner agent per chunk (build → gate → review → fix → one-line hand-back). | the orchestrator writing scripts in the project |
| D10 | **A budget on the A line, enforced.** Wall-clock and launch caps the orchestrator can measure: default 5 h of loop time, 2 reviewer launches per chunk, 1 fixer per scope, 8 consults per slice. Exceeding one ends the flow at the next chunk boundary with the branch as it is and the report saying what is built. The dollar figure is computed after the run by `evals/tools/cost_by_role.py` and written on the E line. | nothing (new) |
| D11 | **Delivery finishes in the foreground.** Nothing in E runs in the background; the PR body is edited with its links, the E line written and the audit sync run in the turn that files the last issue. | §4.E as run (background filing outlived the session) |
| D12 | **Planning fixes from the two planning reviews**, listed in §9: revise in place while the document is still yours; the full question pass before writing; walk the problem doc's open questions; owned documents stay owned; consult answers and stage reports as visible text; one question per `AskUserQuestion`; a no-repo target routes to `repo-bootstrap`; the readiness checks of D4 as skill wording in `architecture-design`, `reliability-requirements`, `screen-design`, `requirements-refinement`. | the 0.6.0 text of those skills |

| D13 | **Fakes only at the system boundary.** A test may fake the external service at its wire boundary (HTTP), the clock, randomness and a browser-only API; it never fakes the project's own modules when the real one can run in the test (repo 2's local D1 can; repo 1's SQLite can). Port fakes of own code are allowed only for a branch the seam test cannot reach, and each is named in the Test List with the branch it exists for. `test-quality-review` keeps a **fake inventory** per chunk (every `vi.fn`/`vi.mock`/`Fake*`/`stub*`/`new Function` and what it replaces); a fake of own code with a real local equivalent is High, a hand-rolled DOM harness is High and points at D7.4 (the code is in a string because it has no module). Real run: 24 `vi.*` doubles, 6 hand-rolled fakes, 5 `new Function` harnesses, six test files over 500 lines (two over 990). | `test-quality-review`'s over-mocking category, which had no rule about own-code fakes |
| D14 | **Simplicity measured, not only judged.** The gate reports per commit, report-only: files over 300 non-blank lines, functions over 40 lines, lines at nesting depth ≥ 4, and the comment density of §8. D7 acts on the slice figures: every function over 80 lines and every file over 300 is a named `code-review` finding ("more than needed" / size) for the D fixer; depth-≥4 share over 10% is a Medium. Real run, repo 2: 33 src files, median 57 lines, 1 file over 300 (`styles.ts`), 3 functions over 40 (longest `routes.tsx` 107), 7% of lines at depth ≥ 4, max depth 8. Repo 1: 42 files, 11 functions over 40 (longest `TransactionsScreen.tsx` 196, `plaid-bank-feed.ts` 108), 13% at depth ≥ 4, max depth 12. Both are within reach of the limits; the limits stop the drift the fix rounds caused (`connect-an-account.ts` 283 lines after 19 commits). | `code-review`'s size category without numbers |

Kept from v3 without change: Sonnet builders and fixers on fresh contexts;
Opus for review; a commit per chunk and per fix; the gate; sandbox check
first with the logged opt-out; `pr-writeup`, `ci-pipeline`, `delivery`;
the planning spine and the state table; the stall rule; the sidecar.

## 3. The row's procedure, v4

Only the steps that change are written out; everything else is v3 §4.

### A. Start

1. Sandbox check first, as v3. `--write-settings` on exit 2 writes only the
   deny rules (D9).
2. Policy question, **one question per `AskUserQuestion`**: settings, then
   sandbox, then policy, then (new) **delegation**: "May decisions that
   come up during the build be settled with the owning persona without
   asking you? Each is logged and you can overturn it." On yes the
   orchestrator writes `planning/delegation-slice-<nnn>.md`: the owner's
   words, the date, the slice, what it covers (design, criteria, screen
   states, accessibility criteria) and what it never covers (scope,
   requirements, anything that changes a confirmed requirement: those are
   backward routes to the owner as today). Committed in the planning
   commit. Skip the question when the owner's message already said it;
   write the file anyway.
3. **Budget** (D10): the A line records `budget — 5h, 2 reviews/chunk, 1
   fix/scope, 8 consults` (defaults; the owner may name others in the
   message). The orchestrator counts launches and reads the clock at every
   chunk boundary.
4. Branch and base as v3. If the target is not in a git repository or has
   no `origin`, stop: `flow not started: no repository`, route to
   `release-engineer:repo-bootstrap` (phase 2 skill, built now in its
   smallest form: `git init`, default branch, `.gitignore`, `gh repo
   create` private, first push; decided with the owner).
5. **Design-readiness gate** (D4, §5) before B. A failed check is a
   backward route, logged as its own entry, to the persona the check
   names; the flow resumes at A.5 when it passes. The A line records
   `readiness — PASS` or the checks that failed and the entries that fixed
   them.

### B. Plan

As v3, plus: each chunk entry's **Done when** names at least one **seam
test** (D6, §6) by name, and its **Touches** line is what selects
`reliability-review` for the chunk (D1). The plan check gains one
mechanical item: every chunk has a seam test named.

### C. Chunks, one at a time

1. **Build** as v3. The builder writes comments under the §8 rule and
   names each plan deviation in its report section; it never edits the
   plan entry. The chunk's seam test is part of its Test List.
2. **Gate** as v3, with `--allow` = the chunk's Files line **plus the
   design's module directories** as B's check lists them. A file inside
   those directories but off the Files line is reported as `scope:
   deviation <path>` and recorded on the C line, not a FAIL; a file
   outside them is the FAIL that goes to the fixer once. The gate also
   runs the project's `typecheck` and `lint` scripts when they exist and
   reports comment density (§8). Deletes the "add it to the plan entry"
   mechanism.
3. **Review** (D1): one Opus agent, `kad-dev-team:code-reviewer:AGENT`,
   handed the chunk's diff, the files it touched, the slice's criteria
   and design by path, and the instruction to invoke `code-review`,
   `test-quality-review` and (when Touches includes HTTP, storage or error
   handling) `reliability-review` in turn and write **one** report in the
   shared format (§4), Critical/High/Medium only, at most eight findings,
   ranked. In parallel, the **smoke run** (D6, §6): one agent starts the
   app as the README says, drives the chunk's Done-when through the real
   interface (browser for UI, HTTP otherwise), and reports PASS or what
   broke as findings in the same format. If the chunk's Touches includes
   UI, the smoke agent is `accessibility-engineer` and also checks the
   chunk's accessibility criteria on the built screen; otherwise it is
   `tdd-coach`. Two launches per chunk round, never more.
4. **Fix** (D2): one fresh Sonnet fixer gets every finding of both reports
   verbatim and commits. Gate. Then the **re-review**: the same single
   reviewer kind, on the fix's diff only, classifying each finding by hunk
   as regression or pre-existing (the sidecar's `class`). Regressions go to
   a **second and last** fixer; pre-existing findings are recorded as
   standing. After the second fixer, the gate runs and the chunk is done:
   no third review. A standing Critical or High stops the flow before the
   next chunk and is reported for the owner; standing Mediums go to the PR
   body's "Standing" list.
5. **A gap that stops a fix** (D5): when the reviewer's or the fixer's
   report says a finding cannot be settled because no planning document
   states the rule (the reviewer reports it as `needs-decision: <owner
   persona>` instead of a severity), the orchestrator launches the owning
   persona once (`software-architect` for structure and interfaces,
   `devsecops-engineer:reliability-requirements` or `:security-requirements`
   for criteria, `ux-designer:screen-design` for a state, `accessibility-
   engineer:accessibility-review` for its criteria) with the findings by
   path and the delegation file. The persona writes its own document in
   place, commits `Decision <n>: <title>` and hands back the hash and one
   sentence. The orchestrator writes one indented line under the C line,
   `decision <n> <sha> (<persona>)`, and passes the hash to the fixer. One
   consult per persona per round; the budget counts them. Without a
   delegation file the persona hands back a recommendation and the flow
   stops for the owner, as `software-architect` did in the real run.
6. **C line**: as v3, plus `deviations <n>`, `smoke PASS|<n> findings`,
   `standing <C/H/M>`, `decision` lines, and `budget <h>h <launches>`.

### D. Slice review

1. `map-update` with the shipped extractor (D9); no extractor for the
   language means the map lists modules from the tree with no edges and
   says so; the orchestrator writes nothing.
2. **Definition of Done** (D7, §7), mechanical checks first; each failure
   is a named fix for one Sonnet fixer, then the gate. Only then:
3. The six reviewers once, on the whole slice diff, the map diff and the
   slice documents, as v3; Lows allowed here. One fix round for
   Critical/High/Medium, regressions-only re-review as C.4. Standing
   Mediums and the Lows go to the PR body.

### E. Delivery

As v3 §4.E with D11: the Lows are **not** filed as issues by default (§13);
standing Mediums are filed, one issue each, with the `tech-debt` label;
PR body edited with the links, E line written, `cost_by_role.py` run on
the session transcripts and its total written on the E line, audit sync
run: all in the same turn. Nothing in E is launched in the background.

### Pausing and resuming

New, named: on a context clear, a rate limit or a session end mid-loop,
write `<reviews dir>/handoff-slice-<nnn>.md` (A–E state, the next step,
the standing list) and a memory pointer; on invocation with a handoff
present, resume from it and append `Resumed <date> at <step>` under the
entry. The real run improvised exactly this and it worked.

## 4. The review in detail

**Why one agent.** Six reviewers each loaded the chunk's diff, files,
criteria and design into their own context (accessibility: 53M cache-read
tokens over 26 runs). One agent reads once and applies three lenses. The
three lenses kept are the ones that produced 71% of the actionable findings
and every defect the suite had missed (the Worker that could not call
Plaid, the empty-cursor pull abort, the claim release across windows came
from test-quality, reliability and architecture; architecture's one real
catch in 31 runs moves to D, where it has the whole slice to read).

**What one review reports.** The shared format every review skill already
states (`### <title>` / `**Severity:**` / `**Location:** path:line` /
`**Category:**` / `**Suggested fix:**`), one file per round
(`chunk-<k>-r<n>-review.md`), ranked, at most eight findings, Critical/
High/Medium only. A finding the reviewer cannot rate because the rule is
undecided is `**Severity:** needs-decision (<persona>)`. The smoke report
uses the same format (`chunk-<k>-r<n>-smoke.md`). `rounds_record.py` (D9)
parses both into the sidecar and prints the counts for the C line, so the
orchestrator never parses a report itself.

**Why one round.** v3 §4a chose "until clean" and named the fallback. The
run's numbers (3.4 rounds mean; 68% of fix-round findings regressions; a
fix made chunk 2 worse) are the churn it said would trigger the fallback.
One fixer, one regressions-only re-review, one more fixer at most: a chunk
costs two reviews and at most two fixes, the stage ends on a known state,
and pre-existing findings the re-review surfaces are recorded instead of
starting a new round of rewriting. Expected rounds: 7 scopes × ≤2.

**Why no Lows per chunk.** 585 Lows, 75% of all findings; none converged;
205 issues nobody will read; $24 to triage them; 22,230 lines of report.
Lows exist to be read once by a human at the PR, which D gives them.

## 5. The design-readiness gate

Run by the orchestrator at A.5 from the planning documents, mechanical
where it can be and a one-line persona question where it cannot. Each item
names the persona a failure routes to. Thresholds are the real run's
gaps, each of which cost a mid-build decision.

| Check | How | Fails to |
|---|---|---|
| Every acceptance criterion in the slice, security, reliability and accessibility files is quoted (or its Given/When/Then opening) under a component in the design's Structure or Boundaries | text match against the design doc | `software-architect:architecture-design` |
| Every failure path a placeholder or failure-mode row names has a structural home: which component records it, what state it leaves | design doc names the row's failure in Structure | `software-architect:architecture-design` |
| Every retry, wait, poll, give-up or stale window in the reliability criteria has a number or an explicit "unbounded, owner approved" | regex for `a few`, `several`, `a while`, `again` without a number in the same criterion | `devsecops-engineer:reliability-requirements` |
| Security and reliability agree on every failure path both mention (what is stored, what the user sees) | the reliability doc cites the security criterion it touches, or hands the overlap to the architect | `devsecops-engineer:reliability-requirements` |
| Every state the security, reliability and accessibility criteria name has a mockup in `visual-ux/` | the screen design's state list covers the criteria's named states | `ux-designer:screen-design` |
| No open question in any planning document is routed to "the implementer", "the builder" or a stage that has already run | text match | the document's owner |
| The design names what the next slice needs persisted from this one (identifiers, cursors, provenance) | a "Kept for later slices" line exists | `software-architect:architecture-design` |
| An external data provider's unusable reply (missing or malformed fields) has a failure-mode row | row exists when the design names an adapter to an external service | `devsecops-engineer:reliability-requirements` |

The same checks become skill wording (D12, §9) so the planning stages
pass them the first time; the gate is what catches the ones they still
miss. A gate run costs no model calls beyond the orchestrator's own turn.

## 6. Seam tests and the smoke run

**The gap, precisely.** In repo 2, route tests run the real Hono app, use
case tests fake the feed at the port, adapter tests run the adapter alone
against hand-written JSON. No test wires the real use case to the real
Plaid adapter, the real vault and the real store with only Plaid's HTTP
faked, which is where the orphaned-token bug lives. Repo 1 has the same
shape (the second-connection bug lives between the API route and the use
case). Neither repo has a test that starts the built app.

**The rule, in `tdd-implementation` and `-lite`.** Each chunk's Done-when
names at least one **seam test**: a test that builds the app through its
real composition root (the same function `index`/`main` uses), with the
real adapters and the real local store, faking **only** the external
service at its wire boundary (an HTTP server or fetch stub that speaks the
provider's protocol, recorded or hand-written) and driving the chunk's
behaviour through the app's own interface (an HTTP request to the route, a
rendered page). The Test List puts it first in RED for the chunk's main
path, so the builder designs the composition root to be constructible in a
test. Port fakes stay for the use case's own branches; they do not count
as the seam test. `test-quality-review` gains the check: a chunk whose
tests all fake at the port and none through the root is a High ("the seam
is untested").

**The smoke run, in the orchestrator's C.3.** One agent per chunk round
starts the app as the README says (`pnpm dev` or the documented command),
waits for it, drives the chunk's Done-when through the real interface
(browser via the Chrome tools for UI, `curl`/fetch otherwise), checks the
accessibility criteria when the chunk touches UI, stops the app, and
reports in the review format. It is the one browser-driving launch per
round, replacing the per-round accessibility review; accessibility's
design-time criteria are checked at D on the whole screen. A smoke run
that cannot start the app is a Critical for the fixer and a README finding
for D7.

## 7. Definition of Done (production-grade), at D

Mechanical checks the orchestrator runs before D's reviewers, each a named
fix for one Sonnet fixer when it fails, in one batch:

1. **README** at the repo root with: what it is, prerequisites (runtime,
   package manager, external accounts and where their secrets go), clone
   to running in numbered commands, how to run the tests and the checks,
   where the data and logs live, what this slice does and does not do.
   Written by `docs-writer:user-facing-docs`'s sibling `readme` (new, small)
   from the project's manifest, the design doc and the slice; a stranger
   test: the smoke agent follows the README on a clean clone in the last D
   round.
2. **Linter and formatter** configured for the stack (`technology-bootstrap`
   names them as deferred-until-D7 categories), clean on the tree, wired
   into the gate's `lint` step and into CI.
3. **Typecheck** in the gate and CI (already in `ci-pipeline`; the gate
   lacked it).
4. **No application code inside string literals**: a mechanical scan for
   `<script>` bodies, `new Function`, or multi-line template literals that
   contain statements, in `src/`. Found: a High for `software-architect`
   to place the code in a real module the build serves.
5. **No planning references in code**: regex for `decision \d`, `ADR-\d`,
   planning file names, "criterion" in `src/`. Found: a comment to delete
   or rewrite as the WHY it stands for.
6. **Comment density** from the gate's report over the slice: above the §8
   threshold is a `code-review` pass on comments only (invoking
   `why-comments` on every file over the line).
7. **Persistence for the next slice**: the design's "Kept for later slices"
   line against the schema (mechanical: the named columns exist). Missing:
   a High for the fixer.
8. **Secrets and fixtures**: the existing `security-review` checks, plus
   `wrangler.toml`/env defaults point at the local or sandbox environment,
   never production.
9. **Tests are not padding**: `test-quality-review` at D reports
   test-to-src line ratio and the share of tests that assert on source
   text, package.json or script bodies; above 10% is a Medium with the
   tests named.

`operational-readiness` is unchanged and still runs when a deployment path
exists; D7 is the slice-level floor beneath it. The PR body gets a
"Definition of Done" table with each check's result.

## 8. The comments rule

`why-comments` already says "default to zero comments" and lists the four
reasons a comment may exist. v4 makes it the writer's rule, not only the
reviewer's:

- `tdd-implementation` and `-lite`, GREEN and REFACTOR: "Write no comment
  unless `why-comments` would keep it: a non-local constraint, a workaround
  for a named external bug, an invariant a future edit could break, a
  rejected obvious alternative. A sentence that restates the next line, a
  field or a function is deleted before the commit. Never cite a planning
  document, a decision number or a criterion in code; put the WHY itself."
- `code-review`: a WHAT-comment is **Medium** (it costs every reader
  time and goes stale); a comment citing a planning reference is Medium;
  a false comment stays Critical.
- `validation_gate.py` reports comment lines / non-blank lines for `src/`
  over the commit range (report-only). D7 acts when the slice's figure is
  above **5%** (the real run: 17%; a 3k-line codebase with ~150 WHY
  comments is the ceiling this allows).

## 9. What changes where

### `skills/orchestrator/SKILL.md`

- A: one question per `AskUserQuestion`, in order; the delegation
  question and file; the budget line; the no-repo route; the
  design-readiness gate (§5) as A.5.
- B: the plan check's seam-test item.
- C: review as one launch plus the smoke launch (§3.C.3); fix as one
  round plus regressions-only re-review (§3.C.4); the gap step (§3.C.5);
  gate scope as Files line plus module dirs with deviations; the C line's
  new fields; `rounds_record.py` named as the only way counts reach the
  log.
- D: Definition of Done (§7) before the reviewers; one round.
- E: no background work; Lows to the PR body; standing Mediums filed;
  cost on the E line; sync in the same turn.
- Pausing and resuming section.
- The log entry format: one bold line per step, indented plain bullets
  for decisions and corrections, never a second bold A/D/E line.
- Delete: "every Low becomes an issue"; "until clean, capped at five"; the
  per-round territory table for six reviewers.

### `skills/tdd-implementation/SKILL.md` and `tdd-implementation-lite/SKILL.md`

- The chunk plan: Done-when names the seam test; Touches drives
  `reliability-review`.
- Building one chunk: the seam test first in the Test List; comments
  under §8; deviations named in the report, the plan entry never edited.
- Reporting: `Fix r<i>` lines directly after `Commit`, no `### Lows`.

### `skills/code-review/SKILL.md`, `test-quality-review/SKILL.md`, `reliability-review/SKILL.md`

- The shared report format stated identically in all three (and in
  `security-review`, `architecture-review`, `accessibility-review`), with
  `needs-decision (<persona>)` as a severity value.
- `code-review`: WHAT-comment and planning-reference comments Medium.
- `test-quality-review`: the seam check (§6); the padding measures (§7.9).
- A "combined review" paragraph in `code-review` for the chunk reviewer:
  invoke the three skills in turn, one report, eight findings.

### `skills/accessibility-review/SKILL.md`

- The smoke-run mode: start the app, drive the chunk's Done-when, check
  the chunk's criteria, report in the shared format; the full design-time
  review runs at D only.

### Planning skills (D12, from the planning reviews)

- `requirements-refinement`: the full question pass before writing (a
  question not yet asked is owed, not "Not yet confirmed"); walk the
  problem doc's Open questions; revise in place while the document is
  still yours, supersede once a later stage has built on it (same wording
  in `scope-map`, `adr` and orchestrator step 3; `vertical-slicing` says a
  slice file is revised in place, never copied to `-v2`).
- `architecture-design`: every criterion and placeholder failure path has
  a structural home or an Open question naming who decides and a re-entry
  note; a "Kept for later slices" line; a recommendation whose consequence
  changes a confirmed requirement is a hand-back to `product-manager`, not
  a consequence to accept; a decision "informed by a consult" names the
  Skill call; the consult's answer is recorded in the decision.
- `reliability-requirements`: numbers on every retry/wait/give-up; read
  the security file first and reconcile or escalate overlaps; the unusable-
  reply row; a question routed here is answered here or re-routed with a
  reason, never to the implementer.
- `screen-design`: every state the security, reliability and accessibility
  files name gets a mockup; leaving out a shell element the design system
  declares is a proposal to `design-system`.
- `security-requirements`, `reliability-requirements`,
  `accessibility-review`: the slice's placeholder line becomes a one-line
  pointer and nothing else is edited; the story is `docs-writer`'s; a
  criterion a fork narrows is a finding for `product-slicer`. Consult
  answers are visible text under `## Consult answer`.
- `problem-framing-doc`: gather the problem through `AskUserQuestion`, one
  question per section.
- `map-query`: emit the report header even for "no map", after checking
  the path.
- Orchestrator step 4: tell a routed skill where to save and nothing about
  other stages' documents; pass "via `AskUserQuestion`" to every routed
  skill. Step 5: re-inspect without asking; report as visible text; when
  one fact ripples through requirement → slice → story, one entry per
  owner, one continue prompt at the end. Outcome bullets: §13.

### `skills/orchestrator/scripts/`

- `validation_gate.py`: `--module-dir` (repeatable) for the deviation
  rule; `typecheck` and `lint` from the manifest; comment density line;
  the seam test is just part of the suite.
- `rounds_record.py` (new): parse a review or smoke report in the shared
  format → sidecar rows with `class` against a commit range → C-line
  counts; `--standing` lists what is carried.
- `readiness_check.py` (new): §5's mechanical items over the planning
  directory → PASS or the failing checks with the persona each routes to.
- `done_check.py` (new): §7's mechanical items (README sections, lint and
  format config present and clean, code-in-strings scan, planning-
  reference scan, comment density, persisted columns, env defaults).
- `sandbox_check.py`: exit-2 `--write-settings` writes deny rules only.
- `cost_by_role.py` (from the audit-docs tools) under `evals/tools/`, run
  at E on the session's transcripts.

### `skills/map-update/`

- `scripts/extract_map.py` for TypeScript/JavaScript and Python (the
  orchestrator wrote one twice now; ship it), and the rule for a language
  without one.

### New skills

- `release-engineer:repo-bootstrap`: the smallest form (§3.A.4).
- `docs-writer:readme`: §7.1, from manifest + design + slice; never
  invents a command the manifest does not have.

### Agents

- `code-reviewer/AGENT.md`: the combined-review launch described; tools
  unchanged.
- `accessibility-engineer/AGENT.md`: the smoke-run role.
- `tdd-coach/AGENT.md`: `maxTurns` tuned from the run (builders 58–139
  tool calls, D r1 fixer 230 turns: keep 120 for builders, 160 for the D
  fixer, passed on launch).

### README, PERSONAS, evals

- README "The chunk loop": the v4 round, the readiness gate, the
  Definition of Done, the budget line, the Low policy.
- PERSONAS: the Orchestrator paragraph points at v4; `release-engineer`
  gains `repo-bootstrap`; `docs-writer` gains `readme`.
- `evals/tools/orchestrator_log_check.py`: Agent launches under an open
  entry across sessions; sidecar for round counts; clean rounds without a
  split; `Policy:`/`policy —`; parentheticals; the v4 fields.
- Version 0.7.0.

## 10. Cost model, against the real run

Per-role figures are the real run's, scaled by the launch counts v4
implies. Estimates, not promises; `cost_by_role.py` on the next run is the
check.

| Role | Run 2 (v3) | v4 estimate | How |
|---|---|---|---|
| Planning | $19 | ~$30 | readiness gate fails route back once or twice; the numbers and states get written up front |
| Builders (Sonnet) | $25 | $25 | unchanged |
| Chunk reviews (Opus) | $144 (186 runs) | ~$30 | 6 chunks × (1 review + 1 smoke + 1 re-review) ≈ 18 launches at ~$1.50 |
| D reviews (Opus) | $40 | ~$12 | 6 reviewers once + 6 re-reviews on the fix diff |
| Fixers (Sonnet) | $28 | ~$14 | ≤ 2 per scope, 7 scopes |
| Consults | $16 | ~$5 | most decisions made before B; ≤ 8 by budget |
| Low filing | $24 | $0 | not filed |
| Orchestrator | $70 | ~$30 | one report per round, no scribing, no scripts, half the turns |
| **Total** | **$346** | **~$145** | |
| Wall clock | 14.5 h | ~5–6 h | 2 reviews per chunk round at 6–12 min; ≤ 2 fixes; no Low triage |

Where the quality gain is expected to come from, in order: the seam tests
(the class of bug both repos have), the readiness gate (the twenty
decisions, and the churn they caused), the Definition of Done (README,
lint, no code in strings, no WHAT-comments), one fix round (fewer
fixer-introduced regressions). None of it comes from reviewer count.

## 11. Eval cases to build

Rebuilt on `evals/fixtures/library-app/`; each is a case directory with
graders, following `evals/README.md`.

1. **Readiness gate**: a planning set whose reliability doc says "retry a
   few times" and whose screen design lacks a state the security file
   names; the orchestrator routes to `reliability-requirements` and
   `screen-design` before any builder launch, and the A line records the
   checks.
2. **Delegation file**: a consult launched with the file writes its
   document and commits; launched without one it hands back a
   recommendation and the flow asks the owner.
3. **One review per chunk**: a chunk round launches exactly one reviewer
   and one smoke agent; the report has ≤ 8 findings and no Low.
4. **One fix round**: a fix whose re-review raises one regression and one
   pre-existing Medium: the regression goes to the second fixer, the
   pre-existing is on the C line as standing, no third review.
5. **Gate scope**: a commit touching a file inside a design module but
   off the Files line passes with a deviation line; one touching another
   directory fails to the fixer.
6. **Seam test**: a chunk plan whose Done-when names no test through the
   composition root fails the plan check; a chunk whose tests all fake at
   the port gets a High from `test-quality-review`.
7. **Comments**: a GREEN step that writes `// increment the counter`
   above `counter++` is caught by the builder's own REVIEW (heavy) or by
   the chunk review (Medium); a comment citing "decision 7" is Medium.
8. **Definition of Done**: a slice with no README, a `<script>` body in a
   template literal and 12% comment density produces three named fixes
   before D's reviewers run.
9. **Budget**: a flow that reaches its hour cap ends at the chunk
   boundary with the branch intact and the report saying what is built.
10. **Delivery in the foreground**: the E line, the PR body's links and
    the sync appear in the turn that files the last issue; no Low issue
    is filed.
11. **Log format**: the checker parses a v4 entry with zero format
    errors; the fixed checker reports none of the 60 false positives on
    the run-2 log and all three real deviations.
12. **Planning**: `requirements-refinement` asks the problem doc's open
    question or lists it under Not yet confirmed; edits the Active file in
    place on a same-conversation correction; `security-requirements`
    changes only the slice's placeholder line and leaves the story
    byte-identical; `architecture-design` routes a scope consequence to
    `product-manager` before approving.

## 12. Build order

1. This document, approved item by item (§13 answered).
2. **PR 1, the loop**: orchestrator A (questions, delegation, budget,
   readiness gate), B (seam test in the plan check), C (one review + smoke,
   one round + regressions-only re-review, the gap step, gate scope), D
   (Definition of Done before the reviewers), E (foreground, Low policy);
   `tdd-implementation` and `-lite` (seam test, comments, deviations,
   report); `code-review`/`test-quality-review`/`reliability-review`
   (shared format, combined review, Medium for WHAT-comments, the seam
   check); `accessibility-review` smoke mode; `readiness_check.py`,
   `done_check.py`, `rounds_record.py`, `validation_gate.py` changes,
   `sandbox_check.py` fix; `map-update` extractor; `docs-writer:readme`;
   `release-engineer:repo-bootstrap`; README, PERSONAS; version 0.7.0.
3. **PR 2, planning**: the §9 planning-skill changes; orchestrator steps
   3–5 wording; `orchestrator_log_check.py`.
4. **PR 3, evals**: cases 1–12; `cost_by_role.py` under `evals/tools/`;
   bars recorded per the playbook.
5. **Run slice 2 on 0.8.1 with the budget line** (the version that
   carries all of v4: PR 1 to PR 3, the launcher and the no-screen slice
   rule that landed with them; 0.7.0 was PR 1 alone), in a fresh repository for a one-to-one
   comparison, audit it the same way, and decide D9's phase 2 (the
   chunk-runner agent) on the orchestrator's measured context.

## 13. Questions for the owner, with the default this design assumes

| Question | Default assumed here |
|---|---|
| Lows: file every open Low, file only standing Mediums, or list Lows in the PR body and file nothing? | List in the PR body under "Known Lows", file nothing; file standing Mediums. |
| One question per `AskUserQuestion`, everywhere (run 1's preference)? | Yes, in every asking skill. |
| Outcome bullets appended to a log entry after its step runs: forbid (the rule) or allow indented bullets (the practice)? | Allow indented plain bullets under any entry; headings and the Routed to / Artifact lines are never edited; never a second bold step line. |
| Report after every planning step, or chain and report at the end (run 2's direction, in memory)? | Report as visible text after every step; ask whether to continue only when the next row needs an owner decision to start. |
| Review records under `planning/implementation/` (gate allows the directory, a records commit per chunk) or outside the protected tree? | Keep under `planning/implementation/`, named in the skill, one `Records:` commit per chunk. |
| Budget defaults: 5 h, 2 reviews per chunk, 1 fix per scope (+1 for regressions), 8 consults? | As stated. |
| Comment-density threshold 5%? | 5%, report-only in the gate, acted on at D. |
| Should the smoke agent also run the README's "clone to running" on a clean clone at D (slower, catches the setup gap both repos had)? | Yes, once, in D's last round. |
