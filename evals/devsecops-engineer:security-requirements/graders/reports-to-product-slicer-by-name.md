---
type: llm
criteria: |
  Having found that the slice needs a capability nobody scoped (login),
  the output must explicitly hand this off to `product-slicer` by name —
  the persona that owns scope. Score 0 if `product-slicer` is never named
  as the recipient of this finding, if the finding is handed to a
  different persona (e.g. `software-architect`), or if it's left as a
  standalone observation with no named next owner; 1 if `product-slicer`
  is explicitly named as who this routes to.
focus: last_message
---

Checks the hand-off names its actual owner rather than leaving the
finding to float, which is how a stage gets skipped without anyone
choosing to skip it.
