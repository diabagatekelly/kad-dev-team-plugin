---
type: llm
criteria: |
  PASS only if the review does NOT flag `'calculates total with discount'`
  — specifically its `vi.spyOn(discounts, 'discountFor')` call on
  `StubDiscountLookup`, the codebase's designated test double — as a
  mocking violation of any kind. `PricingService` itself is still fully
  exercised in that test; only its external dependency is standing in for
  the real thing, which this skill's own acceptable-patterns rule treats
  as normal test infrastructure. FAIL if this test is flagged as
  mocking-the-code-under-test, excessive mocking, or any other violation.
focus: last_message
---

Checks the review doesn't produce a false positive on the one pattern
that's explicitly supposed to be fine — spying on a designated stub, not
the subject under test.
