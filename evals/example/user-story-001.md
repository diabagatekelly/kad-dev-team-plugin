# View raw transactions from all accounts via Plaid

As the user who currently logs into each account by hand to record
transactions in Excel, I want to connect my accounts (3 checking accounts
and my Amex card) via Plaid, so I can see all of their transactions listed
together in one place automatically — without manually logging into each
account to record them. This is the first piece of replacing manual
Excel-based accounting; categorization and budgeting build on top of this
later and are not part of this issue.

## Acceptance criteria

- Given the user has not yet connected any accounts via Plaid, when they
  open the transaction view, then they see a prompt to connect accounts
  via Plaid, not a transaction list or an error.
- Given the user has connected at least one account via Plaid, when the
  system fetches transactions for that account, then it displays that
  account's raw transactions in the list.
- Given the user has connected multiple accounts via Plaid (checking
  accounts and Amex card), when they open the transaction view, then they
  see all connected accounts' raw transactions together in one place, not
  split across separate per-account views.
- Given the user has connected an account via Plaid but it has no
  transactions yet (e.g. a brand-new account), when the system fetches
  transactions for it, then it shows an explicit "no transactions yet"
  state, not an error and not something indistinguishable from "not
  connected."
- Given a connected account's Plaid connection enters an error state (e.g.
  needs re-authentication, or Plaid returns an error), when the system
  fetches transactions for that account, then it surfaces a clear notice
  that the connection needs attention, rather than silently showing no
  transactions or stale data.
- Given this flow touches bank-credential-based account linking and real
  financial transaction data, security criteria (not yet authored — needs
  security-engineer) must be met.
- Given this flow includes user-facing UI (Plaid Link connect flow,
  no-transactions state, connection-error notice, transaction list),
  accessibility criteria (not yet authored — needs accessibility-engineer)
  must be met.

## Out of scope for this issue
- Email-statement parsing (not needed — Plaid is confirmed free at this
  usage volume).
- Recurring/scheduled syncing and duplicate detection across repeated
  fetches (this is a fetch-on-demand view, not an ongoing sync).
- Categorization and budget/spending view (later work).

---
Derived from: `evals/example/slice-001.md` (scope-map-001 step 1)
