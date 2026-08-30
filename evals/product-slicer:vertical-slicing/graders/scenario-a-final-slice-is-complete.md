---
type: llm
criteria: |
  Grading Scenario A's final slice, after the scripted answer (let the
  user pick which of their two checking accounts). It must be a genuinely
  finished slice write-up: thin path, Given/When/Then acceptance criteria,
  Explicitly deferred, and Still open — all present and substantive. It
  must correctly reflect what the requirements doc already confirmed
  (single-user, live bank connection, one account connected at a time) —
  not silently expand into multi-account or reopen the mechanism choice.
  It must include separate placeholder acceptance criteria for BOTH
  security AND accessibility, never combined, never authored directly.
  FAIL if it's still a question, re-decides something the requirements doc
  already settled, or is missing either placeholder.
focus: last_message
---

Regression test for the ask-then-continue gap, adapted to this round's new
requirements-doc-driven flow.
