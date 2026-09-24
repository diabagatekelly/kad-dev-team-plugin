---
type: llm
criteria: |
  `getOrderStatusLabel` in `pricing.ts` is long by raw line count (over 30
  case branches) but is purely mechanical — every branch is a single,
  uniform one-line lookup (`case 'x': return 'Y';`), with no real logic,
  branching complexity, or mixed concerns. This skill's own text is
  explicit that size anchors "prompt a closer look" and are "not the
  finding itself" — "going over the line isn't automatically a violation."
  PASS requires this function NOT being flagged as a real, blocking
  readability finding just for its length — it's acceptable to not mention
  it at all, or to note in passing that it's long but fine given how
  uniform it is. FAIL if it's flagged as a genuine "this function is too
  long, split it up" finding with no acknowledgment that its length comes
  from uniform, low-complexity repetition rather than mixed concerns.
focus: last_message
---

Checks restraint on the size-anchor rule specifically — the companion to
`flags-long-multi-concern-function`, which checks detection on a function
that's long AND actually doing several different jobs. This grader tests
the opposite shape: long but NOT multi-concern, which per the skill's own
text should not be auto-flagged.
