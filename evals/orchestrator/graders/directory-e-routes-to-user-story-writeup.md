---
type: llm
criteria: |
  For Directory E (a slice exists for scope-map-001 step 1, not yet
  written up as a user story), the output must route to
  docs-writer:user-story-writeup for that slice. It must NOT route to
  product-slicer for a next step or slice (there is no next step being
  considered here — filing the existing slice comes first), and must NOT
  skip straight to reporting a terminal "stop" state (the slice hasn't
  been written up yet, so this isn't the terminal row). Score 0 if it
  routes to product-slicer, silently skips filing, or reports the terminal
  state prematurely; 1 if it correctly routes to user-story-writeup.
focus: last_message
---

Tests the exact gap the real dogfooding session caught: after a slice is
cut, the very next thing must be filing it as a user story — never
silently treated as "done, move to the next slice."
