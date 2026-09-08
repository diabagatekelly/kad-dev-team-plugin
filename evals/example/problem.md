# Problem: Replace by-hand Excel accounting

## The problem

Personal accounting is done entirely by hand in Excel today. The current
process, per cycle:

1. Log into each financial account separately.
2. Read transactions and retype them into a spreadsheet.
3. Assign a spending category to every transaction by hand.
4. Compare each category's total against its budgeted amount.
5. Decide at month end whether anything can be saved, and move money from
   checking to savings manually.

The cost is time — hours per month, every month, growing with the number of
accounts and transactions. It is also silently error-prone: a mistyped
amount or a miscategorized row makes a budget look fine when it isn't, and
nothing catches it.

The system is expected to *say* what money needs to move where. Whether it
also moves it is an open question, not a settled exclusion.

## Why now

- The manual process has no ceiling — it recurs monthly and gets worse as
  accounts accumulate.
- The categorization rules currently exist only in the user's head and in
  past spreadsheets. A sample of that past accounting is available now,
  which is what makes automatic categorization tractable rather than
  guesswork.
- Errors compound quietly. Every month of hand entry is another month of
  budget decisions made on numbers nobody verified.

## Constraints

| Constraint | Why it's hard |
|---|---|
| **Zero recurring cost, whole system** | Not just AI — hosting, bank data access, and any model calls must be free. Anything with a subscription or per-call fee is out. |
| **Transactions arrive automatically** | Pulled from the accounts directly. Manual CSV export by hand is not an acceptable end state. |
| **Reachable as a hosted web app from any device** | Implies internet-exposed, which raises the security bar rather than lowering it. |
| **Handles real money data; security bar is high** | Account data and any credentials involved must be protected to a standard defensible for finances, not "reasonable for a side project." |
| **Categorization matches the existing scheme** | Correctness is measured against the user's own past categorizations, not against a generic category set. |

These constraints are in tension with each other. Free, automatic,
internet-exposed, and highly secure bank data access is a combination with
no obvious off-the-shelf answer — free-tier bank aggregation at consumer
scale is scarce, and exposing a service to the internet is exactly what
makes credential handling expensive to do safely. Resolving that tension is
the first open question below, not a detail to defer.

## Open questions

- **If no free path to automatic bank data exists, which constraint
  gives** — zero cost, automatic pull, or hosted-anywhere access? This
  determines whether the problem as stated is solvable at all.
- **Which accounts and institutions must be covered**, and how many? One
  bank behaves very differently from six across different providers.
- **Does the system execute the checking→savings transfer**, or only report
  that it should happen?
- **What does "free AI" mean concretely** — a model running on the host, a
  free API tier, or no AI at all if a rules-based approach learned from the
  sample is sufficient?
- **Where do budget amounts come from**, and how often do they change?
- **Is historical Excel data imported**, or is the past accounting only a
  training sample for categorization?
- **What happens to a transaction the system can't confidently
  categorize** — is a review queue acceptable, or does that reintroduce the
  manual work being eliminated?
- **What is the tolerance for the system being wrong?** A wrong category is
  recoverable; a wrong balance driving a real transfer is not.
