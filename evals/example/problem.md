# Problem: Manual Excel-Based Personal Accounting

## The problem
Every accounting cycle, the user manually logs into each financial account,
records every transaction, categorizes it by hand, and checks it against a
budget for that category — all in Excel. At the end of the period, they also
manually work out how much money (if any) to move from checking to savings.
None of this is automated: no transactions are pulled automatically, no
categorization is assisted, and no budget-vs-actual view exists outside the
spreadsheet the user maintains themselves. This is extremely time-consuming.

## Why now
The time cost recurs every accounting cycle rather than being a one-time
expense, so it keeps compounding the longer it goes unaddressed.

## Constraints
- Any AI-assisted categorization must remain free to run — no ongoing paid
  API/service cost for that capability.
- The solution handles direct access to financial accounts and money-movement
  decisions, so it must be very secure.

## Non-goals
Not yet defined — see open questions below.

## Open questions
- Which accounts/institutions are in scope (checking, savings, credit cards,
  investments, etc.), and are all of them included from the start?
- What does "very secure" mean concretely here — specific requirements for
  auth, data storage, third-party data sharing, or compliance expectations?
- What does "free" mean for AI-assisted categorization — zero paid API calls
  ever, or a free tier that comfortably covers expected usage?
- Does moving money between checking and savings need to happen automatically,
  or is a recommendation ("move $X to savings") sufficient?
- What's explicitly out of scope for a first version — e.g. investment
  tracking, bill pay, tax prep, multi-user/shared accounts?
