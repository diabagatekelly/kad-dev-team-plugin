Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/scope-map/SKILL.md

# Scope Map: Manual, Excel-Based Personal Budgeting (scope-map-001)

## Status
Active

## Steps
1. Connect & retrieve transactions — pull transactions directly from the user's financial accounts via a read-only connection, replacing manual login-and-record.
2. Categorize transactions — categorize retrieved transactions, seeded from the user's own historical categorization sample.
3. Track budget vs. actual — compare categorized spend against the budgeted amount per category.
4. Decide the savings transfer — surface how much to move from checking to savings (or across other allocations) at month end, based on the budget-vs-actual picture.

## Sequencing notes
Each step depends on data the previous one produces: categorization has nothing to categorize until transactions are retrieved, budget comparison has nothing to compare until spend is categorized, and the transfer decision has nothing to act on until spend is measured against budget. This dependency chain is why the order isn't arbitrary, even though nothing here designs how any step gets built.
