---
type: llm
criteria: |
  PASS only if the review uses the Critical/High/Medium/Low severity
  scale (not a different vocabulary — no axe-style
  critical/serious/moderate/minor, no plain blocking/non-blocking), rates
  the mocking-code-under-test finding Critical, and each individual
  finding names a location, category, and severity plus a concrete
  suggested fix — not just prose describing problems in general terms
  with no per-finding structure. FAIL if severity labels are absent,
  use a different vocabulary, or findings aren't individually
  identifiable with a location and suggested fix.
focus: last_message
---

Checks the review uses this roster's shared Critical/High/Medium/Low
scale and produces individually actionable findings, not an unstructured
narrative.
