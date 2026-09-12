---
type: llm
criteria: |
  This skill's job is two things from one pass: a findings report AND the
  slice's real accessibility acceptance criteria, replacing the
  placeholder — not a findings report alone.

  PASS requires the output to include acceptance criteria written in
  Given/When/Then form (matching the slice's existing functional
  criterion's own form), covering at least the keyboard-operability and
  heading/status-structure gaps this fixture contains, and distinguishing
  what's confirmed now against this mockup from what can only be verified
  once real code exists (e.g. whether a live-region actually announces on
  a real save failure). Score 0 if the output is only a findings list
  with no Given/When/Then acceptance criteria section, or the criteria
  don't distinguish confirmed-now from deferred; 1 if both are present.
focus: last_message
---

Tests the skill's core deliverable framing ("two things from one pass")
against the temptation to produce only the more familiar review-report
half and skip turning the result into the actual criteria the slice's
placeholder needs — the specific reason this skill exists rather than
being folded into a generic review.
