---
type: llm
criteria: |
  PORTABLE — holds for any design doc, not just this case's fixture.

  The design must state an explicit importance ordering for the slice's
  parts — which pieces are strategic/high-importance versus
  tactical/low-importance/swappable, with reasoning tying importance to
  business risk (how much harm a defect there would cause) — rather than
  leaving the strategic/tactical split implicit or skipping it. Score 0 if
  the design jumps straight to structure/boundaries with no stated
  importance ordering, or lists components without ever saying which are
  more/less important and why; 1 if an explicit ordering is stated with
  reasoning.
focus: last_message
---

Extracted from the retired `stays-conceptual-and-states-importance`
grader, generalized: the original tied its check to this fixture's own
example (CSV-writing mechanics vs. which transactions get included). This
version checks only that an ordering is stated and reasoned, not what it
says — so it holds for any slice this skill designs, and is safe to borrow
when grading a real design doc.

