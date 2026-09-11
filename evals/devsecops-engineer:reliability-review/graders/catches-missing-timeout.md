---
type: llm
criteria: |
  `fetch(...)` in `infra/bankClient.ts` has no timeout or abort signal —
  if the provider accepts the connection but never responds, the call
  waits indefinitely. PASS requires this being flagged as a missing
  timeout, per the skill's explicit framing: "a call with no timeout
  doesn't fail — it waits, holding whatever it holds, until something
  upstream gives out," and that this class is commonly missed because
  "nothing looks wrong until the day it does." Score 0 if this finding is
  absent; 1 if the missing timeout is identified as its own finding
  (not merged into "the fetch might fail," which is a different claim).
focus: last_message
---

Tests the skill's explicitly named "most commonly missed" failure mode
against a fixture built to have it.
