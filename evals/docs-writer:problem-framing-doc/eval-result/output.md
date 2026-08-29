Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/problem-framing-doc/SKILL.md

Note: the request already leans toward a solution (web app, direct account pulling, AI categorization). Per the problem-framing-doc skill, that "how" doesn't belong here yet — it's captured below only as constraints on the solution space or pushed to open questions/non-goals, not as decided design.

---

# Problem: Manual Personal Finance Tracking

## The problem
Every month, the user manually: logs into each financial account, records and categorizes every transaction by hand in Excel, checks actual spend against budgeted amounts per category, and transfers surplus funds from checking to savings. Every step — login, entry, categorization, reconciliation, rebalancing — is done by hand, repeated monthly. This consumes a large, recurring amount of time.

## Why now
The time cost of the fully manual process is high enough that the user is willing to invest in building a replacement rather than keep absorbing it.

## Constraints
- The system will hold real transaction and account data — security is a hard requirement given the financial stakes, not a nice-to-have.
- Any AI/ML-assisted categorization must run at no ongoing cost.
- Historical hand-categorized transaction data exists and is available to establish correct categorization — the categorization scheme is the user's own, not a generic one.

## Non-goals
- Not deciding how transactions get retrieved from accounts (aggregator service, direct bank integration, manual export/import, etc.) — later design decision.
- Not deciding whether or how AI is used for categorization, or what bounds "free" — later design decision.
- Not covering investing, tax filing, or bill pay — scope is limited to transaction tracking, budgeting, and checking/savings rebalancing as described, unless the user says otherwise.

## Open questions
- Which institutions/account types need support, and does that constrain how transactions can be retrieved?
- What does "very secure" require concretely — e.g., no third party ever holding credentials, encryption at rest, a specific compliance bar — or is it general best practice?
- How much historical categorized data exists, and in what format/volume?
- Single-user only, or does this need to support shared/household finances?
- Is "free" AI a hard requirement (must never cost money, ever) or a strong preference that can flex later?
- When categorization is ambiguous, is manual review/correction expected, or is full automation assumed?
