---
name: user-facing-docs
description: Write user-facing feature documentation — a help page, user guide or FAQ entry — for someone other than an engineer. Use when a feature is done (or about to ship) and members, customers or staff need to understand why and when to use it.
---

# User-Facing Feature Documentation

**Trigger:** a feature is done and someone other than an engineer needs to
understand it.

Write for the user's question, not the engineer's implementation: explain
*why* and *when* to use a feature, not the sequence of clicks. Skip button
colors, exact positions, and screenshots — all three go stale the moment the
UI changes, and none of them answer why a user would bother.

- Lead with the problem the feature solves and who has it.
- Describe what's available (fields, options, behavior) as thoroughly as
  needed — thoroughness isn't the enemy here, prescribing exact clicks is.
- Give high-level access guidance ("found under Settings"), not a numbered
  click-path.
- Note real limitations plainly; don't oversell.

A user doc that would need a rewrite after a button moves has failed at the
one thing it's for.

**State only what you checked.** Every rule, limit and effect on the page
comes from code or a source you actually read. A question you didn't check
(fees, fines, notifications, what another part of the system does) stays
off the page, or becomes "ask the desk", never a confident guess. If you
can't see the interface, don't name its screens or buttons either.

**Write for skimming.** Lead with the point; prefer bullets and headers to
prose; a paragraph is one or two sentences at most. If a sentence wouldn't
change what the reader does next, cut it.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.
