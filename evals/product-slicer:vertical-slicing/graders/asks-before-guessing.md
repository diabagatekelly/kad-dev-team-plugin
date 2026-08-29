---
type: llm
target: phase1
criteria: |
  Single-user vs. shared/multi-device access is an open question in the
  problem doc that changes whether slice one needs an identity/account
  concept at all — a shape-changing ambiguity, not a minor detail. The
  agent must ask about this directly (e.g. via a clarifying question)
  before committing to a final slice write-up, rather than silently
  assuming single-user (or shared) and proceeding straight to a finished
  scope. Score 0 if it guesses without asking; 1 if it asks first.
focus: last_message
---

Regression test for the "ask when it matters, defer when it doesn't" rule
in agents/product-slicer/AGENT.md — this is the exact scenario that rule
was written for.
