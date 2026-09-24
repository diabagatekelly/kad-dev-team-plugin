---
type: llm
criteria: |
  The comment above the retry loop in `processOrder` says "retried up to 5
  times," but the loop condition is `i < 3` — the comment states a number
  the code doesn't actually implement. PASS requires this being flagged as
  a finding, AND rated Critical severity specifically — this skill's own
  severity taxonomy defines Critical as code that actively misleads a
  future editor into believing something false about current behavior,
  which is exactly this case (a future edit relying on "retries 5 times"
  would be wrong). FAIL if this mismatch isn't caught at all, or if it's
  caught but rated High/Medium/Low instead of Critical.
focus: last_message
---

Checks not just detection but severity calibration — this is the one
finding in the fixture built specifically to test whether Critical is
reserved for actively-misleading code rather than used loosely for
anything that looks bad.
