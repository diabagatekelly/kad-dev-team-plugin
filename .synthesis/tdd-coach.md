# Synthesis: tdd-coach

Internal only — never referenced from `agents/tdd-coach/AGENT.md` or its
backing skills. Delete once the full roster is built.

Roster row 5, first of the two originally-planned "core strength" personas
(the other being `code-reviewer`). Two skills already decided in the
planning session that preceded this synthesis (see PERSONAS.md "Next to
build" → `Next: tdd-coach`): `tdd-implementation` (write a designed slice
via genuine Red-Green-Refactor; also applies specifically-named fixes
handed back from any reviewer, through the same loop) and
`test-quality-review` (critique existing tests — over-mocking, false
positives, coverage-as-theater — standalone-capable and reused unmodified
as one of several parallel graders in the restored quarantine/grade/combine
flow, see PERSONAS.md "Deferred / phase-2 ideas" → Orchestrator v2).
`tdd-implementation` follows Clean Architecture/OeA principles as a writing
constraint, informed by `architecture-design`'s already-decided boundaries
for the slice — it does not decide or verify architecture itself.

This is also the first persona in the roster whose sources hand it
genuinely new tooling implications: every source's RED/GREEN/REFACTOR step
assumes real test execution, not narration. `tdd-implementation` needs
`Bash` (to actually run the test suite) alongside `Read`/`Write`/`Edit` —
the roster's other personas so far are all `Read`/`Grep`/`Glob`-plus-
artifact-writing. `test-quality-review` stays `Read`/`Grep`/`Glob`-only,
report-and-recommend, same as every other reviewer this roster has built
(`accessibility-review`, `architecture-review`) — reviewing static test
content doesn't require executing anything, and it never edits someone
else's test file directly.

## Sources consulted

1. **CAMS** —
   - `skills/cams-development-workflow/SKILL.md` in full: the 6-step
     vertical-slice workflow, specifically Step 5's
     RED-GREEN-REFACTOR-**REVIEW**-REPEAT cycle (a fourth named step this
     source adds beyond the textbook three).
   - `skills/cams-refactoring/SKILL.md`, Procedures 1–5 in full (identify
     smells, decide whether to refactor, refactor safely, Boy Scout Rule,
     refactor inside the TDD cycle). Procedures 6–15 (the smell-specific
     pattern catalog — long function, duplication, long parameter list,
     large class, primitive obsession, feature envy, data clumps, switch
     statements, dead code) read for structure only, not quoted — this is
     TypeScript-flavored procedure duplicating the Fowler/Beck canon that
     Flexion's `oea-refactorings` already states in fully portable terms
     (see Scope decisions).
   - `skills/cams-testing-unit/SKILL.md`: Testing Philosophy, the Critical
     Mocking Strategy section, and PROCEDURE 6 (TDD cycle) read in full.
     The five per-layer test-writing procedures (use case/repository/
     controller/UI component/utility) skipped — CAMS-specific procedure,
     not a portable principle, per this plugin's own read-past-the-
     procedure rule.
   - `agents/cams-unit-test-reviewer/AGENT.md` in full — the direct
     precedent for `test-quality-review`: seven issue categories, a
     severity taxonomy, and an acceptable-patterns exception list.
   - `agents/pragmatic-reviewer/AGENT.md` in full — YAGNI enforcement, the
     "second use case" test, "weighted highest in conflicts."
2. **Flexion plugin** —
   - `flexion-engineer-base/skills/tdd-workflow/SKILL.md` in full — Kent
     Beck's Test List workflow (absent from every other source), the core
     RGR cycle, and "Code Review Checkpoints."
   - `flexion-engineer-base/skills/tdd-workflow/references/tdd-multiagent.md`
     and `references/tdd-reference.md` in full — multi-agent TDD
     (per-agent responsibilities, progress-reporting format, convergence
     signals), test organization (unit vs. integration, AAA, naming),
     common pitfalls, and an explicit "when to deviate from TDD" list.
   - `flexion-ai-tdd-typescript-jest/skills/tdd-typescript-jest/SKILL.md`
     in full — a framework-specific (Jest/Vitest/Playwright) illustration
     of the same three-phase discipline, read for the principles under the
     framework wrapping, same portability rule as every prior synthesis.
   - `flexion-oea-coder/skills/oea-refactorings/SKILL.md` in full — a
     fully language-agnostic Fowler/Beck pattern catalog. Surfaced a real
     scope boundary rather than pure reusable content (see Scope
     decisions).
