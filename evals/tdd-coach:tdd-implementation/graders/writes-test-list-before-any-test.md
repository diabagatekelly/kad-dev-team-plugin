---
type: llm
criteria: |
  PASS only if the response starts with a Test List — the scenarios
  `AssignCase` needs, listed before any test code appears — and then works
  it one entry at a time (write one test, make it pass, refactor, review,
  then move to the next entry), not by writing every test up front and
  implementing them as a batch afterward. FAIL if test code appears before
  any list of scenarios exists, or if multiple tests are written together
  before the first one is made to pass.
focus: last_message
---

Checks the Test List discipline itself — analysis before implementation,
one entry worked at a time, not a batch.
