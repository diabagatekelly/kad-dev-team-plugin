---
type: llm
criteria: |
  For Directory C (an Active scope map with 4 steps, no requirements docs
  and no slices anywhere), the output must identify step 1 ("Transaction
  retrieval") as the current unit — the lowest-numbered step with no
  requirements-refinement doc yet — and route to
  product-manager:requirements-refinement for that step. It must NOT route
  to product-slicer directly (no WHAT has been confirmed yet) and must NOT
  pick a different step. Score 0 if it routes to product-slicer, skips
  product-manager, or targets the wrong step; 1 if it correctly routes to
  product-manager for step 1.
focus: last_message
---

Tests that product-manager is actually wired into the routing table
between scope-map and slicing, and that it's targeted at the right step.
