---
type: llm
criteria: |
  PASS only if every test written for `AssignCase` asserts on
  `execute()`'s return value (the `AssignmentResult` shape) or an
  observable call to one of its injected collaborators (`AttorneyDirectory`,
  or a repository-style dependency `AssignCase` uses to persist the
  assignment, since "assigns" is itself part of what the design says
  `execute()` does) — not on a private method, private internal state, or
  call order between two of `AssignCase`'s own internal steps that isn't
  part of its described public contract. Asserting that an injected
  collaborator's method was called with the right arguments is a
  legitimate boundary check, not an implementation-detail violation — the
  collaborator is a designated stub standing in for a real dependency, the
  same acceptable pattern this roster's `test-quality-review` skill names
  for spying on test doubles. Each test should also be traceably about one
  scenario (open+available, not-open, attorney-not-available, etc.), not
  several behaviors asserted in one test. FAIL if any test reaches into
  genuine implementation detail not implied by the design doc's
  boundary (e.g. asserting on a private helper method, or on call order
  between two steps with no observable difference in outcome), or bundles
  multiple behaviors into a single test with multiple unrelated
  assertions.
focus: last_message
---

Checks tests are written at the clean boundary the design doc actually
describes, not against implementation detail — while correctly treating an
assertion on an injected collaborator's contract as legitimate, not a
violation.
