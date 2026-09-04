# Requirements: scope-map-001 step 1 (requirements-001)

## Status
Active

## User
The user themself — a solo individual managing their own personal finances,
not a multi-user product.

## What they need
Automatic retrieval of transactions from a single financial account via a
live bank connection, so transactions appear without any manual login and
copy step.

## Why this, why now
The user picked a live bank connection over a simpler manual CSV import,
even though the problem doc's security constraint makes a live connection
the riskier piece to build correctly — because their bar for real progress
on this step is transactions appearing on their own, and a CSV import would
still require manually downloading and uploading a file each time, which
doesn't clear that bar. They chose to scope this step to one account rather
than all accounts at once, so the live-sync mechanism gets proven out before
expanding.

## Confirmed in scope
- A live connection to one financial account (not all accounts yet)
- Automatic retrieval of that account's transactions, with no manual entry
- Done bar: transactions show up on their own, even as a raw, unsorted list

## Confirmed out, for now
- Connecting additional accounts (savings, credit cards, etc.) — deferred
  until the single-account live sync is proven out
- Manual CSV/file import as a fallback or alternative — explicitly not
  wanted; it wouldn't clear the user's bar for real progress
- Categorizing, organizing, or sorting the retrieved transactions — that's
  scope-map-001 step 2, not this piece
