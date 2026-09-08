---
type: llm
criteria: |
  Scenario A's final slice write-up must name the whole provisional slice
  SET for this unit — more than just the slice being written up — as short
  one-line entries, with the current slice identifiable among them. The set
  must be marked or described as provisional/expected to change. Crucially,
  the other slices must stay one-liners: score 0 if any slice other than the
  current one is given acceptance criteria, a thin path, or its own detailed
  write-up. Also score 0 if no set is named at all, or if it is presented as
  a fixed plan rather than a provisional list. Score 1 if the set is present,
  provisional, and only the first slice is specified in full.
focus: last_message
---

Covers the "name the whole set, specify only the first" rule. Two distinct
failure modes, in opposite directions: omitting the set entirely (a slice cut
in isolation can't be checked against "is this actually the thinnest first
step"), and over-specifying it into a backlog with criteria for slices that
building the first one is about to invalidate. Both are failures; the grader
has to catch each.
