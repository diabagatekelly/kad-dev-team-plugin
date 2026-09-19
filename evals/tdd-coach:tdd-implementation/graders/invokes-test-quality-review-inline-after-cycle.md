---
type: llm
criteria: |
  PASS only if the response explicitly runs (or clearly states it ran)
  `test-quality-review` against the tests it just wrote, at least once
  during the `AssignCase` work, before considering that work done — named
  as such, not just a generic "and I reviewed my code" statement. FAIL if
  the response never mentions running or invoking test-quality-review at
  all, or only claims to do so once at the very end covering everything
  rather than as part of the cycle.
focus: last_message
---

Checks the REVIEW step of the cycle actually happens and is named,
matching AGENT.md's "runs test-quality-review against its own tests as
part of its own loop."
