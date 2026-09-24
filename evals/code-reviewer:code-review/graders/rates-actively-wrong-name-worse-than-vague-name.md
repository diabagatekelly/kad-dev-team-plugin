---
type: llm
criteria: |
  Two naming issues in `pricing.ts`: `getActiveDiscount(order)` is actively
  wrong — its name promises fetching a discount, but the function actually
  zeroes out any existing discount and adds a 2% surcharge instead.
  `process(order)` is merely vague — it doesn't say what kind of processing
  happens, but it doesn't claim anything false either (it just stamps a
  processedAt timestamp). This skill's own text says "a name that's
  actively wrong outranks a name that's merely vague" and defines Critical
  severity as code that "actively misleads a future edit into being
  wrong." PASS requires `getActiveDiscount` being rated a clearly higher
  severity than `process` (ideally Critical for the former, given it's a
  "get" that actually mutates and does the opposite of what it claims;
  Medium or Low is acceptable for the latter). FAIL if both are rated the
  same severity, if `getActiveDiscount` is rated lower than or equal to
  `process`, or if `getActiveDiscount`'s misleading nature isn't called out
  as worse than ordinary vagueness.
focus: last_message
---

Checks severity calibration on naming specifically (as opposed to
comments, already tested) — a name that lies is worse than a name that's
merely unhelpful, and the skill's severity taxonomy should reflect that
distinction, not just detect both as generic "naming" findings.
