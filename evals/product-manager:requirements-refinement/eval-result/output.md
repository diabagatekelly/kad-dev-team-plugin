# Requirements: scope-map-001 step 1 (requirements-001)

## Status
Active

## User
A single individual tracking their own financial accounts — no shared or
household access needed for this piece.

## What they need
A live connection to their primary checking account that pulls
transactions in automatically, so they no longer have to manually export
and upload data from their bank. Starting with one account is enough;
connecting every account isn't required yet.

## Why this, why now
The user explicitly wants a live bank connection over a simpler CSV-import
approach, even knowing it's the riskier and more expensive option
technically. For them, the entire point of building this is eliminating
the manual export/upload step — if they still have to manually pull a file
from their bank every month, the core problem isn't actually solved, no
matter how much safer or cheaper that approach would be to build first.
They already considered continuing to manually paste CSV exports into a
tool and rejected it for the same reason: it's just a restatement of the
manual process they're trying to get away from, not real progress.

## Confirmed in scope
- A live, read-only connection to one financial account (the user's main
  checking account).
- Transactions from that one account retrieved automatically, without a
  manual export/upload step.

## Confirmed out, for now
- Connecting additional accounts beyond the first — the user confirmed one
  account is enough to feel like real progress; more can follow later.
- Any shared/household access model — this is single-user only for this
  piece.
- CSV import as an approach — considered and explicitly rejected by the
  user, not merely deprioritized; it doesn't solve their actual problem.
