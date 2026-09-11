---
type: llm
criteria: |
  The output must treat normal, non-buggy outcomes — the provider
  legitimately rejecting the connection, the account genuinely having no
  transactions in the period — as expected failures with their own plain
  explanation, not as errors. It must also name that a genuine unexpected
  fault inside the app (a bug) needs to remain visible to whoever
  maintains it and must not be disguised as one of the expected outcomes
  above. Score 0 if expected outcomes are treated as generic errors, or if
  there's no distinction at all between an expected failure and an
  unexpected fault; 1 if both categories are named and kept distinguishable
  from each other.
focus: last_message
---

Checks the skill's expected-vs-unexpected distinction is actually applied
to this slice's specific failure modes, not just restated as a general
principle.
