---
type: llm
criteria: |
  PORTABLE — holds for any design doc, not just this case's fixture.

  The design must stay conceptual throughout: no code snippets, no
  pseudo-code, no literal file paths, and no function/method signatures.
  Naming components, boundaries, and interfaces in plain structural terms
  is correct; describing implementation syntax is not. Score 0 if any
  code, file path, or signature appears anywhere in the output; 1 if the
  whole document stays at the structural/conceptual level.
focus: last_message
---

Extracted from the retired `stays-conceptual-and-states-importance`
grader, split out because it holds regardless of fixture content — this is
the same discipline `adr` applies to decision records, and every design
this skill produces should be checkable against it.

