---
type: llm
criteria: |
  Across all three answers, PASS only if the response never renders a
  verdict about whether a candidate is "the same thing," "close enough to
  reuse," "a real duplicate," or "fine to build separately" — those calls
  belong to whichever persona asked (`architecture-design` or
  `tdd-implementation`), not to this skill. Reporting facts (paths, tiers,
  exports, the specific shared shape) is expected and should PASS; a
  sentence that crosses into telling the asker what to actually do about a
  candidate should FAIL. A closing line like "this skill only reports
  facts, the reuse call is yours" is fine and does not by itself cause a
  FAIL.
focus: last_message
---

Checks the never-judge, never-decide boundary holds across every answer,
not just one.
