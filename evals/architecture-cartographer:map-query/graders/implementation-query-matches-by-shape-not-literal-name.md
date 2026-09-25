---
type: llm
criteria: |
  Question 2 asks about a new `OrderRepository` class with a find-by-id
  method and a list-by-status method. No module literally named
  `OrderRepository` or anything about "orders" exists in the given map —
  the real candidate is `domain/case-directory.ts`, whose recorded exports
  (`findCaseById`, `listCasesByStatus`) share the same shape (find-by-id,
  list-by-status) under different domain naming. PASS only if the answer
  surfaces `CaseDirectory`/`case-directory.ts` as a candidate despite the
  literal name mismatch, reporting the specific shared shape (e.g. both
  expose a find-by-id and a list-by-status operation) as the stated
  overlap, without declaring that the new class should or shouldn't reuse
  it. FAIL if the answer reports nothing found (missing the shape match
  because the names differ), or if it renders a reuse verdict instead of
  handing back the candidate and its shared shape as facts.
focus: last_message
---

Checks matching works by recorded shape/overlap, not by literal name —
the exact gap this skill exists to close.
