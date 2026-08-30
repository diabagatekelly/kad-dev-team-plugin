# Slice 1 (scope-map-001 step 1): View raw transactions from all accounts via Plaid

## Thin path
The user connects their accounts (3 checking accounts, 1 Amex card) via
Plaid. The system pulls each connected account's transactions and the user
sees all of them listed together in one place — no categorization or
budgeting yet.

## Acceptance criteria

Given the user has not yet connected any accounts via Plaid,
When they open the transaction view,
Then they see a prompt to connect accounts via Plaid, not a transaction
list or an error.

Given the user has connected at least one account via Plaid,
When the system fetches transactions for that account,
Then it displays that account's raw transactions in the list.

Given the user has connected multiple accounts via Plaid (their checking
accounts and Amex card),
When they open the transaction view,
Then they see all connected accounts' raw transactions together in one
place, not split across separate per-account views.

Given the user has connected an account via Plaid but it has no
transactions yet (e.g. a brand-new account),
When the system fetches transactions for it,
Then it shows an explicit "no transactions yet" state, not an error and
not something indistinguishable from "not connected."

Given a connected account's Plaid connection enters an error state (e.g.
needs re-authentication, or Plaid returns an error),
When the system fetches transactions for that account,
Then it surfaces a clear notice that the connection needs attention,
rather than silently showing no transactions or stale data.

Given this slice's flow touches bank-credential-based account linking and
real financial transaction data,
When security-engineer defines the security criteria for it,
Then those criteria are met. [Placeholder — not authored here; this
persona doesn't have that expertise. Note: this now carries higher stakes
than the email-parsing approach it replaced, since it involves
bank-credential-based linking directly.]

Given this slice's flow includes user-facing UI (Plaid Link connect flow,
no-transactions state, connection-error notice, transaction list),
When accessibility-engineer defines the accessibility criteria for it,
Then those criteria are met. [Placeholder — not authored here; this
persona doesn't have that expertise.]

## Explicitly deferred
- **Email-statement parsing** — no longer this slice's mechanism now that
  Plaid is confirmed free at this usage volume (Trial plan: 10 free
  Production Items, no minimum spend on Pay-as-you-go beyond that). Could
  still be revisited as a fallback later if that ever changes, but isn't
  needed for slice 1.
- **Recurring/scheduled transaction syncing and duplicate detection across
  repeated fetches** — deferred. Slice 1 is a fetch-on-demand view, not an
  ongoing sync, so there's no repeat action yet to de-duplicate against.
- **Categorization and budget/spending view** — out of scope per
  requirements-001; later scope-map steps.

## Still open
- Whether the 3 checking accounts are at the same institution or different
  ones. Doesn't block slice 1 — Plaid Link is repeatable per institution
  either way — but affects how many separate connection steps the user
  goes through.
- Exact Plaid product/plan details to request (Transactions product usage
  against the 10-Item Trial cap, what happens if that cap is ever
  approached) — an architecture/technology decision, not this persona's
  call.
- The concrete re-fetch/de-duplication key — needed once recurring syncing
  is scoped, not before.
