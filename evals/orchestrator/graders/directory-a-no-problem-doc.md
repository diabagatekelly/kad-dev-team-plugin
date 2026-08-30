---
type: llm
criteria: |
  For Directory A (empty directory, invoked with the parameter given), the
  output must recognize no problem framing doc exists and route to
  docs-writer:problem-framing-doc. Score 0 if it routes anywhere else,
  invents a problem, or asks an unrelated question; 1 if it correctly
  identifies the missing-problem-doc row and routes there.
focus: last_message
---

Tests the routing table's first row — the simplest case, and a baseline
that should never regress.
