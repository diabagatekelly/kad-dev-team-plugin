FAIL — stale in one element only, same root cause as directory-f

Judge agent: directories A–E, G and H all correctly name a single routed
action or a single question. The sole failing element is Directory F, whose
stated next action is `devsecops-engineer:security-requirements` rather than
"stop," plus the cross-cutting note "None of the eight is at that terminal
row: F is two rows away."

That is the same superseded-terminal-row assumption as
`directory-f-terminal-stop-no-cascade`, not an independent defect. **The
no-chaining property this grader exists to test held everywhere**, including
in F, which named exactly one next step rather than a multi-stage plan.

Fixing Directory F's fixture (see the directory-f score) clears this grader
too. The clause "and Directory F's next action must be 'stop'" should move to
whichever directory ends up carrying terminal coverage.
