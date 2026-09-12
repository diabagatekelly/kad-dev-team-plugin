---
type: llm
criteria: |
  PORTABLE — holds for any screen design output, not just this case's
  fixture.

  The output must name which established design-system patterns each
  rendered state uses (e.g. a named Card, Button, empty-state pattern),
  rather than composing the screen from ad hoc, unnamed styling. Any
  genuinely new pattern this screen needs must be explicitly flagged back
  to `design-system` in a "New patterns proposed" section, not invented
  silently and left unflagged.

  Score 0 if the output never names which existing patterns it's using, or
  if it introduces new visual treatment not traceable to an existing
  pattern without flagging it as new; 1 if pattern reuse is explicit and
  any new pattern is flagged rather than silently invented.
focus: last_message
---

Grounded in `skills/screen-design/SKILL.md`'s "Reuse before you invent"
section and its "New patterns proposed, if any" output requirement:
"flag[ged] back to `design-system` rather than invented ad hoc."
