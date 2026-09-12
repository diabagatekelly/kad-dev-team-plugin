---
type: llm
criteria: |
  Both nav-rail icons are `<div class="icon-nav" onclick="...">` elements
  with no `role`, no `tabindex`, and only a `title` attribute — not a real
  `<button>`/`<a>`, and not keyboard-focusable at all despite visually
  reading as clickable navigation.

  PASS requires this to be flagged as a finding distinct from a missing
  focus *style* (this is a missing focus *target* — nothing there to
  style in the first place), with a fix naming a real interactive element
  or the role/tabindex/keyboard-handling equivalent. Score 0 if this is
  missing entirely, or is conflated with/described only as a contrast or
  focus-style issue; 1 if it's named as its own finding with a correct
  fix.
focus: last_message
---

Tests the skill's seventh check ("anything that looks interactive is a
real interactive element"), added to `SKILL.md` after a real dogfood run
against `evals/example/`'s mockups surfaced this exact pattern — nav
icons and a quick-action control built as styled `<div>`s with no
keyboard path at all. This grader confirms the fix that dogfood run
produced actually generalizes to a fresh fixture, not just the one that
found it.