3. **Personal skills** — `~/.claude/skills/tests-audit/SKILL.md` and
   `~/.claude/skills/code-review/SKILL.md` in full. Searched every
   project-level `.claude/skills` under `~/Documents/*`
   (`feature-gap-analyzer`, `clean-docs` — neither TDD-related). **This is
   the first synthesis in this roster where personal skills contribute
   real, load-bearing content rather than the "nothing found" silence
   every prior synthesis (`ux-designer`, `accessibility-engineer`,
   `software-architect`) reported for its own topic.** `tests-audit`
   supplies mutation testing / false-positive detection and a
   TDD-adherence-via-git-log method, neither present in CAMS or Flexion.
   `code-review`'s DRY/architecture/security categories already belong to
   personas this roster owns elsewhere (a future `code-reviewer`,
   `architecture-review`, `devsecops-engineer`) — noted, not imported.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Before Red/Green/Refactor starts, write a **Test List** — every scenario the current goal needs, as analysis not implementation — then work it one test at a time, marking each off before picking the next. The named failure mode: converting the whole list into concrete tests up front, then making them pass one at a time, defeats the incremental-design purpose of TDD | tdd-workflow ("CRITICAL MISTAKE TO AVOID") | gap → added — absent from CAMS and personal sources; this is the organizing structure `tdd-implementation`'s Red step runs inside |
