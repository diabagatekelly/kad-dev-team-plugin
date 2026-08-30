---
type: llm
target: phase1
criteria: |
  The output must be genuine clarifying questions to the user about WHO
  benefits, WHAT they specifically want for this step, WHY (priority or
  trade-off), and/or what the simplest version that still feels like
  progress would be — NOT a finished requirements doc produced by
  inferring these answers from the scope map alone. Score 0 if it
  produces a finished requirements write-up without asking first, or asks
  only trivial/unrelated questions; 1 if it genuinely asks before
  deciding.
---

This persona's entire value is asking instead of inferring — this is the
core behavior under test, checked against the question it asks before any
scripted answer is supplied.
