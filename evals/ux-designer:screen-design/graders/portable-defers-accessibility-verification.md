---
type: llm
criteria: |
  PORTABLE — holds for any screen design output, not just this case's
  fixture.

  The output must not claim that a specific accessibility standard (e.g.
  WCAG) has been verified or met for this screen. It's acceptable, and
  expected, for the design to follow the design system's by-construction
  rules (focus states, contrast-conformant colors, color never carrying
  meaning alone) — but confirming actual conformance must be named as
  belonging to `accessibility-engineer`, not claimed here.

  Score 0 if the output asserts or implies this screen has been verified
  accessible/WCAG-conformant; 1 if it either says nothing about
  conformance verification, or explicitly defers it to
  `accessibility-engineer`.
focus: last_message
---

Grounded in `skills/screen-design/SKILL.md`'s "What this decides, and what
it doesn't": "It also does not verify accessibility compliance — design so
it holds up, but confirming it belongs to `accessibility-engineer`."
