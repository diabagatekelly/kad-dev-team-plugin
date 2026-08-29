---
name: user-facing-docs
description: Write user-facing feature documentation for someone other than an engineer. Use when a feature is done and a non-engineer needs to understand why and when to use it.
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