| YAGNI applies to the Test List itself, not just the code: only list scenarios the current goal actually needs, not "nice to have," not speculative edge cases, not future requirements | tdd-workflow | gap → added, reinforces baseline below |
| RED: write one concrete, failing test for one behavior; verify it fails, and fails for the right reason (not a syntax error or missing dependency) — don't assume | cams-development-workflow, cams-testing-unit PROCEDURE 6, tdd-workflow, tdd-typescript-jest | baseline, four-way convergence |
| GREEN: minimum code to pass the one active test — hardcoding is acceptable, ignore untested future cases, stop the instant it's green | cams-development-workflow, cams-testing-unit, tdd-workflow, tdd-typescript-jest | baseline, four-way convergence |
| REFACTOR: improve structure only, in small steps, running tests after every step; revert immediately on red and retry smaller; never mix a behavior change into a refactoring step (CAMS's own worked example: a validation extraction commit must not also add a new "attorney workload" business rule) | cams-refactoring Procedures 3 & 5, cams-testing-unit, tdd-workflow, tdd-typescript-jest | baseline, four-way convergence |
| Refactoring means *simplifying* — extracting duplication, clarifying names — never adding an interface "for flexibility," defensive code, or anything not required by a passing test | tdd-workflow, tdd-typescript-jest ("What NOT to Refactor") | baseline, reinforced by pragmatic-reviewer's YAGNI stance generally |
| A fourth, named step — **REVIEW** — sits inside the cycle, not after it: trigger the test-quality reviewer, address CRITICAL/HIGH findings, only then repeat | cams-development-workflow Step 5 | gap → added, and the direct structural justification for this persona's own impl/review two-skill split (see Contradiction 1 for cadence) |
| A fix handed back from review re-enters the same test-then-code discipline — re-run tests, proceed only after a clean re-review — not a free-form patch exempted from the loop | cams-development-workflow ("Address any CRITICAL or HIGH... before proceeding"), tdd-workflow ("Outcome of Review") | baseline, two-way convergence — direct support for `tdd-implementation`'s already-decided "applies named fixes through the same loop" behavior |
| Touching existing, messy code as part of a task: apply the Boy Scout Rule — a small, bounded cleanup (rename, extract one constant, fix one duplication) if not blocking; a larger refactor-first-then-feature if the mess actually blocks the feature; never refactor code you're not touching, never spend hours perfecting it | cams-refactoring Procedure 4 | gap → added |
| A design gap discovered mid-implementation gets a concrete, bounded escalation rule instead of either silently guessing or always stopping to ask: if the fix is small and doesn't change the design's shape, make it and note it; if it would mean rethinking architecture or scope, stop and return to whichever persona owns that decision | cams-development-workflow Step 3 ("If the fix takes <15 minutes, update directly. If it requires rethinking architecture, return to `/cams-slice-design`.") | gap → added — see Scope decisions for why this replaces both silent guessing and a live `AskUserQuestion` |
| Test-quality review's seven issue categories: mocking the code under test (CRITICAL — the test is invalid); excessive mocking; useless tests *and* missing coverage (an exported function/branch with zero tests is a gap, not just noise to trim); tests asserting on implementation details instead of behavior; defensive-coding patterns the tests reveal as untested/unneeded; incomplete edge-case coverage on guard/validation functions; testing through the wrong component boundary (asserting on a dependency's internals instead of the unit's own contract) | cams-unit-test-reviewer | baseline — this is `test-quality-review`'s core checklist, near-verbatim source precedent |
| Severity scale for test-quality findings: Critical (mocking the code under test) / High (excessive mocking, implementation-detail tests, wrong-boundary tests) / Medium (useless tests, revealed defensive coding, incomplete edge cases) / Low (style) | cams-unit-test-reviewer | baseline — already matches this roster's own adopted Critical/High/Medium/Low scale (`accessibility-review`, `devsecops-engineer`); first source whose native severity vocabulary needed no remapping at all |
| Spying on a test stub/fake/mock class that stands in for an external dependency is not a mocking violation — only flag stub usage when the stub itself is complex enough to need its own tests, or a test asserts on the stub's internals instead of outcomes | cams-unit-test-reviewer ("Acceptable Patterns") | baseline |
| The mocking *mechanism* has to match how the code under test actually obtains its dependency — constructor/parameter-injected dependencies substitute cleanly; a dependency reached via a tightly-coupled import needs a mechanism that actually intercepts that reference. Using the wrong one produces a test that silently exercises the real dependency while believing it's mocked | cams-testing-unit ("Critical: Mocking Strategy") | gap → added, generalized past its `vi.spyOn()`-specific framing — neither Flexion TDD source goes past "mock external dependencies" |
| A guard/validation function's tests must cover every input *shape* that can actually reach it (including null/undefined/wrong-type), not just a valid instance and an empty object — the common gap is a test suite that never proves the guard survives the one input shape most likely to crash it | cams-unit-test-reviewer | gap → added, generalized past its TypeScript-specific `typeof null === 'object'` example to "test every reachable input shape, not just the happy path plus one empty case" |
| Tests written only to inflate a coverage number, rather than to specify a real behavior, are a defect in the test suite, not a benign padding | tdd-workflow ("Useless/Unneeded Tests"), cams-unit-test-reviewer, tests-audit ("False Positive Detection") | baseline, three-way convergence |
| Coverage completeness is verified by mutation testing (or, absent a tool, manual red/green: mutate the source, confirm the test now fails, restore) — a test suite can show 100% line coverage while still never actually detecting a broken implementation, and that gap is only caught by trying to break the code on purpose | tests-audit | gap → added — none of the CAMS or Flexion TDD sources describe this; the single most load-bearing thing personal skills contributed to this synthesis |
| Target: 100% line and branch coverage, arrived at as the natural result of testing every real behavior on the Test List — not a number pursued by writing low-value tests after the fact | cams-unit-test-reviewer ("100% branch and line coverage"), tests-audit ("100% for New Code") | resolved toward the majority position — see Contradiction 2 |
| TDD-adherence is independently verifiable after the fact from git history, *if* the test and its implementation were committed as separate, ordered commits (test commit, then implementation commit, then any refactor commit) | cams-testing-unit PROCEDURE 6 (commit discipline), tests-audit ("TDD Adherence" — checks exactly this via `git log --follow`) | gap → added, two-way convergence — CAMS supplies the discipline, personal skills supply the reason it's worth keeping: it's the only source of retrospective auditability this synthesis found |
| Report progress in a fixed, legible shape at each stage: baseline (tests/coverage before starting), the Test List as created, status after each completed cycle, and a final convergence report (Test List complete, review passed, coverage maintained or improved, YAGNI-compliant) before signaling done | tdd-multiagent.md | gap → added — this is the vocabulary `tdd-implementation` reports completion in, and (via PERSONAS.md's already-decided Orchestrator v2 quarantine flow) what each of the two blind candidate instances hands back for grading |
| TDD is the default, not an unconditional rule — skip it for exploratory spikes and throwaway prototyping, pure configuration with no logic, or an explicit user request to proceed without it; resume it the moment spike code is kept or a prototype becomes real | tdd-reference ("When to Deviate from TDD") | gap → added — without this, `tdd-implementation` would over-apply strict TDD to work no source actually asks it to |

## Contradictions — flagged and resolved

**1. How often does the review step fire?** `cams-development-workflow`
Step 5 names REVIEW as the fourth stage *inside* the per-test
RED-GREEN-REFACTOR loop — "For EACH Task: RED-GREEN-REFACTOR-**REVIEW**,"
run again before advancing to the next test. `tdd-workflow`'s "Code Review
Checkpoints" section triggers review once the *whole Test List* is
passing — once per goal, not once per test — explicitly listing "all
tests on your Test List are passing" as the trigger condition.

**Resolved toward CAMS's tighter, per-cycle cadence.** `test-quality-review`
is a read-only static check with no side effects — running it after every
cycle costs little, and the point of catching a bad mocking pattern or an
implementation-detail assertion is that it's cheap to fix when it's the
newest thing on the stack and expensive once several more cycles have been
built on the same bad pattern. This is the same "catch it as close to the
introduction point as possible" reasoning already implicit in the
Boy-Scout-Rule and immediate-revert-on-red principles every source shares.
Flexion's looser per-goal cadence is the position not adopted — it reads
as an efficiency trade-off for a cheap check that doesn't need to be made
here. This also settles the cadence question PERSONAS.md's Orchestrator
v2 note left open at the *candidate* level (one review pass per finished
implementation, run by the orchestrator's grading step) — that grading
pass is a separate, coarser-grained review of a finished candidate, not a
substitute for `tdd-implementation`'s own per-cycle self-check while
writing.

**2. Coverage target: 95%/90% vs. 100%/100%.** `tdd-multiagent.md` names
"95%+ line, 90%+ branch" as the target. `cams-unit-test-reviewer` and
`tests-audit` both independently land on 100% for new code.

**Resolved toward 100%**, the position two of three sources hold
independently, with `cams-unit-test-reviewer`'s framing kept alongside it
deliberately: 100% is described there as a natural *result* of writing a
test for every behavior a Test List actually names, not a separate number
to chase by padding tests after the fact — the same "coverage-as-theater"
failure mode named directly above as a three-way convergence. Flexion's
95/90 is the position not adopted, on the reasoning that a target with
built-in slack invites exactly the "good enough, stop here" instinct the
100%-and-mutation-tested combination above is designed to close off.

## Scope decisions, not sourced from a contradiction

**Whole-module refactoring patterns are out of scope for `tdd-implementation`'s
Refactor step — a real boundary this synthesis found, not a contradiction
to adjudicate.** `oea-refactorings` catalogs Extract Module, Move
Function/Field-across-modules, and Extract Interface (dependency
inversion) — and states explicitly that these patterns run **no tests**:
"a split or merge logs its `refactoring` entry... and moves on... the next
scheduled green catches a botched reshape." That reads as directly opposed
to every TDD-specific source's insistence on running tests after every
refactoring step. It isn't actually opposed — it's a different activity,
governed by a different process's own condition-checker and scheduled-green
cadence, not something `tdd-coach` owns or invokes. `tdd-implementation`'s
Refactor step operates at Fowler's *small*-refactoring grain, entirely
inside a module already in front of it — extract, inline, rename, move a
few lines — and for that grain every TDD source agrees: tests run after
every change, revert immediately on red. A refactor that would cross a
module boundary or invert a dependency direction is exactly the
architectural territory this persona already doesn't own, per its own
already-decided line in PERSONAS.md ("doesn't decide or verify
architecture itself — `architecture-design`/`architecture-review` still
own that"). A mid-cycle discovery that the real fix needs a module
boundary redrawn escalates via the CAMS Step-3 threshold above rather than
being redrawn unilaterally. `oea-refactorings`' catalog was still useful
for confirming that Fowler/Beck's vocabulary (extract/inline/move/rename)
generalizes cleanly past CAMS's TypeScript-flavored version of the same
patterns — but this synthesis doesn't reproduce a pattern catalog in
`tdd-implementation`'s own text; the skill names the discipline
(small step, tests green after each, never mixed with a behavior change)
and trusts standard refactoring vocabulary, the same principle-over-
catalog choice this roster has made everywhere else.

**No live `AskUserQuestion` for implementation-time ambiguity — this
persona resolves gaps through escalation to whichever upstream persona
already owns the decision, not through a mid-task question.**
`tdd-coach` isn't one of the roster's enumerated must-ask planning
personas (`product-manager`, `product-slicer`, `software-architect`,
`devsecops-engineer`) — it turns an already-designed slice into code, the
same "verifies/executes, doesn't decide" position `accessibility-engineer`
already holds relative to `ux-designer`. But unlike a pure reviewer,
silently downgrading every gap to a logged Low-severity note (accessibility-
engineer's own resolution) doesn't fit a persona that's actively writing
code against an ambiguous instruction. The CAMS Step-3 threshold supplies
the actual rule instead: a small, non-architectural gap gets filled and
named in the work itself (visible in a Test List entry or a commit
message, not silently assumed); a genuinely load-bearing gap escalates
back to the design-owning persona (`architecture-design` for a boundary
question, this roster's `acceptance-criteria` for a behavior question)
rather than being decided unilaterally mid-implementation or bounced to a
live question this persona has no standing to ask.

**`test-quality-review` never edits a test file directly — report and
recommend only**, the same non-negotiable this roster already holds for
every other reviewer (`accessibility-review`, `architecture-review`).
Directly confirmed by `cams-unit-test-reviewer`'s own tool list
(`Read`/`Grep`/`Glob` only, no `Edit`) — no contradiction to resolve, a
clean baseline match.
