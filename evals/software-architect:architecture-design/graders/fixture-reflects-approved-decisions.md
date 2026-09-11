---
type: llm
criteria: |
  FIXTURE-SPECIFIC — asserts this case's own two decisions, not a general
  property.

  Grading the final design (output.md), after both decisions were
  approved. The rest of the design must actually reflect the approved
  choices: synchronous export (no job-status/notification component
  anywhere in the Structure section) and CSV built directly (no generic
  pluggable-formatter interface anywhere). PASS only if both approved
  decisions are visibly reflected in the design's actual structure, not
  contradicted by it. FAIL if either decision isn't reflected in the
  structure. General "was this narrated as approved rather than
  autonomous" quality is graded separately by
  `portable-decisions-shown-as-approved`, which this grader no longer
  duplicates.
focus: last_message
---

Checks the approval loop actually changes what gets built into the final
artifact, not just what gets narrated in a "Decisions" section. Trimmed to
drop the general approval-narrative check once
`portable-decisions-shown-as-approved` was split out to cover it — this
grader now checks only whether *this fixture's* two specific choices
survived into the structure.
