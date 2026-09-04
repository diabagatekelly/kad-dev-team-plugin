---
type: llm
criteria: |
  Grading the final design (output.md), after both decisions were
  approved. The "Decisions" section must show both decisions as having
  been presented for approval and approved — not just stated as if
  autonomously decided — and the rest of the design must actually reflect
  the approved choices: synchronous export (no job-status/notification
  component anywhere in the Structure section) and CSV built directly (no
  generic pluggable-formatter interface anywhere). PASS only if both
  approved decisions are visibly reflected in the design's actual
  structure, not just restated in the Decisions section while the rest of
  the design contradicts them. FAIL if either decision isn't reflected in
  the structure, or if the Decisions section reads as autonomously decided
  rather than approved.
focus: last_message
---

Checks the approval loop actually changes what gets built into the final
artifact, not just what gets narrated in a "Decisions" section.
