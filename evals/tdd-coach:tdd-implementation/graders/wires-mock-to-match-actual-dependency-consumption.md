---
type: llm
criteria: |
  PASS only if the test double for `AttorneyDirectory` is wired as an
  injected fake/stub matching how the design says `AssignCase` obtains it
  (a constructor or parameter-passed dependency implementing the
  `AttorneyDirectory` interface) — not a mock that patches a global/module
  reference the code doesn't actually consume that way, and not a mock
  targeting `AttorneyDirectoryGateway` or the staffing SDK directly (which
  `AssignCase` never touches per the design). FAIL if the test double
  can't actually be reached by the code under test as wired, or if it
  targets the wrong layer (the gateway/SDK instead of the interface
  `AssignCase` depends on).
focus: last_message
---

Checks the mocking-mechanism-matches-actual-wiring principle: a test
double only proves anything if it actually intercepts how the dependency
is really obtained.
