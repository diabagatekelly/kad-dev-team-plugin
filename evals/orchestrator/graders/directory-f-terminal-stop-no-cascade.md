---
type: llm
criteria: |
  For Directory F (same as E, but the user confirms slice 1 has already
  been written up as a user story), the output must recognize this is the
  routing table's terminal row and STOP — explicitly stating that this is
  as far as the roster currently reaches, that software-architect would
  design this slice next, and that software-architect doesn't exist yet.
  It must explicitly NOT propose starting requirements-refinement or
  slicing for scope-map-001 step 2, or any other next scope-map step, as
  the next action — even as an offered option. Score 0 if it proposes
  advancing to step 2 (or any other step) in any form; 1 if it correctly
  stops and names software-architect as the (currently unavailable) next
  stage.
focus: last_message
---

Tests the most important behavioral fix from this round: the roster must
never cascade across scope-map steps automatically, because each unit
needs design/implementation before the next one's shape should be decided
— the same reason CAMS's own workflow iterates per-slice instead of
front-loading every slice. This was the orchestrator's original (wrong)
default behavior before this fix.
