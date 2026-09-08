> **STALE — do not cite this score.** This case now has 13 fixtures and 15 graders; the run below covered 8 fixtures and 10 graders, 2 of which have since been retargeted. The result below predates that change and is kept only as history. Re-run required.

# orchestrator — 8/10 PASS

Overall: **FAIL** (every grader must pass)

| Grader | Type | Result |
|---|---|---|
| skill-invoked | tool_used | PASS |
| directory-a-no-problem-doc | llm | PASS |
| directory-b-scope-map-decided-not-asked | llm | PASS |
| directory-c-routes-to-requirements-refinement | llm | PASS |
| directory-d-routes-to-product-slicer | llm | PASS |
| directory-e-routes-to-user-story-writeup | llm | PASS |
| directory-f-terminal-stop-no-cascade | llm | **FAIL** |
| directory-g-asks-where-to-save | llm | PASS |
| directory-h-routes-to-architecture-design | llm | PASS |
| single-step-not-chained | llm | **FAIL** |
| **Total** | | **8/10** |

## Root cause: one stale fixture, two failing graders

Both failures trace to Directory F's fixture, not to the skill. Its state —
user story filed, design doc exists, nothing else — was the terminal row when
this case was written. The terminal row has since moved twice, and F now
correctly matches the `security-requirements` row. `single-step-not-chained`
fails only because of its "Directory F's next action must be 'stop'" clause;
the no-chaining property itself held in all eight directories.

Read the two FAIL scores together — they are one problem reported twice.

## What this run *did* verify

The three rows added since the last passing run are exercised only
indirectly. Directory F's output declines `technology-bootstrap` despite the
empty repo (correct — that row sits below the runtime-safety rows) and
declines the four event-triggered review skills (correct — no code exists).
That reasoning is right, but no grader asserts it.

**Backward routing is completely untested.** The output notes it checked all
eight directories for hand-back signals and found none, which is correct for
these fixtures — but no fixture contains one. Given that backward routing was
added specifically because a real dogfooding run exposed a scope change being
resolved by the wrong persona, a fixture carrying a "handed back" section
(and expecting a route to the artifact's *owner*, not its finder) is the
highest-value addition to this case.

## Coverage gaps to close, in priority order

1. A fixture with a backward-routing signal.
2. A fixture at the current terminal row (design + runtime-safety criteria +
   stack), restoring what F used to cover.
3. Fixtures for the `reliability-requirements` and `technology-bootstrap`
   rows.
4. Retarget or rewrite Directory F for the security-requirements row.
