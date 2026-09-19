---
type: llm
criteria: |
  PASS only if the review flags `'applies zero discount when lookup
  fails'` for creating `mockDiscountFor` (a `vi.fn().mockReturnValue(0.5)`)
  that is never actually attached to `discounts` via `vi.spyOn` or any
  other wiring — the real `StubDiscountLookup.discountFor` (returning `0`
  by default) is what actually runs, and the assertion
  (`expect(total).toBe(100)`) passes because of that real default, not
  because of anything the "mock" did. FAIL if this test isn't flagged, or
  if the review's explanation doesn't identify that the mock was never
  wired to anything real (e.g. if it's only flagged as "weak" without
  naming the actual defect).
focus: last_message
---

Checks the review catches a mock that looks like it's testing the fallback
path but was never actually wired to intercept the real dependency.
