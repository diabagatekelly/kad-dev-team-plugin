---
type: llm
criteria: |
  The export route's catch block returns `{ error: err.message, stack:
  err.stack }` directly to the caller — internal detail (a stack trace)
  reaching an external response. PASS requires this being flagged as an
  information-disclosure finding per the skill's explicit framing ("a
  caller learns that their request failed; they don't learn why in terms
  that describe your internals"). Score 0 if this is missing or treated
  only as an ergonomics/code-quality issue rather than a security finding;
  1 if flagged as information disclosure.
focus: last_message
---

Tests the skill's explicit stance that internal detail reaching a caller
is a security finding, not just sloppy error handling.
