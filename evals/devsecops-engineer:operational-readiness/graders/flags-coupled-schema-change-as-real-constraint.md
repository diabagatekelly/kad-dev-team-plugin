---
type: llm
criteria: |
  The release renames `transactions.category` to `transactions.category_id`
  via migration, deployed in the same release as code that only
  understands the new column — meaning rolling back the code alone (the
  standard rollback move) would break, since the column the old code
  expects no longer exists. PASS requires the output to identify this
  coupling as a real constraint on rollback, per the skill's explicit
  framing: "What can't be rolled back. Schema and data changes... these
  are the real constraint, and they're what makes a change genuinely
  one-way... A deployment that ships both at once, where one can be
  reversed and the other can't, is the standard way a rollback becomes
  impossible." Credit either naming the coupling explicitly as a rollback
  blocker, or recommending separating the data change from the code
  change (e.g. an expand/contract approach: add the new column, backfill,
  deploy code that tolerates either, then drop the old column later).
  Score 0 if this coupling is never identified as a constraint on
  rollback; 1 if it's named, regardless of which correct resolution is
  recommended.
focus: last_message
---

Tests whether the "real constraint" checks apply on their own terms even
inside an otherwise heavily scaled-down review — this is the rule the
skill says matters "regardless of scale," unlike on-call/monitoring
questions.
