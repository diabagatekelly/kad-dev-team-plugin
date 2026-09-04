---
type: llm
criteria: |
  For Directory F (same as E, but the user confirms slice 1 has been
  written up as a user story AND software-architect has already produced
  a design doc for it), the output must recognize this is the routing
  table's terminal row and STOP — explicitly stating that this is as far
  as the roster currently reaches, that tdd-coach would implement this
  slice next, and that tdd-coach doesn't exist yet. It must explicitly NOT
  propose starting requirements-refinement or slicing for scope-map-001
  step 2, or any other next scope-map step, as the next action — even as
  an offered option. It must also NOT route back to
  software-architect:architecture-design (the design already exists for
  this slice). Score 0 if it proposes advancing to step 2 (or any other
  step) in any form, or re-routes to architecture-design; 1 if it
  correctly stops and names tdd-coach as the (currently unavailable) next
  stage.
focus: last_message
---

Tests the most important behavioral fix from this round: the roster must
never cascade across scope-map steps automatically, because each unit
needs design/implementation before the next one's shape should be decided
— the same reason CAMS's own workflow iterates per-slice instead of
front-loading every slice. The terminal condition itself moved (design
doc exists, not just user-story-filed) now that software-architect is
wired in — this grader was updated to match, with directory-h below
covering the row that used to be terminal.
