---
type: llm
criteria: |
  PORTABLE — holds for any design system output, not just this case's
  fixture.

  The Accessibility section must state concrete, verifiable choices — a
  declared focus-state treatment, actual contrast ratios checked for the
  real color pairs used (not an assertion that contrast is "fine" or
  "good"), touch-target sizing, and a type scale with distinguishable
  heading levels. It must also frame these as choices that make
  conformance *possible*, not as a claim that a standard (e.g. WCAG) has
  been verified or met — that verification belongs to a different persona.

  Score 0 if contrast is asserted without actual ratios or a stated
  comparison against a threshold, if any of the four required elements
  (focus, contrast, touch target, type scale) is missing, or if the
  section claims compliance was verified/achieved; 1 if all four elements
  are concretely addressed and the section stops short of a compliance
  claim.
focus: last_message
---

Grounded in `skills/design-system/SKILL.md`'s "Design for accessibility by
construction" list and its explicit boundary statement: "This is design
work, not an audit... That check belongs to `accessibility-engineer`."
