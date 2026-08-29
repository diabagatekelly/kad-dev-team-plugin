---
type: llm
criteria: |
  The output must NOT propose a solution, technology choice, or design
  decision (e.g. naming a bank-aggregation API, a specific tech stack, or an
  implementation approach). It should only capture the problem, why now,
  constraints, non-goals, and open questions. Score 0 if any solution/design
  content appears; 1 if it stays strictly to problem framing.
focus: last_message
---

Problem framing docs are not specs — this is the skill's own core rule
under test.
