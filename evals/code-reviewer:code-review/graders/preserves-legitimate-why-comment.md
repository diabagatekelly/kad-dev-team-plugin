---
type: llm
criteria: |
  The comment above `applyStateTax` ("Tax rate is intentionally asymmetric
  for digital vs. physical goods per state statute §7.2 — not a bug.")
  explains a non-obvious business rule that the code alone can't express —
  exactly the kind of comment `why-comments` is supposed to preserve, not
  the kind code-review flags for removal. PASS requires this comment NOT
  being flagged as a finding (not listed as removable, not criticized as
  unnecessary or WHAT-not-WHY). FAIL if it's flagged for removal or rewrite,
  for any reason.
focus: last_message
---

False-positive check: verifies the WHY-not-WHY test isn't applied so
aggressively that it starts flagging comments that genuinely earn their
place.
