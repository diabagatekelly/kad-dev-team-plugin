---
name: pr-writeup
description: Write a PR description for a completed change that's ready for review. Use when code already exists and needs to be described for a reviewer, distinct from filing not-yet-built work (see user-story-writeup).
---

# PR Description

**Trigger:** a change already exists and is ready for review. This
describes work that already happened; if the work hasn't started yet and
needs to become a trackable item first, that's `user-story-writeup`, not
this.

Explain the change in plain language a reviewer can follow top to bottom
with no cross-referencing anything else — what changed, why, and what a
reviewer should pay attention to.

- Keep ticket/issue IDs out of the narrative — put them on a short trailing
  reference line (e.g. "Tracked under PROJ-123") instead of weaving them
  into sentences.
- **If there's no ticket this PR references and none exists yet, ask**
  whether to file one (which system) or leave the PR self-contained —
  don't silently assume either answer.
- If AI materially produced the change, say so accurately and keep it
  current: name the specific model/tool and its role (plan, implement,
  review), not just "AI." Update the note when the tooling or role
  changes — a stale provenance note is a lie by omission.
