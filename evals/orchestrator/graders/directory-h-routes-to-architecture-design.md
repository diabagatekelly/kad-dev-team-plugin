---
type: llm
criteria: |
  For Directory H (a slice exists for scope-map-001 step 1, already
  written up as a user story, no design doc yet), the output must route
  to software-architect:architecture-design for that slice. It must NOT
  report a terminal "stop" state (that row now requires a design doc to
  already exist, which it doesn't here) and must NOT skip ahead to the
  next scope-map step. Score 0 if it reports terminal/stop, routes
  anywhere else, or advances to a different scope-map step; 1 if it
  correctly routes to software-architect:architecture-design.
focus: last_message
---

Tests the row added when software-architect was wired into the routing
table: written-up-but-undesigned is a real intermediate state, not the
same as terminal.
