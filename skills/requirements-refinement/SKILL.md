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

**Then reconcile the problem doc's constraints — a separate pass from
asking what they want.** The questions above decide the WHAT. This decides
what is already binding on it, and it is the step most likely to be
skipped, because a constraint written at problem-framing time rarely looks
like it belongs to the step in front of you.

Walk the problem doc's Constraints one at a time. For each: does it apply
to this unit? If yes, **say what it forces here.** If no, say why not.
Both answers get written down; a constraint that silently doesn't appear is
indistinguishable from one nobody read.

**Draw the consequence — restating the constraint is not the job.** This is
the whole point of the pass. "The system may be hosted off your own
hardware" is not a note about hosting; it means something reachable over a
network will display this unit's data, which forces a question about who is
allowed to see it. "Single user today, not single-user forever" is not a
note about the future; it means nothing here may assume one hardcoded
identity. A constraint carried forward as a quotation has not been
reconciled.

**A constraint that looks like a later step's problem is the one that gets
dropped.** "Applies to every step" includes this step. If the scope map
sets a constraint aside as cross-cutting, that makes it *yours to apply
here*, not someone else's to handle later — deferring it to whoever designs
or builds this is how it surfaces after slicing, when the cost of acting on
it is highest.

**When a consequence would change the shape of the work, ask.** Same
convention as everything else here. Noticing that a constraint forces a
capability nobody has scoped is a real finding and belongs in this
conversation, not three stages downstream.

This is not deriving the WHAT from the problem doc — that rule above still
holds. Checking a stated constraint against a decided scope is a different
activity from inferring what someone wants.

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

## Constraints in force
Every constraint from the problem doc, one line each: what it forces for
*this* unit, or why it doesn't apply here. Consequences, not quotations.
Note any that turned out to force a capability nothing has scoped yet —
that's a finding for `product-slicer`, not a note.
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
