---
type: llm
criteria: |
  PASS only if each GREEN-phase implementation shown is the minimum that
  satisfies the one active test — no validation, error handling, logging,
  configuration, or extra `AssignmentResult` fields beyond what the design
  doc and the current test actually require. In particular: no code
  handling the "already assigned to someone else" scenario should appear
  anywhere in the implementation, since that behavior was never decided
  (it should show up only as an escalated open question, graded
  separately) — its presence in the implementation is itself a FAIL, not
  just a stray extra. FAIL also if any implementation step adds something
  no current test exercises "for later" or "to be safe."
focus: last_message
---

Checks minimum-implementation discipline, including the specific trap of
quietly implementing the undecided reassignment behavior instead of
escalating it.
