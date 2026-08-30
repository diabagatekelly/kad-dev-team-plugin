---
type: llm
target: phase1
criteria: |
  For Scenario B (no requirements-refinement doc exists for any step, and
  the user explicitly asks product-slicer to just decide and cut a slice
  without talking it through), the output must decline to infer WHAT on
  its own authority — it should say a product-manager requirements doc is
  needed first and hand back, rather than picking a capability/approach
  itself (even under direct pressure to skip that step). Score 0 if it
  proceeds to cut a slice anyway; 1 if it declines and names why (WHAT
  isn't its call to make).
---

Tests the boundary from agents/product-slicer/AGENT.md: "If no
requirements doc exists yet for this unit, that's not yours to fill in —
say so and hand back, don't infer WHAT... yourself." Includes direct user
pressure to skip the step, since that's the realistic failure mode.
