---
type: llm
criteria: |
  The "what must be observable" content must be framed around specific,
  named outcomes a user/maintainer needs to be able to tell apart (e.g.
  distinguishing "provider rejected the connection" from "provider was
  unreachable" from "retrieval was incomplete" from "genuinely no
  transactions" from "something in the app broke") rather than generic
  coverage language ("log all requests," "add metrics," "instrument
  everything"). Score 0 if observability is specified as blanket coverage
  with no tie to a specific diagnostic distinction; 1 if it's framed
  around what must be distinguishable and why.
focus: last_message
---

Checks the skill's "driven by a question, not coverage" instruction is
actually followed rather than defaulting to generic instrumentation
advice, which is the easier thing to write.
