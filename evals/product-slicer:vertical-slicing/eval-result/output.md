Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/agents/product-slicer/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/vertical-slicing/SKILL.md

## Scenario A

You pick the account — you have two checking accounts and care which one
this is. That makes selection part of the thin path.

# Slice 1 (scope-map-001 step 1): Connect one checking account you choose, and see its transactions

## Slice set for this unit

Every slice step 1 currently looks like it needs. Provisional — building
this one is the best information about whether the rest is right.

1. **Connect one checking account you choose, and see its transactions** ←
   this slice.
2. Pull that account again later and see new transactions without old ones
   repeating.
3. See the connection's state, and recover when it fails or expires.
4. Connect a second account and see each account's transactions separately.

## Thin path

You choose which of your two checking accounts to connect, complete the live
connection to it, and see that account's transactions listed in the app —
without logging in to the bank and recording anything by hand.

## Acceptance criteria

> Given I have no account connected
> When I start the connection flow
> Then I can see my checking accounts and choose which one to connect

> Given I have chosen one of my checking accounts
> When the connection completes successfully
> Then that account is shown as connected, identified clearly enough that I
> can tell which of my two accounts it is

> Given a checking account is connected
> When I open the transaction list
> Then I see transactions from that account, each showing its date,
> description, and amount

> Given I chose one checking account and connected it
> When I look at the transaction list
> Then no transactions from my other checking account appear

> Given I start the connection flow
> When the connection does not complete — I cancel it, or the bank refuses
> Then no account is shown as connected, and I am told it didn't connect

- SECURITY — placeholder, to be authored by
  `devsecops-engineer:security-requirements`. This slice connects to a real
  financial institution and displays real transaction data; concrete
  criteria are not mine to write.
- ACCESSIBILITY — placeholder, owned by `accessibility-engineer` once that
  persona exists. Both the account-selection control and the transaction
  list are real UI a person has to operate.

## Explicitly deferred

- **The second checking account, and every other account.** The
  requirements doc confirms one is enough to feel like progress. Slice 4.
- **Repeat pulls and duplicate handling.** This slice connects once and
  lists what comes back. What happens on the second pull — and what makes
  two transactions "the same" — is slice 2, and asserting anything about
  duplicates here would mean asserting an outcome whose matching key nobody
  has named yet.
- **Backfilled history.** Not raised in the requirements doc; how far back
  the first pull reaches is left to slice 2's conversation rather than
  decided silently here.
- **Categorization, budget view, money movement.** Scope-map steps 2
  through 4, confirmed out in the requirements doc.
- **Connection expiry and re-authentication.** Slice 3. Safe to defer only
  because nothing in this slice depends on the connection outliving its
  first use.

## Still open

- **Which institution and connection mechanism.** The requirements doc
  confirms a live connection that's free at this usage level; *how* that
  connection is made is a technology decision for
  `software-architect`, not mine to pick here.
- **What "free at their usage level" is actually bounded by.** Confirmed
  free in the requirements doc, but not what happens if that changes. Worth
  a decision before this ships, and it belongs to `product-manager` rather
  than to slicing.
- **How the two checking accounts are told apart in the UI.** The criteria
  above require you can tell which one is connected; what identifies it —
  nickname, last four digits, institution name — isn't decided here.

## Scenario B

Unchanged from my first response, and not a position I'd soften after the
push: there's no requirements doc for any step of this scope map, so there's
no confirmed WHAT for me to cut.

Deciding what to build first is `product-manager`'s call, made with you.
Cutting a slice now would mean inferring it myself and presenting an
engineering heuristic as your decision. Run
`product-manager:requirements-refinement` on whichever step is next, hand me
the result, and the slice takes minutes.
