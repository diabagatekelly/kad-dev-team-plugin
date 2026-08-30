---
type: llm
target: phase1
criteria: |
  For Scenario A, the requirements doc already confirmed WHAT (single-user,
  live bank connection preferred over CSV, one checking account, why).
  Product-slicer must NOT re-ask any of that — no re-asking single-user
  vs. shared, no re-asking connection mechanism preference. If it asks a
  question, it must be a genuine technical-slicing (HOW) ambiguity not
  resolved by the requirements doc — e.g. which specific checking account,
  given the user has more than one. Score 0 if it re-asks a WHAT-level
  question already resolved in the requirements doc, or silently guesses
  on the genuine HOW ambiguity without asking; 1 if it asks only the
  HOW-level question (or reasonably identifies no ambiguity and proceeds,
  as long as it doesn't re-litigate WHAT).
---

Tests the core boundary this round's changes established: product-slicer
re-asking WHAT would mean product-manager's whole reason for existing
didn't survive the hand-off.
