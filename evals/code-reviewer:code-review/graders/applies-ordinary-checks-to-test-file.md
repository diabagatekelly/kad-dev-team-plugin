---
type: llm
criteria: |
  Both test cases in `pricing.test.ts` are named `'t1'` — an identical,
  uninformative test name used twice in the same `describe` block. This
  skill's own text says test files "get the same read as any other file"
  for naming, comments, and duplication. PASS requires the duplicate/
  uninformative `'t1'` test names being flagged as a naming issue, the same
  way a duplicate or unclear name anywhere else in this PR would be. FAIL
  if `pricing.test.ts` is skipped entirely from review, or if the
  duplicate/vague test names aren't flagged.
focus: last_message
---

Checks that ordinary code-review checks actually extend to test files, not
just application code — never exercised by any prior grader in this case.
