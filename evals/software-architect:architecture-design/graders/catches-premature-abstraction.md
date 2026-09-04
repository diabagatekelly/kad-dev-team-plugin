---
type: llm
criteria: |
  Grading phase 2 — the response after the synchronous-export decision was
  approved. The engineer proposed a generic export interface with
  pluggable formatters "for later" even though only CSV is needed now —
  this is a premature abstraction (no second concrete format exists
  today). PASS only if this response: (a) does NOT silently decide this
  and move straight to a finished design — it must present this as its
  own decision, separate from the first one; (b) recommends rejecting the
  generic interface, with reasoning tied to there being no second concrete
  use case yet (not just a vague "keep it simple" without naming why);
  (c) names the alternative considered (building the generic interface
  now) and why it's rejected; (d) explicitly asks for approval rather than
  asserting the rejection as already final. FAIL if it accepts the
  generic interface, decides the rejection without asking, bundles this
  with unrelated content, or fails to name why it's premature.
focus: last_message
target: phase2
---

Checks the two-sided YAGNI mandate surfaces as an approval-seeking
decision even when the persona is confident in its recommendation — a
confident call doesn't get to skip the approval loop.
