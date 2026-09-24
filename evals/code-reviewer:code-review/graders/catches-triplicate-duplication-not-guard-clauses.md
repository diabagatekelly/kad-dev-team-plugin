---
type: llm
criteria: |
  `calculateShippingCost`, `calculateHandlingFee`, and `calculateInsuranceFee`
  are near-identical: same weight-based base cost, same domestic/international
  branch shape, differing only in the per-zone constants (5/25, 3/15, 1/8).
  PASS requires this three-way duplication flagged as a real finding (High or
  Critical severity), described as a candidate for consolidating into one
  parameterized function rather than three near-copies.

  Separately, all three functions also share an identical one-line guard
  clause (`if (!order) return 0;`) — PASS requires this guard clause NOT
  being flagged as part of the duplication finding, or not flagged at all.
  It's exactly the kind of short, conventional pattern this skill's own
  scope excludes from DRY findings.

  FAIL if the three-function duplication is missed entirely, or if the
  one-line guard clause is flagged as a duplication violation (with or
  without the real finding also being caught).
focus: last_message
---

Checks the flagship DRY finding is caught, and that the skill's own
stated exemption for short conventional patterns (guard clauses) actually
holds rather than being stated and then ignored.
