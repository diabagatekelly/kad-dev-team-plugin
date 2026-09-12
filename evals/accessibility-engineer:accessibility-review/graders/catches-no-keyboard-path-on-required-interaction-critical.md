---
type: llm
criteria: |
  Reordering accounts is this slice's entire required interaction, and the
  mockup implements it only via `draggable="true"` list items with no
  keyboard-operable alternative anywhere on the page (no move-up/move-down
  controls, no keyboard handler, nothing focusable in the list itself).
  Per the skill's own escalation rule, a required action with no
  accessible path at all is the ceiling of severity regardless of what
  else the review finds.

  PASS requires this finding to be present and rated Critical
  specifically — not High, Medium, or Low. Score 0 if the drag-and-drop
  reorder mechanism's total lack of a keyboard path is missing entirely,
  or is flagged at any severity below Critical; 1 if it's flagged at
  Critical.
focus: last_message
---

Tests the skill's named severity ceiling ("no accessible path at all for
a required action... is Critical even if it's the only finding") against
a fixture built to have exactly one such gap. This is the single most
load-bearing severity call this skill makes — getting it right on
anything less than Critical would mean the scale doesn't actually track
the exclusion it claims to measure.
