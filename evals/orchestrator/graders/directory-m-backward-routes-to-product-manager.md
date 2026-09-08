---
type: llm
criteria: |
  For Directory M (slice-000 exists, and its own "Still open" section states
  that a requirements-refinement pass never ran for its step because it was
  created by a mid-flight scope decision; the only requirements doc present
  is scoped to a different step), the output must apply BACKWARD routing and
  route to product-manager:requirements-refinement for slice-000's step. It
  must NOT route forward to docs-writer:user-story-writeup or
  architecture-design on the grounds that a slice exists, and must NOT treat
  the existing requirements-001 as covering this slice's step. Score 0 if it
  routes forward or accepts the mismatched requirements doc; 1 if it detects
  the self-reported skipped stage and routes back to product-manager.
focus: last_message
---

Tests the second backward-routing signal: an artifact whose own text says a
stage was skipped for it. Taken verbatim from a real dogfooded artifact —
`slice-000.md` in this plugin's own `evals/example/` flagged precisely this
about itself, and nothing in the spine could act on it, because the table was
forward-only.

Also tests that a requirements doc scoped to a *different* step doesn't
satisfy the requirements row for this one.
