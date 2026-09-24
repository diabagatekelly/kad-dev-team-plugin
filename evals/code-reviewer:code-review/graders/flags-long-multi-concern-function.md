---
type: llm
criteria: |
  `reconcileNightlyLedger` in `pricing.ts` is long and visibly does at
  least four distinct jobs in sequence: validating entries, converting
  currencies, deduplicating by id+postedAt, building a per-currency
  breakdown, and aggregating totals (plus logging). PASS requires this
  being flagged as a real finding about its size/shape — not just a
  passing mention, but an actual finding noting it does multiple distinct
  jobs and would benefit from being split. FAIL if this function isn't
  flagged at all.
focus: last_message
---

Checks the "long function actually doing several jobs" half of the
size-anchor rule — detection, as opposed to the companion
does-not-auto-flag grader, which checks restraint on a function that's
long but NOT multi-concern.
