---
type: llm
criteria: |
  For each of the thirteen directories, the output must name exactly one next
  action (one persona/skill to route to, or one question to ask) — never a
  multi-step plan that chains through several stages at once (e.g. "route to
  product-manager, then once that's done route to product-slicer, then file
  it"). It's fine to mention what a later stage might look like in passing
  (Directory K explicitly should name tdd-coach as the reason it's stopping),
  but the *stated next action* for each directory must be singular, and
  Directory K's next action must be "stop," not a proposal to advance.
  Directories L and M each have exactly one next action too — a single
  backward route — not a backward step plus a plan for resuming forward.
  Score 0 if any directory's answer proposes more than one routed step as
  "what happens next"; 1 if all thirteen stay single-step (including K
  correctly having no next step at all).
focus: last_message
---

Tests the "route to exactly one next stage, then stop" rule across the full
pipeline. Updated twice: the terminal-directory clause moved from F to K when
the terminal row moved, and directories L and M were added, where the
temptation is to describe the whole round trip ("go back to product-slicer,
then come back here") instead of a single backward step.
