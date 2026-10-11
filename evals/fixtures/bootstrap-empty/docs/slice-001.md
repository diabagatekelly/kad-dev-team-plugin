# Slice 1 (scope-map-001 step 1): Connect one checking account and see its transactions

## Thin path
You choose one of your checking accounts, connect it through a
bank-aggregation vendor, and see that account's recent transactions listed
in the app.

## Acceptance criteria (abridged)
- Given I choose an account and the connection succeeds, that account shows
  as connected and I can tell which one it is.
- Given a connected account, when I open the transaction list, I see its
  transactions with date, description and amount.
- Given the connection fails, no account shows as connected and I am told.

Transactions are shown for the current session only. Nothing in this slice
requires them to still be there after a restart — re-pulling on next use is
acceptable and expected.
