# Scope Map: Replace by-hand Excel accounting (scope-map-001)

## Status

Active

## Steps

1. **Account connection** — establish an automatic connection to the user's
   financial accounts and retrieve transactions from them at no recurring
   cost.
2. **Transaction record** — keep a durable record of retrieved transactions
   across cycles, so a month's numbers don't have to be rebuilt each time.
3. **Categorization** — assign each retrieved transaction a spending
   category matching the user's own scheme, derived from a sample of their
   past accounting.
4. **Correction and learning** — let the user fix a wrong or missing
   category on a categorized transaction, and carry that correction forward
   into future categorization.
5. **Budget definition** — capture the budgeted amount for each spending
   category and how it changes over time.
6. **Budget-vs-actual view** — show categorized spending against each
   category's budget for the current period.
7. **Transfer recommendation** — surface how much money should move between
   accounts, based on the budget-vs-actual picture.

## Sequencing notes

The order mirrors the manual process being replaced, which is why most of it
is self-evident. Two things aren't:

- **Step 1 is first because it's where the problem doc's central tension
  gets resolved.** Free, automatic, internet-exposed account access has no
  obvious answer. If it turns out to be impossible, the constraint that
  gives changes the shape of every step after it — so it isn't safe to
  treat later steps as settled until this one has been worked.
- **Step 5 doesn't depend on steps 1–4.** Budget amounts come from the
  user, not from retrieved data, so this step is available to work early if
  step 1 stalls.

## Out of scope

These steps cover *reporting* what money should move, not moving it.
Whether actually executing the transfer belongs in this problem is still an
open question in the problem doc — it is not being asserted as excluded
here, only noted as absent from the current steps so its absence doesn't
read as an oversight.

## Cross-cutting constraints

These apply to every step and would be misleading as steps of their own.
Each is reconciled against a step's confirmed scope during **that step's own
`requirements-refinement` pass**, before anything is sliced — not deferred
to design or review:

- **Zero recurring cost across the whole system** — hosting, account data
  access, and any model usage.
- **Protection of financial data and any credentials involved**, at a
  standard defensible for money, given the system is internet-exposed by
  the hosted-anywhere constraint.
