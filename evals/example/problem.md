# Problem: Manual Excel-Based Personal Accounting

## The problem
Each month, the user logs into every financial account individually,
transcribes each transaction into Excel by hand, assigns it a spending
category, and checks the running total against that category's budget. At
month end, they manually calculate whatever surplus exists and decide how
much to move from checking into savings. Every step — pulling transactions,
categorizing them, checking budget fit, and deciding on the checking-to-
savings transfer — is done by hand, with no automation anywhere in the
process. This consumes a large amount of time every month.

## Why now
The cost isn't a one-time fix — it's a recurring monthly tax on the user's
time that continues indefinitely as long as the process stays manual.

## Constraints
- If an AI capability is used for categorization, it must remain free to
  operate — no ongoing paid usage cost.
- The system connects to and moves money between real financial accounts, so
  it must be built and operated securely.

## Open questions
- Which accounts and institutions need to be connected, and are all of them
  in scope from day one?
- What counts as "very secure" here in concrete terms — credential handling,
  data storage/encryption, third-party access, audit logging?
- The user can supply a sample of their own historically-categorized
  transactions — how should that sample be used to categorize new
  transactions (train a model, derive rules, something else)?
- What does "free" bound to, exactly — no AI cost ever, or a free tier
  that's expected to cover ongoing usage comfortably?
- Should checking-to-savings transfers execute automatically, or should the
  system only surface a recommendation for the user to act on?
- What's out of scope for a first version — e.g. investment accounts, bill
  pay, tax prep, multi-user access?
