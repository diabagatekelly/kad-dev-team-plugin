Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/agents/product-manager/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/requirements-refinement/SKILL.md

# Requirements: scope-map-001 step 1 — Transaction retrieval (requirements-001)

## Status
Active

## User
You, one person, tracking your own accounts. Not shared with anyone else —
no partner, no household, no second person needing access to the same data.

## What they need

Transactions from your main checking account arrive in the system over a
live bank connection, without you logging in to record them by hand.

One account is the whole of it for now. You have several accounts; this
piece connects one.

## Why this, why now

**You want the live bank connection specifically, and you named the
trade-off yourself.** You know it's the riskier and more expensive option
compared with importing a CSV export by hand — and you chose it anyway,
because the manual export-and-upload step is the exact thing you're trying
to escape. In your words: if you still have to do that every month, you
haven't really solved your problem.

That reasoning is the point of this document. A risk-avoidance heuristic
would have picked CSV import here and been wrong about what you're buying.

**The alternative you rejected, and why:** continuing to paste CSV exports
into a spreadsheet tool. You dismissed it as literally what you already do
by hand — it wouldn't feel like progress at all.

## Confirmed in scope

- One account — your main checking account.
- A live connection to it, rather than a manual export/import step.
- That account's transactions arriving in the system without manual entry.

## Confirmed out, for now

- **Your other accounts.** You have several; you confirmed you don't need
  them connected on day one.
- **Manual CSV import**, as either the primary path or a fallback. Raised
  and explicitly rejected — it recreates the effort this piece exists to
  remove.
- **Categorization, budget view, and money movement.** Scope-map steps 2
  through 4, not this piece.

## Constraints in force

**This pass could not be completed, and that is a finding rather than an
omission.** I was given the scope map but not the problem framing doc, so
its Constraints section was not available to reconcile against this step.

What I know is outstanding, from the scope map's own framing:

- Any constraint on **how transactions may be retrieved** binds this step
  directly — it is the step that does the retrieving.
- Any constraint on **security or handling of real account data** binds this
  step, because this is the first step where that data enters the system at
  all. Whatever it forces here needs saying before a slice is cut, not after.
- Any constraint on **cost** may bind, since a live bank connection is the
  most likely place in this problem for a recurring charge to appear.

Each of those needs an explicit answer — what it forces for this step, or
why it doesn't apply. Until the problem doc is available, treat this section
as unfinished and this document as not yet safe to slice against: a
constraint discovered after slicing costs a re-slice, which is the failure
this pass exists to prevent.
