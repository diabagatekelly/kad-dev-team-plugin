# Slice 1 (scope-map-001 step 1): Connect one account via live bank sync and view its recent transactions

## Thin path
The user completes a live bank connection for one financial account (the
first account the login returns, no picker) and sees that account's
transactions from the last 30 days appear automatically, with no manual
entry.

## Acceptance criteria

Given the user has not yet connected a financial account
When they complete a live bank connection through the aggregator
Then their account's transactions from the last 30 days appear in the
transaction list, with no transaction entered manually

Given the user attempts a live bank connection
When the bank login fails (e.g. wrong credentials)
Then no account is connected, the transaction list stays empty, and the
user sees a message explaining the connection failed

Given the user's connected account has no transactions in the last 30 days
When the connection completes
Then the transaction list is shown empty, not as an error

Given the user already has a connected account with transactions already
retrieved
When a sync runs again and returns the same transactions
Then no transaction (matched on the bank's own transaction ID) appears more
than once in the list

- [SECURITY — placeholder, owned by `security-engineer` once that persona
  exists]: bank credentials and connection tokens are handled securely
  end to end. Concrete criteria not yet defined.
- [ACCESSIBILITY — placeholder, owned by `accessibility-engineer` once that
  persona exists]: the connection flow and transaction list are usable via
  assistive technology. Concrete criteria not yet defined.

## Explicitly deferred
- Connecting additional accounts (savings, credit cards, etc.) — per
  requirements-001, this slice proves the one-account mechanism first.
- Manual CSV/file import — per requirements-001, live sync is what the user
  wants; CSV isn't being built as a fallback.
- Categorizing, organizing, or sorting the transactions — that's
  scope-map-001 step 2, not this slice.
- Picking which account to connect, when a login exposes more than one —
  this session's answer confirmed the first account only; no picker UI in
  this slice.
- Transaction history beyond the last 30 days — a recent window was chosen
  to keep this slice small; the exact 30-day figure is a placeholder
  default, not a firm requirement (see Still open).

## Still open
- Which bank-aggregation service/vendor to use — a technology decision for
  `software-architect`, not decided here.
- Concrete security requirements for credential/token handling — for
  `security-engineer` to fill in once that persona exists.
- Concrete accessibility requirements for the connection and transaction-
  list UI — for `accessibility-engineer` to fill in once that persona
  exists.
- Whether 30 days is the right default history window, or should be
  shorter/longer — flagged as a placeholder choice, not a confirmed
  requirement.
