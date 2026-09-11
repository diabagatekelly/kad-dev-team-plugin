---
type: llm
criteria: |
  PORTABLE — holds for any design doc, not just this case's fixture.

  For at least one boundary the design introduces, the "Boundaries and
  interfaces" section (or equivalent) must state what actually crosses
  that boundary — and it must be plain data (primitives, plain
  objects/arrays of those), not a framework type, ORM model, or a type
  carrying library-attached methods, unless a translation step at the edge
  is explicitly named for it. Score 0 if boundaries are named without ever
  saying what crosses them, or if what's stated to cross a boundary is a
  non-plain-data/framework-attached type with no translation step named;
  1 if at least one boundary states its crossing type and it's plain data
  (or a named translation makes it so).
focus: last_message
---

New grader, not extracted from an existing one — added to cover Good
Fences, which none of this case's prior graders checked at all. Holds for
any design with at least one boundary, which every non-trivial slice has.

