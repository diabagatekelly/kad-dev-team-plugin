---
type: llm
criteria: |
  PASS only if the review flags `'uses a mocked discount client, logger,
  cache, and audit trail'` for excessive/unnecessary mocking — four mocks
  in one test, three of which (logger, cache, audit) have nothing to do
  with what `calculateTotal` actually needs to be tested, and the
  assertions only check those irrelevant mocks were never called rather
  than testing real pricing behavior. FAIL if this test isn't flagged, or
  is flagged only for something else (e.g. only called out as a useless
  test) without naming the mocking excess itself.
focus: last_message
---

Checks excessive mocking is recognized even when the assertions
technically "pass" — the mocks themselves are the problem, not just the
assertions.
