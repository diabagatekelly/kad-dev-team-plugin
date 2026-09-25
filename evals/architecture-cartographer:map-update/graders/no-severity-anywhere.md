---
type: llm
criteria: |
  PASS only if nothing in the output attaches a severity label (Critical,
  High, Medium, Low, or any numeric score/rating) to the wrong-direction
  candidate, the duplication candidate, or anything else reported. Plain
  factual description of what changed and what was flagged is expected
  and should pass. FAIL if any severity or scoring language appears
  anywhere in the output, even informally (e.g. "this is a serious
  problem," "high risk," "a 7/10 concern").
focus: last_message
---

Checks this skill carries no severity apparatus at all, sharper than this
roster's usual qualitative-only stance — this persona never reaches the
judgment a severity label would describe.
