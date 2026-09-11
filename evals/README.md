# Evals

Hand-authored against `claude plugin eval`'s documented format (`prompt.md`
+ `graders/*.md` per case, confirmed via `claude plugin eval --help`) — the
CLI itself is early-access-gated in this environment (`init` fails with
"currently in early access"). None of these have run against the real CLI;
some have been run via the homegrown `.claude/skills/agent-eval` stand-in
(see each case's `eval-score/summary.md` if present). Treat the format as
best-effort until real access lands; re-check each case against
`claude plugin eval init --bare <name>`'s real output once it does.

Each case tests one skill trigger: does the right skill get invoked
(`tool_used` grader), and is the output actually correct (`llm` grader).

**Two-phase cases.** If a persona's correct behavior is to ask a clarifying
question, `agent-eval` runs a second phase: it supplies a scripted answer
(from the case's `## Scripted answers` section) and re-invokes the persona
to get the actual finished artifact — a real invocation would ask via
`AskUserQuestion` and keep going in the same turn; a single-phase run can't
model that; grading only the question would validate "did it ask" and never
"did it finish the job." `eval-result/phase1-question.md` holds the
question, `eval-result/output.md` holds the final artifact. Graders default
to grading the final artifact; a grader with `target: phase1` in its
frontmatter grades the question instead (used for the "did it ask" checks).

## Coverage

Case names follow `agent:skill` for persona-backed triggers, or just
`skill` for a skill with no owning persona (e.g. `orchestrator`).

**Last result** is the most recent score. **Current** says whether that score
still describes the code: a case goes stale the moment its `AGENT.md` or
`SKILL.md` changes, or its own fixtures/graders are edited. A stale case's
score is history, not a claim about today.

| Case | Last result | Current? |
|---|---|---|
| `docs-writer:problem-framing-doc` | 3/3 PASS | yes |
| `docs-writer:scope-map` | 5/5 PASS, inline | yes |
| `docs-writer:adr` | — | not written |
| `docs-writer:why-comments` | — | not written |
| `docs-writer:user-story-writeup` | 3/3 PASS, two-phase | yes |
| `docs-writer:pr-writeup` | — | not written |
| `docs-writer:user-facing-docs` | — | not written |
| `docs-writer:staleness-audit` | — | not written |
| `product-manager:requirements-refinement` | 6/6 PASS, two-phase | yes |
| `product-slicer:vertical-slicing` | 6/6 PASS, two-phase | yes |
| `product-slicer:acceptance-criteria` | 2/2 PASS, inline | yes |
| `orchestrator` | 15/15 PASS, skill-only | yes |
| `software-architect:architecture-design` | 8/8 PASS, three-phase — extends the documented format, see the case's own `prompt.md` | yes |
| `software-architect:architecture-review` | 4/4 PASS, inline | yes |
| `software-architect:technology-bootstrap` | 6/6 PASS, inline | yes |
| `devsecops-engineer:security-requirements` | 7/7 PASS, inline | yes |
| `devsecops-engineer:security-review` | 7/7 PASS, inline | yes |
| `devsecops-engineer:supply-chain-review` | — | not written |
| `devsecops-engineer:reliability-requirements` | 5/5 PASS, inline | yes |
| `devsecops-engineer:reliability-review` | 6/6 PASS, inline | yes |
| `devsecops-engineer:operational-readiness` | — | not written |

### The `example/` directory

`example/` is not a case and has no graders of its own. It's the dogfooding
record: one real problem worked end to end by the actual personas, which is
where most of this plugin's rules came from — usually by watching the run
break.

It gets graded by borrowing the graders from each artifact's owning case.
Two limits on that, both recorded in its `summary.md`: `skill-invoked` and
phase-1 graders don't apply (these are finished documents, not captured
harness output), and some graders are bound to their fixture's specifics and
have to be adapted or skipped. **Passing there is not the same as the case
passing** — it's real artifacts against adapted criteria.

### Run backlog

Eight cases currently need a run. Nothing here is green — every score in
the table above either predates a change to the code it covers, or predates
an edit to the case itself. Ordered by what's worth doing first, not by
what's cheapest.

| # | Case | Why it's first |
|---|---|---|
| 1 | ~~`orchestrator`~~ | **Run, fixed, re-run: 15/15 PASS.** First pass was 14/15 — `single-step-not-chained` caught backward routes L and M narrating the post-resolution forward resumption. Fixed in `skills/orchestrator/SKILL.md`'s backward-routing section and confirmed clean on re-run. Details in `orchestrator/eval-score/summary.md`. |
| 2 | ~~`software-architect:technology-bootstrap`~~ | **Run: 6/6 PASS.** The negative grader (never solicit CI/CD, hosting, a database, observability, or auth) passed clean against its own fixture for the first time. One interpretive call worth watching in future runs: UI framework was judged not-forced by the first test — defensible, but not mechanical. Details in `software-architect:technology-bootstrap/eval-score/summary.md`. |
| 3 | ~~`docs-writer:scope-map`~~ | **Run, fixed, re-run: 5/5 PASS.** First pass was 4/5 — the "AI categorization must be free" constraint got absorbed into its step's one-liner instead of being flagged cross-cutting like security. Fixed in `skills/scope-map/SKILL.md`: identify a cross-cutting constraint by its underlying concern, not by which step's sentence names it. Confirmed clean on re-run. Details in `docs-writer:scope-map/eval-score/summary.md`. |
| 4 | ~~`product-manager:requirements-refinement`~~ | **Run: 6/6 PASS.** The constraints-in-force grader — added after a real run dropped the hosting and single-user constraints for a step that didn't look like it owned them — passed clean: both non-obvious consequences (network access-control gate, present-tense single-user modeling) were drawn correctly. |
| 5 | ~~`product-slicer:vertical-slicing`~~ | **Run: 6/6 PASS.** Scenario C's grader — encoding the real failure where a menu of options got handed to the user, who picked "grow the slice" — passed clean: ranked order worked through explicitly, narrowing rejected with a concrete reason, new slice ahead chosen, both invalidations named. |
| 6 | ~~`product-slicer:acceptance-criteria`~~ | **Run: 2/2 PASS.** Regression confirmation, no news, as expected. |
| 7 | ~~`software-architect:architecture-review`~~ | **Run: 4/4 PASS.** Regression confirmation, no news, as expected. |
| 8 | ~~`software-architect:architecture-design`~~ | **Reworked, then run: 8/8 PASS.** Graders split into four `portable-*` (hold for any design doc) and three `fixture-*` (this case's own sync/async and premature-abstraction content) per `NOTES.md`'s plan. First-ever gradable result for this case, and the first real test of the "Technology at a boundary" section added since it was last run. |

All eight cases in this backlog have now been run at least once.

Run with the `agent-eval` skill, one case per invocation.

### Known coverage gaps

- **`devsecops-engineer` has four cases out of six skills.**
  `security-requirements` (7/7), `reliability-requirements` (5/5),
  `security-review` (7/7), and `reliability-review` (6/6) are now covered;
  `supply-chain-review` and `operational-readiness` still have none.
  `operational-readiness` was written from a gap rather than synthesized
  from sources, so running it is the only way it can be checked.
- ~~**The hand-back rule is tested from one side only.**~~ **Closed.**
  `devsecops-engineer:security-requirements` now tests the producing side —
  reports a login gap forced by the slice being hosted-and-reachable, names
  `product-slicer` by name, and doesn't enumerate a resolution menu — all
  passed clean. Independently auditing `evals/example/security-requirements-001.md`
  against `SKILL.md` directly (not assuming it was correct) also surfaced a
  real, narrower gap: it never addresses monitoring/telemetry/analytics as
  an exit for its sensitive data, though four of the five named exits are
  covered. A new `addresses-all-five-exits` grader now checks this, and it
  caught the same gap in this case's own first draft too (missing
  exception/stack-trace, distinct from error-response) — fixed and
  re-verified. Details in `devsecops-engineer:security-requirements/eval-score/summary.md`.
- **`technology-bootstrap`'s advisor-consult path is only softly graded.**
  Consulting `devsecops-engineer` inline is treated as expected-but-not-
  required, because the emulation harness can't distinguish an inline
  consult from a spawn — the distinction the rule actually exists to
  enforce.

Root-cause notes for any bug a case caught live in that case's own
`eval-score/summary.md`, not here — check there before touching a skill,
grader, or the `agent-eval` harness that a case already covers.
