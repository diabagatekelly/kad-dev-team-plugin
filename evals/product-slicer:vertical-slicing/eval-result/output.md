## Scenario A: Slice 1

# Slice 1 (scope-map-001 step 1): Connect a chosen checking account and view its transactions

## Thin path
The user picks which of their checking accounts to connect (they have
more than one and care which), connects it via a live bank connection,
and sees that account's transactions listed. No categorization, budget
view, or money movement yet — just the connect-and-view step.

## Acceptance criteria

Given the user has not yet connected an account,
When they start the connection flow,
Then they're shown their checking accounts to choose from and pick one to
connect — not an automatic connection to whichever account the flow
happens to see first.

Given the user has selected and connected one checking account,
When the system fetches transactions for it,
Then it displays that account's transactions in a list.

Given the user is connecting an account,
When they decline or cancel before the connection completes,
Then no account is connected and nothing is shown as connected.

Given the user's selected account has no transactions yet,
When the system fetches transactions for it,
Then it shows an explicit "no transactions yet" state, not an error and
not something indistinguishable from "not connected."

Given the connection enters an error state (e.g. needs re-authentication),
When the system fetches transactions for that account,
Then it surfaces a clear notice that the connection needs attention,
rather than silently showing no transactions or stale data.

Given this slice's flow touches bank-credential-based account linking and
real transaction data,
When security-engineer defines the security criteria for it,
Then those criteria are met. [Placeholder — not authored here.]

Given this slice's flow includes user-facing UI (account picker, connect
flow, no-transactions state, error notice, transaction list),
When accessibility-engineer defines the accessibility criteria for it,
Then those criteria are met. [Placeholder — not authored here.]

## Explicitly deferred
- **Connecting a second account** — the requirements doc confirms one
  account is enough to feel like progress for this piece; picking which
  one is in scope, connecting more than one is not.
- **Categorization, budget view, money movement** — later scope-map
  steps, out of scope per requirements-001.
- **CSV import as a fallback mechanism** — not needed; the live connection
  is already confirmed free at the user's usage level per requirements-001.

## Still open
- Exact account-picker UI shape (list, search, etc.) — a design/architecture
  call, not this persona's.
- Concrete security and accessibility criteria — owned by
  security-engineer and accessibility-engineer respectively.

---

## Scenario B: unchanged

I still can't decide what to build first here without a `product-manager`
requirements doc — that hasn't changed. I'm not producing a slice for this
scenario; the correct next step is a hand-off to `product-manager`, not a
slice write-up.
