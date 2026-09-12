---
type: llm
criteria: |
  The status block's title ("Your changes couldn't be saved") is marked
  up as `<strong>`, not a heading element, and it's the only titled
  content block below the page's one `<h1>`.

  PASS requires this to be flagged under heading structure/order — a
  screen-reader user navigating by heading has no way to find this
  outcome. Score 0 if this is not flagged at all, or is only mentioned as
  a generic styling note without identifying the heading-navigation
  consequence; 1 if flagged with a fix naming a real heading element
  (e.g. `<h2>`).
focus: last_message
---

Tests check 3 (heading order/structure) against a case where there's no
literal "skipped level" — the failure is a titled content block with no
heading at all, which the skill's own text and the real dogfood finding
behind it both treat as the same category of problem.
