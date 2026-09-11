---
type: llm
criteria: |
  `logInvoiceAccess` logs `{ invoice, user }` — entire objects, not
  specific fields or identifiers. PASS requires this being flagged as its
  own finding distinct from "logging is fine because these fields are
  harmless today" — the skill's own framing is that logging a whole object
  is a distinct finding from logging a sensitive field, because it leaks
  every field the object has including ones added later by someone who
  never considered this log line. The suggested fix should point toward
  logging identifiers (e.g. invoice ID, user ID) rather than the objects
  themselves. Score 0 if this is missing, or if the finding is framed only
  as "these particular fields are sensitive" without naming the
  whole-object-logging problem itself; 1 if the whole-object framing is
  present with an identifier-based fix suggested.
focus: last_message
---

Tests the skill's specific "logging a whole object is a distinct finding"
rule, which a review only checking for named-sensitive-field leaks would
miss even while technically reviewing this exact line.
