> **STALE — do not cite this score.** This case now has 5 graders; the run below covered 4 (the cross-cutting-constraint grader was added afterward). The result below predates that change and is kept only as history. Re-run required.

# docs-writer:scope-map — 4/4 PASS

Overall: **PASS**

| Grader | Type | Result |
|---|---|---|
| has-required-sections | regex | PASS |
| skill-invoked | tool_used | PASS |
| no-slicing-or-design | llm | PASS |
| steps-cover-full-problem | llm | PASS |

Re-run after this session added the cross-cutting-constraint rule to
`skills/scope-map/SKILL.md` (a constraint that applies to every step is not
a step, and routes to each step's `requirements-refinement` pass rather than
to "made concrete per slice as each is designed"). No regression: the new
material lands in the Out of scope section and did not leak into any step
line, which is what `no-slicing-or-design` guards.

Previous result was also 4/4 against the pre-change skill.
