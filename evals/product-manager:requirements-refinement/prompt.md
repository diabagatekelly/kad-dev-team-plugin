---
name: product-manager:requirements-refinement
tags: [product-manager, requirements-refinement]
runs: 3
---

A problem framing doc and a scope map both exist for this problem.

# Problem: Manual Personal Finance Tracking

## Constraints
- **Zero cost, permanently.** No paid services, no subscriptions, no
  metered API bills — including for any AI capability.
- **Financial data is the core asset.** Hosting off your own hardware is
  acceptable, but the data must be encrypted in transit and at rest. A
  breach here exposes complete transaction history and account details.
- **Categorization must match the existing scheme.** Correct means "matches
  how it was categorized by hand," not "reasonable." A sample of past
  hand-done accounting is the ground truth.
- **Single user today, not single-user forever.** Use starts personal but
  is expected to extend beyond the household. Assumptions that would be
  expensive to unwind later — one hardcoded identity, shared data with no
  ownership boundary — are ruled out, without building multi-user
  machinery now.

# Scope Map: Manual Personal Finance Tracking (scope-map-001)

## Status
Active

## Steps
1. Transaction retrieval — getting transaction data out of each account and
   into the system, replacing the manual per-account login/lookup step.
2. Transaction categorization — assigning a category to each transaction,
   using the user's own historical categorized data as the basis rather
   than a generic scheme.
3. Budget & spending view — showing actual spend per category against
   budgeted amounts, replacing the manual by-hand comparison.
4. Checking/savings rebalancing — surfacing (and possibly acting on) how
   much surplus should move from checking to savings at month end.

## Out of scope
Protecting the financial data is deliberately not a step — it applies to
every step that touches transactions. It gets reconciled at each step's own
requirements pass.

Step 1 ("Transaction retrieval") is next in line to be worked. No slice
has been cut for it yet, and nobody has confirmed with the user what they
specifically want built for it. Pin down the requirements for step 1.

## Scripted answers

- Who benefits / what they're trying to accomplish: "It's just me, one
  person, tracking my own accounts — not shared with anyone else."
- Priority / trade-off: "I actually want a live connection to my bank,
  even though I know that's the riskier, more expensive option compared
  to just importing a CSV export by hand. The whole point of building
  this for me is not having to manually export and upload files every
  month — if I still have to do that, I haven't really solved my problem."
- Simplest version that still feels like progress: "Just one account to
  start — my main checking account. I have several accounts total but
  don't need all of them connected on day one."
- Alternatives considered: "I looked at just continuing to paste CSV
  exports into a spreadsheet tool, but that's literally what I'm already
  doing by hand — it wouldn't feel like progress at all."
- If asked where the app will run or who can reach it: "I'd host it
  somewhere cheap rather than on my own machine, so I can get to it from
  my phone."
- If asked whether anyone else will ever use it: "Eventually my partner
  probably, but not now."
