---
type: llm
criteria: |
  `chargeInUsd` and `formatCurrencyLabel` in `pricing.ts` both independently
  reimplement "is this USD" logic on a raw `currency` string — one does a
  case-sensitive `!== 'USD'` check, the other does a case-insensitive
  `.toUpperCase() === 'USD'` check. Nothing centralizes what counts as a
  valid/matching currency. PASS requires this being flagged as a primitive
  obsession finding (a raw string standing in for a concept — currency —
  that has its own validation rules, checked inconsistently in different
  places) rather than only being described as plain duplication (the two
  functions aren't textually similar enough to be a duplication finding —
  the actual issue is the missing shared concept, not repeated code). FAIL
  if this is missed entirely.
focus: last_message
---

Checks the primitive obsession check specifically — never exercised by any
prior grader in this case.
