---
type: llm
criteria: |
  This grades the FINAL output, after the agent received the answer to its
  clarifying question (single-user only). It must be an actual finished
  slice write-up — thin path, Given/When/Then acceptance criteria,
  explicitly deferred, still open — not another question, and not still
  hedging on single-user vs. shared access. It must correctly reflect
  "single-user" (e.g. not scoping in multi-device/shared-account concerns
  it was just told don't apply). It must still include a placeholder
  acceptance criterion for security/accessibility review rather than
  authoring one directly (per the "ask when it matters" / placeholder rule
  in agents/product-slicer/AGENT.md) — that rule doesn't go away just
  because a different question got answered. FAIL if it's still a
  question, ignores the answer, or authors security/accessibility
  criteria directly instead of a placeholder.
focus: last_message
---

Regression test for the ask-then-continue gap: the persona should actually
finish the job once it has the answer it asked for, not just demonstrate
that it knows how to ask.
