---
type: llm
criteria: |
  The output's Steps section must name enough distinct steps to plausibly
  cover the whole problem's scope as described in the task — at minimum,
  something about retrieving/connecting transactions, something about
  categorization, something about budget-vs-actual comparison, and
  something about the savings-transfer decision — rather than naming only
  one narrow piece of it. Score 0 if the map reads like a single slice or
  covers only one capability; 1 if it gives loose visibility into the
  problem's full shape.
focus: last_message
---

Distinguishes a scope map from a slice write-up: the whole point is loose
visibility into the entire problem, not a deep cut into one part of it.
