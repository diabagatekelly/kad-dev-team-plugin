# Requirements: scope-map-001 step 1 — Transaction ingestion (requirements-001)

## Status
Active

## User
The user themselves — the person currently logging into each account by
hand to record transactions in Excel.

## What they need
Automatic ingestion of transactions from all of their accounts, so they
stop manually logging into each one to record activity. A live automatic
connection (e.g. Plaid) is the preferred mechanism if it's free at their
usage level. If it isn't free, an acceptable fallback is automatically
grabbing and parsing bank statements sent to their email — the point is
eliminating manual entry, not the specific mechanism.

## Why this, why now
The whole value of this step is removing the manual "log into each account
and record" work. The user is indifferent between the two ingestion
mechanisms as long as one is free and automatic — cost rules out Plaid
before mechanism preference does.

## Confirmed in scope
- All 4 accounts: 3 checking accounts and 1 Amex card.
- Banks and Amex may be treated as separate ingestion paths, since they're
  different institution types (user's own framing, not yet a technical
  decision).
- Seeing all raw transactions from these accounts in one place,
  automatically, even before categorization or budgeting exist — this is
  what "progress" means for this piece.

## Confirmed out, for now
- Categorization and budget/spending view — later scope-map steps, not
  this one.
- Final choice between Plaid and email-statement parsing — contingent on
  verifying whether Plaid is free at the user's usage level, which isn't
  confirmed yet and will be settled once this step is designed/sliced.
