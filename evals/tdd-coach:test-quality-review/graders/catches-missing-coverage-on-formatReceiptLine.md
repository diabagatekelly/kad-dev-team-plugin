---
type: llm
criteria: |
  PASS only if the review notes that `formatReceiptLine` is exported from
  `pricing.ts` but has zero tests anywhere in `pricing.test.ts`. FAIL if
  this gap isn't mentioned at all.
focus: last_message
---

Checks missing coverage on an exported function is caught, not just
issues with tests that already exist.
