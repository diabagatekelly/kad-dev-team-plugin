---
type: llm
criteria: |
  The final output must NOT include a thin path, Given/When/Then
  acceptance criteria, or a slicing-technique decision (happy-path-first,
  input variations, reduce scope, etc.) — those belong to product-slicer
  and acceptance-criteria, invoked later, once this hands off a decided
  WHAT. Score 0 if the output includes any of these; 1 if it stays at
  who/what/why/confirmed-in/confirmed-out, in plain language, with no
  technical slicing content.
focus: last_message
---

Boundary test mirroring the same discipline `scope-map` holds against
slicing/design content — this persona hands off a decided WHAT, it doesn't
also decide HOW.
