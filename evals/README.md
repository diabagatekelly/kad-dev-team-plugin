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

| Case | Status |
|---|---|
| `docs-writer:problem-framing-doc` | Run via agent-eval (3/3 PASS) |
| `docs-writer:scope-map` | Run via agent-eval (4/4 PASS) |
| `docs-writer:adr` | Not written |
| `docs-writer:why-comments` | Not written |
| `docs-writer:user-story-writeup` | Run via agent-eval, two-phase (3/3 PASS) |
| `docs-writer:pr-writeup` | Not written |
| `docs-writer:user-facing-docs` | Not written |
| `docs-writer:staleness-audit` | Not written |
| `product-manager:requirements-refinement` | Run via agent-eval, two-phase (5/5 PASS) |
| `product-slicer:vertical-slicing` | Run via agent-eval, two-phase (4/4 PASS) |
| `product-slicer:acceptance-criteria` | Run via agent-eval (2/2 PASS) |
| `orchestrator` | Run via agent-eval, skill-only case (9/9 PASS) |

Root-cause notes for any bug a case caught live in that case's own
`eval-score/summary.md`, not here — check there before touching a skill,
grader, or the `agent-eval` harness that a case already covers.
