---
type: llm
criteria: |
  Grading the final design, after the scripted synchronous-export answer.
  Two checks: (1) the design states an explicit importance ordering for
  this slice's parts (e.g. which transactions get included is a business
  rule worth keeping independent of the CSV library, vs. the CSV-writing
  mechanics themselves being low-importance/swappable) rather than leaving
  the strategic/tactical split implicit or skipping it; (2) the design
  stays conceptual — no code, no file paths, no function signatures. A
  design that reads like a spec of what components exist and how they
  relate, without pseudo-code, passes the second check; one that includes
  actual code snippets or literal file paths fails it. FAIL if either
  check fails.
focus: last_message
---

Checks the design applies the importance-as-risk framing explicitly and
respects the conceptual-only output discipline.
