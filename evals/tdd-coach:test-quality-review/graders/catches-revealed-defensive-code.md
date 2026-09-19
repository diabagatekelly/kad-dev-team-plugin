---
type: llm
criteria: |
  PASS only if the review flags `'returns 0 for undefined items'` (and/or
  the `if (!items) return 0;` guard it exercises) as testing a defensive
  path for a state the type signature already rules out — `items` is
  typed as required, so a real caller can never pass `undefined`, and the
  test only reaches this branch via a `@ts-expect-error` escape hatch.
  FAIL if this isn't flagged as unnecessary defensive coding revealed by
  the tests.
focus: last_message
---

Checks the review recognizes a test written specifically to justify
defensive code for a state that can't actually occur.
