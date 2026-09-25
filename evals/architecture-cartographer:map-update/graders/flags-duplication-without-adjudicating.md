---
type: llm
criteria: |
  `domain/refund-ledger.ts` and `domain/credit-ledger.ts` share an import
  target (`domain/order-directory.ts`) and an overlapping export shape (a
  record-with-order-id-and-amount method, a list-by-order method) under
  different literal names. PASS only if this pair is flagged as a
  duplication candidate, naming the specific shared import target and/or
  the shared shape as the basis. The flag must stop at the candidate fact
  — it must NOT declare the pair a real duplicate that should be merged,
  and must NOT declare them definitely fine to stay separate; the response
  should either stay silent on which verdict is correct or explicitly
  note both are possible (shared shape today, could still be genuinely
  different concerns that diverge). FAIL if the pair is missed, or if the
  response renders either verdict (merge them / leave them, stated as a
  conclusion rather than an open candidate).
focus: last_message
---

Checks duplication candidates are discovered mechanically and the
coincidental-vs-real judgment is explicitly left open, not decided here.
