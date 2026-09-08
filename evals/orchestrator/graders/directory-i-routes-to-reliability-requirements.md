---
type: llm
criteria: |
  For Directory I (slice designed, security criteria filled and no longer a
  placeholder, nothing yet describing failure behavior, empty repo), the
  output must route to devsecops-engineer:reliability-requirements for that
  slice. It must NOT re-route to security-requirements (already filled), must
  NOT skip to technology-bootstrap despite the empty repo, and must NOT
  report a terminal stop. Score 0 if it routes anywhere else or stops; 1 if
  it routes to reliability-requirements.
focus: last_message
---

Covers a routing row added when `devsecops-engineer` was wired in, which had
no fixture until now. Also re-tests the bootstrap-comes-last ordering from a
second starting state.
