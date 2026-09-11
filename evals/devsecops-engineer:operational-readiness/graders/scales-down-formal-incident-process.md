---
type: llm
criteria: |
  The developer explicitly asks whether they should set up an on-call
  rotation and a post-mortem template before shipping, for a personal
  project they alone use. PASS requires the output to decline this per
  the skill's explicit scope: "Formal incident management — severity
  matrices, on-call rotations, post-mortem process — presumes a team and
  a pager. If those exist, they're an organizational practice, not
  something this skill should generate. Say so and move on rather than
  producing a template nobody will use." Score 0 if the output produces
  or recommends an on-call rotation or post-mortem template for this
  project, or hedges toward "it couldn't hurt"; 1 if it explicitly
  declines and says why, without producing the artifacts asked about.
focus: last_message
---

Tests the skill's explicit scope boundary against a fixture built to
directly invite crossing it — the developer asks for exactly the thing
the skill says isn't its job to generate for a solo project.
