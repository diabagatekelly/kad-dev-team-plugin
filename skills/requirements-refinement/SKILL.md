---
name: requirements-refinement
description: Pin down the concrete user requirement for one scope-map step (or one small, un-mapped problem) by asking the user directly — who benefits, what they actually want, and why — before any slice gets cut. Use once a step is about to be worked and its WHAT hasn't been confirmed with the user yet, before handing off to product-slicer.
---

# Requirements Refinement

**Trigger:** a scope-map step (or a small problem that skipped scope-map
entirely) is next in line to be worked, and nobody has actually asked the
user what they specifically want built for it. The problem doc states the
problem; the scope map names the rough shape; neither decides WHAT to
build — that decision doesn't get made by inference, it gets made by
asking.

**This is a live conversation, not a reading exercise.** Ask the user
directly — don't derive the answer from the problem doc or scope map alone,
even when a plausible answer seems obvious. A wrong assumption here
reshapes the slice that gets built on top of it.

**Ask, merged into one pass:**
- Who specifically benefits from this piece? Reuse what the problem doc or
  scope map already narrowed down; only ask if it's still generic ("the
  user") or genuinely ambiguous for this one piece.
- What are they actually trying to accomplish here, in their own terms?
- Why this, why now — is there a priority or trade-off they care about
  (e.g. "I want live bank sync even though it's riskier, because that's
  the whole point for me")? Don't assume risk-avoidance or smallest-first
  is what they'd choose; ask.
- What's the simplest version that would still feel like real progress to
  them — not the simplest version that's easiest to build.
- Were there alternative approaches they considered or rejected, and why?
  Capture the reason, not just the choice.

**Template:**

```markdown
# Requirements: <step name — "scope-map-NNN step K", or "problem: <short name>" if no scope map> (requirements-001)

## Status
Active | Superseded by requirements-NNN

## User
Who specifically benefits from this piece.

## What they need
The confirmed capability, in plain language — decided with the user
directly for this one piece, not inferred from the problem doc or scope
map alone.

## Why this, why now
Any priority or trade-off the user expressed for this piece specifically.
State it even if it contradicts what a risk-avoidance heuristic would have
picked — that's the point of asking.

## Confirmed in scope
What's definitely part of this piece, as the user confirmed it. Plain
language — not a thin path, not acceptance criteria.

## Confirmed out, for now
What was raised but the user confirmed isn't part of this piece yet, and
why. Narrower than the scope map's whole-problem "Out of scope"; distinct
from `product-slicer`'s own "Explicitly deferred," which covers
slicing-technique deferrals decided later, once a thin path exists.
```

**Never write a thin path, Given/When/Then acceptance criteria, or apply a
slicing technique** (happy-path-first, input variations, reduce scope,
etc.) — those stay `product-slicer`'s and `acceptance-criteria`'s job once
this hands off a decided WHAT. If you catch yourself describing *how* the
capability gets built rather than *what* the user confirmed they want,
stop — that's the next persona's job, not this one's.

**Revise by superseding, never by editing.** Number sequentially, same as
`scope-map` and `adr`. If a later slice or a design conversation reveals
the confirmed WHAT was wrong, write a new numbered version and mark the
old one `Superseded by requirements-NNN` — don't edit an Active one in
place.
