---
type: llm
criteria: |
  `legacyCalc` is explicitly marked in the task as pre-existing and not
  touched by this PR. It has real issues (cryptic name and parameters, a
  WHAT-not-WHY comment) that would be flagged normally on new code. PASS
  requires one of: (a) it isn't flagged at all, or (b) it's flagged but
  explicitly marked as pre-existing/lower-priority/not-blocking, separate
  from the findings against the actually-new code in this PR. FAIL if
  `legacyCalc`'s issues are presented as primary, blocking findings on the
  same footing as the new code's real issues, with no acknowledgment that
  this file section predates the PR.
focus: last_message
---

Checks the Boy Scout Rule actually holds in practice: review what changed,
don't demand the whole file be clean first.
