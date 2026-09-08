Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/agents/docs-writer/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/scope-map/SKILL.md

# Scope Map: Replacing manual Excel budgeting (scope-map-001)

## Status
Active

## Steps
1. Getting transactions in — obtain transaction records directly from the
   user's financial accounts, read-only, replacing the per-account login and
   hand-recording step.
2. Existing categories and budgets — capture the category scheme, the
   per-category budgeted amounts, and the sample of past hand-categorized
   accounting that currently live in the spreadsheet.
3. Categorizing transactions — assign each retrieved transaction a category
   consistent with how it would have been categorized by hand.
4. Correcting a category — change a category that came out wrong, and have
   that correction hold rather than being re-fixed every month.
5. Budget vs. actual — show spending per category against that category's
   budgeted amount for a given month.
6. What to move where — surface the month-end surplus and the
   checking-to-savings transfer it implies.

## Sequencing notes
Step 1 is first because it's the step most likely to reshape the others. The
problem doc's open question about which institutions support secure,
read-only access resolves here, and the answer changes what steps 3 through
6 are working with and how often.

Steps 2 and 3 are separate because the historical sample is an input the
system needs regardless of how categorization is eventually approached, and
the problem doc rules that approach out of scope for now.

## Out of scope
Executing transfers is not a step. Step 6 reports what should move; the move
itself is a bank-side function the problem doc excludes.

Multi-user and household-shared access, bookkeeping/tax/business features,
and choosing the categorization approach or security architecture are all
excluded by the problem doc's own non-goals.

**Two constraints are cross-cutting rather than steps of their own**, and
naming them here is not the same as deferring them:

- **The security bar** applies to every step that touches account data,
  starting with step 1.
- **The zero-ongoing-cost constraint on AI categorization** applies wherever
  that capability is used.

Both get reconciled at **each step's own `requirements-refinement` pass**,
against that step's confirmed scope, before anything is sliced. They are not
deferred to per-slice design — a whole-problem constraint pushed past the
point where scope is decided resurfaces when the only fixes left are
re-slicing or growing a slice.
