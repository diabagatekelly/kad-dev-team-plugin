---
type: llm
criteria: |
  PORTABLE — holds for any design system output, not just this case's
  fixture.

  Every required token category — color, typography, spacing,
  border-radius, shadow/elevation, and motion — must have either a
  declared value or an explicit "none, deliberately" statement. A category
  that's simply absent from the output, with no indication it was
  considered, fails: the skill's own text requires silent omission to be
  distinguishable from a deliberate decision.

  Score 0 if any of the six categories is missing entirely with no
  "none, deliberately" statement in its place; 1 if all six are addressed
  one way or the other.
focus: last_message
---

Grounded in `skills/design-system/SKILL.md`'s "Declare the tokens"
section: "'none, deliberately' is a valid answer for a category the
project genuinely doesn't need yet; silent absence is not, because nothing
distinguishes an omission from a decision."
