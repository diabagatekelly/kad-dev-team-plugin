# Problem: Manual personal accounting in Excel

## The problem
Every month: log into each account by hand, record and categorize every
transaction, check spend against budget per category, and manually move
money between checking and savings at month-end. Fully manual, in Excel.

## Why now
The process works — it's just extremely time-consuming.

## Constraints
- Must stay free — no paid AI/API tiers, even if AI-assisted categorization
  is used.
- Must be very secure — the app handles real account credentials and real
  money.
- Categorization should reflect the user's own existing categories; a
  sample of prior manual accounting will be provided to ground it, rather
  than inventing a category scheme from scratch.

## Non-goals
None confirmed yet — see open questions.

## Open questions
- Does "pull transactions directly" mean bank-aggregation API, or manual
  CSV import, or both?
- Does categorization need to be AI/ML-driven, or is rule-based matching
  against the provided sample sufficient?
- What triggers a "move money" recommendation — fixed end-of-month rule,
  a threshold, something else?
- Single-user only, or does "very secure" anticipate multi-device/shared
  access?
- Does "must stay free" apply only to the AI piece, or to the entire
  hosting/infra stack?
