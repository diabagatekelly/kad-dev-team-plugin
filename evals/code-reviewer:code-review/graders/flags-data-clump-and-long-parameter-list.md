---
type: llm
criteria: |
  In `pricing.ts`, `street, city, state, zip` travel together across three
  separate function signatures (`validateAddress`, `printShippingLabel`,
  `scheduleDelivery`) — a data clump, candidate for one Address
  object/parameter. `scheduleDelivery` also has seven parameters total,
  independently long enough to warrant a look as a parameter list on its
  own. PASS requires BOTH being named: the data clump (the same group of
  values recurring across multiple signatures, suggesting a shared object)
  and the long parameter list on `scheduleDelivery` specifically (whether
  as one finding or two). FAIL if neither is mentioned, or if only one of
  the two is mentioned.
focus: last_message
---

Checks both the data clump check and the long-parameter-list check —
neither exercised by any prior grader in this case. Deliberately combined
into one grader since they're the same underlying code pattern.
