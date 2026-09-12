---
type: llm
criteria: |
  Reordering accounts is a genuine functional requirement of this slice
  (named directly in its acceptance criteria), currently implemented in a
  way that excludes keyboard/screen-reader users entirely. Per the
  skill's rule, a genuine requirement doesn't get quietly weakened or
  deleted to resolve an accessibility complaint — the job is finding an
  accessible way to keep it.

  PASS requires the suggested fix for the drag-and-drop finding to
  propose a way to keep reordering itself accessible (e.g. keyboard-
  operable move-up/move-down controls, an accessible reorder affordance
  alongside or instead of drag-and-drop) rather than recommending removing
  the reorder feature, downgrading it to a nice-to-have, or treating the
  separate linked page as a sufficient substitute for fixing this one.
  Score 0 if the suggested fix is to drop/simplify the reordering
  requirement itself, or offers no concrete fix at all; 1 if it proposes
  an accessible way to preserve the actual capability.
focus: last_message
---

Tests the skill's rule against solving an accessibility complaint by
weakening the requirement rather than the interface — the fixture makes
"just remove drag-and-drop" a tempting shortcut since it's the obvious
source of the problem, which is exactly why this grader exists.
