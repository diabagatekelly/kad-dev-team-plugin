# Requirements: scope-map-001 step 1 — Account connection (requirements-001)

## Status

Active

## User

The account holder doing the accounting today — one person now, but not
permanently. A partner may use it later.

## What they need

An automatic connection to **one** financial institution the user names,
retrieving that institution's transactions so they appear in the app
without anyone logging into the bank and retyping them.

One institution, connected automatically, is the bar. Not a broader
connection, and not a file the user downloads themselves.

## Why this, why now

- **One account first, deliberately.** The user chose seeing a single real
  account's transactions over broader coverage, because the unsolved
  question is whether a free automatic connection is possible at all —
  breadth is worthless until that's answered.
- **Cost outranks coverage.** Asked which constraint gives if a free
  automatic connection doesn't exist for their banks, the user chose to
  keep it free and connect only to whatever institutions can be reached for
  free, accepting that the rest may stay manual indefinitely. Coverage is
  the negotiable thing here; money is not.
- Note the consequence: this means **which institution goes first is not
  purely the user's preference.** The user names it, but only from among
  institutions with a free path. If their most important account has no
  free route, this step delivers a less important account or nothing.

## Confirmed in scope

- Automatic retrieval of transactions from one named institution.
- Those transactions being visible to the user in the app.
- Repeat retrieval that keeps working — a connection that reads once and
  breaks doesn't replace the manual chore.

## Confirmed out, for now

- **Other institutions.** Deferred by the user's own choice of one-account
  scope; breadth is a later pass, and may never cover institutions with no
  free route.
- **Any categorization of what's retrieved.** That's step 3. Step 1's
  transactions arrive uncategorized.
- **Budgets, budget comparison, transfer recommendations.** Steps 5–7.
- **Anything that moves money.** Not merely unscoped — this step's
  connection should not be capable of it. Executing transfers isn't
  confirmed as in scope for the problem at all, and a retrieval connection
  that could also move funds enlarges what a compromise costs for no
  benefit this step needs.

## Constraints in force

| Constraint | What it forces here |
|---|---|
| **Zero recurring cost, whole system** | Binding, and it decides institution selection rather than merely capping a bill. The set of connectable institutions is whatever is reachable for free — the user confirmed this ordering explicitly. |
| **Transactions arrive automatically** | Binding and not satisfiable by a fallback. A hand-downloaded file does not complete this step; the whole point of going first is to find out whether automatic-and-free exists. |
| **Reachable as a hosted web app from any device** | Binding, and it forces a capability nothing has scoped — see the finding below. Something on a network will display this account's transactions, so "who is allowed to see this" must be answered inside this step, not after it. |
| **Handles real money data; security bar high** | Binding hardest here of any step. Whatever proves the user's identity to their bank is the highest-value thing the system will ever hold, and it exists only because of this step. Every later step handles data derived from this one; only this step touches what grants access to the money itself. |
| **Single user today, not forever** | Binding. The user expects a partner may use this later, so nothing in this step may assume one hardcoded identity — retrieved transactions need an owner even while there is exactly one owner. |
| **Categorization matches the user's existing scheme** | Does not apply — nothing is categorized in this step. One consequence carries over anyway: what gets retrieved has to carry enough detail for step 3 to categorize from later. Retrieval that returns only dates and amounts would pass this step and make step 3 unbuildable. |

## Finding for product-slicer

**Access control is forced by this step and is not a step on the scope
map.** The hosted-anywhere constraint means this step puts real financial
data on a network-reachable surface. There is no version of this step that
is complete and also leaves "who can see this" unanswered.

The scope map anticipated this — it set data protection aside as
cross-cutting and routed it to each step's requirements pass, which is
here. So this is not a gap in the map. It is a fact about this step's true
size that slicing has to absorb: the first slice cut from step 1 carries
both a bank connection and an answer to who's allowed to view what it
returns.
