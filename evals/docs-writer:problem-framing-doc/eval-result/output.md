Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/problem-framing-doc/SKILL.md

# Problem: Manual, Excel-Based Personal Budgeting

## The problem
Today, all personal accounting runs by hand in Excel:

- Log into each financial account individually.
- Manually record and categorize every transaction.
- Manually check actual spend against the budgeted amount per category.
- Manually decide how much to move from checking to savings at month end.

This repeats every month and is described as extremely time-consuming.

## Why now
The cost is recurring, not a one-time event: every account login, every
transaction entered and categorized by hand, and every end-of-month transfer
decision repeats indefinitely and scales with transaction volume. There's no
external deadline driving this — the case for acting is simply that the
manual cost keeps compounding the longer it continues.

## Constraints
- Must retrieve transactions directly from the user's financial accounts —
  not a manual-entry or manual-import tool.
- Handles real account data and real money-movement decisions, so the
  security bar is high — explicitly called out as a requirement, not a nice-to-have.
- Any AI-assisted categorization must run at no ongoing cost — free, not
  "free trial" or "free tier that later requires payment."
- Categorization must be seeded from the user's own historical categorization
  (a sample of past accounting), not from generic default categories.

## Open questions
- Which financial institutions/accounts need to be in scope, and do they
  support secure, read-only transaction access?
- What does "very secure" mean in concrete, checkable terms? What's the
  acceptable risk bar (e.g., data storage location, encryption, third-party
  data sharing)?
- What counts as "free" for the AI capability — a permanently free tier,
  a self-hosted/open-source model, or no AI at all if nothing free is
  reliable enough?
- What format and size is the historical categorization sample, and how many
  categories does it use?
- Is "move money where" limited to checking → savings, or does it need to
  cover more complex allocation rules across categories/accounts?
- Single user only, or does this need to support a partner/household with
  shared accounts?
