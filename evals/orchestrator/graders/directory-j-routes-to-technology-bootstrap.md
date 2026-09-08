---
type: llm
criteria: |
  For Directory J (slice designed, BOTH security and reliability criteria
  filled, and the user confirms the repo has no language/test
  runner/package manager set up), the output must route to
  software-architect:technology-bootstrap. It must NOT report a terminal stop
  (the project has no stack, so the terminal row's condition isn't met), and
  must NOT advance to another scope-map step. Score 0 if it stops or routes
  elsewhere; 1 if it routes to technology-bootstrap.
focus: last_message
---

Covers the routing row added with the `technology-bootstrap` skill. This is
the one state where bootstrapping is correct — everything upstream is
satisfied and the only thing blocking the first failing test is the absence
of a stack.
