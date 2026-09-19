---
type: llm
criteria: |
  PASS only if the review flags `'rounds correctly'` — its assertion
  (`expect(result).toBeGreaterThan(0)`) would pass for almost any
  positive number, not just the specific correctly-rounded value
  `applyRounding(9.005)` should produce, so the test wouldn't catch a
  wrong rounding implementation. FAIL if this test isn't flagged as a
  weak assertion / false-positive risk.
focus: last_message
---

Checks the review catches an assertion too weak to actually verify the
behavior its test name claims to check.
