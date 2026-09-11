# docs-writer:scope-map — eval summary

**Result: PASS — 5/5 graders passed**

| Grader | Result |
|---|---|
| skill-invoked | PASS |
| has-required-sections | PASS |
| steps-cover-full-problem | PASS |
| no-slicing-or-design | PASS |
| cross-cutting-constraints-routed-not-deferred | PASS |

## History

First run scored 4/5. The security constraint (real account/money data
spans every step) was correctly flagged as cross-cutting and routed to each
step's own requirements-refinement pass. The other constraint the grader
checks — "AI-assisted categorization must run at no ongoing cost" — was
instead absorbed into Step 2's one-liner, which is a defensible literal
reading (the problem doc's sentence names categorization specifically, and
no other step does anything AI-assisted) but conflicts with the skill's own
"staying free" example, listed alongside "protecting sensitive data" as a
canonical cross-cutting constraint.

**Fix applied** to `skills/scope-map/SKILL.md`: added guidance to identify a
cross-cutting constraint by its underlying concern rather than by which
step's sentence happens to name it — a constraint can read as though it
only touches the step where it first bites (categorization, in this case)
without the concern underneath it (no recurring bill for the project) being
specific to that step.

**Re-run after the fix**: only the affected grader was re-run — the fixed
output moved the cost constraint into the same cross-cutting callout as
security and dropped it from Step 2's line, leaving the other three steps
and the other three graders' targets unchanged in substance from the first
run, so those verdicts were kept rather than re-spawning redundant judges.
