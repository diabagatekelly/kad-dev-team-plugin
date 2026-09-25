---
type: llm
criteria: |
  Question 1 asks about a structural boundary for persisting and
  retrieving case-linked records. The map's `domain/case-directory.ts` /
  `domain/case-directory.types.ts` (tier 1) plus its `infra/mongo-case-directory.ts`
  implementation (tier 3) is the real comparable boundary already in the
  map. PASS only if the answer to question 1 surfaces this candidate (by
  path or by name — `CaseDirectory` is enough), reports it using facts the
  map actually records (its tier, and/or its exports/edges), and does not
  render a verdict on whether it should actually be reused for court
  orders (no "yes, reuse this" / "this is close enough" / "you should
  build on this instead"). FAIL if the candidate is missed entirely, if a
  module not present in the given map is invented, or if the answer
  declares a reuse verdict rather than handing the fact back.
focus: last_message
---

Checks the structural-level query correctly surfaces the real candidate
from the map as a fact, not a verdict.
