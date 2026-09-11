Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/scope-map/SKILL.md

```markdown
# Scope Map: Manual, Excel-Based Personal Budgeting (scope-map-001)

## Status
Active

## Steps
1. Transaction retrieval — connecting to the user's financial accounts and retrieving their transactions directly, not via manual entry or import.
2. Categorization — assigning a category to each retrieved transaction, seeded from the user's own historical categorization sample rather than generic default categories.
3. Budget & spending view — comparing actual spend against the budgeted amount per category, based on the categorized transactions.
4. Checking/savings rebalancing — surfacing how much surplus to move from checking to savings, based on the budget-vs-actual picture.

## Out of scope
Two constraints from the problem doc apply to every step rather than being one, so they aren't steps of their own:
- The high security bar on real account and money-movement data.
- Running at no ongoing cost — the problem doc's sentence names AI-assisted categorization specifically, but the underlying concern (this project must not accrue a recurring bill) isn't specific to that one step.

Both are addressed at each step's own requirements-refinement pass, against that step's confirmed scope, not deferred to design.
```
</content>
