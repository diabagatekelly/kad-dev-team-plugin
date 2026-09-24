---
type: llm
criteria: |
  Both tests in `pricing.test.ts` mock out `chargeInUsd` itself (the exact
  function under test) and only assert the mock was called
  (`expect(svc.chargeInUsd).toHaveBeenCalled()`) — never checking any real
  return value or behavior. This is a textbook over-mocked/false-positive
  test smell. This skill's own text says over-mocking, false positives, and
  coverage-as-theater are "a different, deeper judgment call" belonging to
  `tdd-coach:test-quality-review`, "not yours; don't re-litigate it here."
  PASS requires this skill NOT rendering its own verdict on the mocking
  quality/test validity itself — it's fine to not mention it at all, or to
  note its existence while explicitly deferring the judgment (e.g. "this
  looks like it may be a test-quality-review concern"), but FAIL if the
  response treats the over-mocking itself as one of this skill's own
  Critical/High/Medium/Low code-review findings (e.g. flagging it as "this
  test doesn't test real behavior" as a graded finding in its own right).
focus: last_message
---

Checks restraint on the test-quality boundary — the companion to
`applies-ordinary-checks-to-test-file`, which checks that ordinary
naming/duplication checks DO apply to test files. This grader checks that
the deeper test-validity judgment does NOT get absorbed into this skill's
own findings.
