---
type: llm
criteria: |
  `isValidSku` and `isValidWarehouseCode` in `pricing.ts` are structurally
  identical (same two guard checks, same shape), but appear only twice —
  not three or more times. This skill's own duplication rule says two
  instances is "a note to watch for a third, not yet a finding," distinct
  from three-or-more being a real one. PASS requires this pair NOT being
  presented as a ranked Critical/High/Medium/Low finding — it may be
  mentioned as a lower-key note to watch for a third occurrence, or not
  mentioned at all. FAIL if it's presented as a real, severity-rated
  duplication finding on the same footing as the three-way
  `calculate*Fee` duplication in `orders.ts`.
focus: last_message
---

Checks the two-instance threshold is actually respected, not just stated —
a common failure mode is treating "differs only by instance count" as not
worth tracking and flagging any structural repetition regardless of count.
