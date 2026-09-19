---
type: llm
criteria: |
  PASS only if the implementation matches the design doc's already-approved
  structure exactly: `AttorneyDirectory` is defined on the strategic side
  (owned by/alongside `AssignCase`, not inside a gateway/infrastructure
  file), `AssignCase` depends only on the `AttorneyDirectory` interface
  and never imports `AttorneyDirectoryGateway` or the staffing SDK
  directly, and `AssignmentResult` stays plain data. The response should
  not introduce a new boundary, a new interface, or a different structure
  than what the design doc named — if it hits something that would
  require doing that, it should say so and treat it as a question for
  whoever owns the design, not decide it itself. FAIL if any of the
  above boundaries are violated or silently redrawn.
focus: last_message
---

Checks the implementation stays inside the boundaries `architecture-design`
already decided rather than redrawing them — the "writing constraint, not
a verifying/deciding role" line this persona holds relative to
`architecture-design`/`architecture-review`.
