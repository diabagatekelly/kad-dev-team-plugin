---
type: llm
criteria: |
  The final requirements doc must contain a section reconciling the problem
  doc's four constraints against THIS step (transaction retrieval). Grade
  three things.

  (1) COVERAGE: all four constraints are addressed — zero cost; financial
  data as core asset / hosting off own hardware / encryption; categorization
  matching the existing scheme; single user today but not forever. Each is
  either applied to this step or explicitly dismissed with a reason. Score 0
  if any of the four is silently absent. The categorization constraint is the
  one that legitimately does NOT bind step 1 (categorization is step 2) — it
  must still be named and dismissed with a stated reason, not omitted.

  (2) CONSEQUENCES, NOT QUOTATIONS: for each constraint that applies, the doc
  must say what it FORCES for this step, not restate the constraint. "Data
  must be encrypted in transit and at rest" copied across is a fail for that
  entry; "the transaction list will be reachable over a network, so something
  has to establish who is asking before it is displayed" is a pass. Score 0
  if the applying constraints are merely restated.

  (3) THE NON-OBVIOUS ONE: the hosting/core-asset constraint must be carried
  through to its actual consequence — that this step's data will be displayed
  by a system reachable over a network, which raises who is allowed to see
  it. Credit any equivalent phrasing (a gate, sign-in, access control, "who
  is asking"). This is the element most likely to be missed, because a step
  named "transaction retrieval" doesn't look like it owns that question.
  Additionally, the single-user constraint must be carried to "nothing here
  may assume one hardcoded identity" rather than being read as a note about
  the future.

  Score 1 only if all three hold.
focus: last_message
---

Tests the Constraints-in-force pass added after a real dogfooding run failed
exactly here. In that run the problem doc contained both the hosting and the
single-user constraints; the requirements doc carried forward only the $0 one
(obviously about connections) and dropped the other two, because for a step
called "getting transactions in" they looked like someone else's problem. The
gap surfaced three stages later at security-requirements, when the only
remaining fixes were re-slicing or growing a slice.

Element 3 is the whole point. Elements 1 and 2 can be satisfied by a
mechanical walk of the list; only element 3 tests whether the persona
actually drew a consequence nobody had drawn.

The scope map in this case deliberately says protecting the data "gets
reconciled at each step's own requirements pass" — the corrected routing.
A persona that reads that and still defers is failing the rule twice.
