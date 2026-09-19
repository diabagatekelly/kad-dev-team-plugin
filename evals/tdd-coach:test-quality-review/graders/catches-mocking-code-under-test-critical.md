---
type: llm
criteria: |
  PASS only if the review flags `'calculateTotal returns the discounted
  total'` (the test that does `vi.spyOn(service, 'calculateTotal')
  .mockReturnValue(999)` — replacing the exact method under test with a
  mock, then asserting `result === 999`, a value the mock configured
  itself) as mocking the code under test, and rates it Critical — the
  test can never fail regardless of whether the real `calculateTotal`
  implementation is correct. FAIL if this test is missed entirely, or
  flagged at any severity other than Critical.
focus: last_message
---

Checks the single most serious category is caught and rated correctly —
a test that replaces its own subject's behavior and then asserts on the
replacement's own configured output is invalid, not just weak.
