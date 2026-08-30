---
type: llm
criteria: |
  For Directory D (a small, un-mapped problem with an Active requirements
  doc but no slice yet), the output must route to product-slicer
  (vertical-slicing + acceptance-criteria), using the requirements doc as
  the input for WHAT to slice. It must NOT route back to product-manager
  (WHAT is already confirmed) and must NOT route to docs-writer:scope-map
  (already correctly skipped for this small problem). Score 0 if it routes
  anywhere other than product-slicer, or re-litigates the scope-map
  decision; 1 if it correctly routes to product-slicer.
focus: last_message
---

Tests the requirements-doc-exists-but-no-slice row, and specifically that
a requirements doc for the whole problem (no scope map involved) is
handled the same way as one for a single scope-map step.
