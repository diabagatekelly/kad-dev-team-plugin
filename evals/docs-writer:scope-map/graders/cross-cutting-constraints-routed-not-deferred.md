---
type: llm
criteria: |
  The source problem doc carries constraints that apply across every step
  rather than being a step of their own — notably the high security bar on
  real account data, and the requirement that AI-assisted categorization run
  at no ongoing cost.

  If the output addresses such a constraint at all (most likely in an "Out of
  scope" or equivalent section), it must do BOTH of the following:
  (a) say the constraint is cross-cutting rather than a step, AND
  (b) say it gets applied at each step's own requirements-refinement pass.

  It is a FAIL if the output routes a cross-cutting constraint to per-slice
  design or to a later persona — phrasings like "gets made concrete per slice
  as each is designed," "handled during design," or "left to
  software-architect" all fail, because they defer a whole-problem constraint
  past the point where scope is decided.

  It is also a FAIL if a cross-cutting constraint is turned into a numbered
  step of its own (e.g. a "Security" step), since that misrepresents
  something that applies to every step.

  Score 1 if cross-cutting constraints are either correctly identified and
  routed to requirements-refinement, or simply not mentioned at all (silence
  is acceptable — the template's Out of scope section is conditional). Score
  0 only if one is mentioned and mis-routed, or made into a step.
focus: last_message
---

Tests the rule added after a real dogfooding run, where this exact skill
produced the line "Protecting the financial data is deliberately not a step.
It applies to every step that touches transactions... and gets made concrete
per slice as each is designed." The first half is right; the second half
defers a whole-problem constraint to design, and it resurfaced after slicing
when the only fixes left were re-slicing or growing a slice.

Deliberately tolerant of silence: the scope-map template makes Out of scope
conditional, and this grader shouldn't force a section the template says to
omit when unneeded. It only fires when the map does mention a cross-cutting
constraint and sends it somewhere wrong.
