---
type: llm
criteria: |
  For each of the eight directories, the output must name exactly one next
  action (one persona/skill to route to, or one question to ask) — never a
  multi-step plan that chains through several stages at once (e.g. "route
  to product-manager, then once that's done route to product-slicer, then
  file it"). It's fine to mention what a later stage might look like in
  passing (Directory F explicitly should name tdd-coach as the reason it's
  stopping), but the *stated next action* for each directory must be
  singular, and Directory F's next action must be "stop," not a proposal
  to advance. Score 0 if any directory's answer proposes more than one
  routed step as "what happens next"; 1 if all eight stay single-step
  (including F correctly having no next step at all).
focus: last_message
---

Tests the "route to exactly one next stage, then stop" rule across the
now-longer pipeline — still must hold with four planning personas instead
of three.
