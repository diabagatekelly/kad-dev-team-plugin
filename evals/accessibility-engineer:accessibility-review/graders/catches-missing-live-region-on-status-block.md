---
type: llm
criteria: |
  `.status-block` (the "couldn't be saved" failure message) carries no
  `role="status"`, `role="alert"`, or `aria-live` attribute anywhere in
  the markup.

  PASS requires this absence to be flagged as a current, checkable-now
  finding (not deferred to "needs real code") — the skill's own text
  treats a missing live-region attribute as visible in static markup
  today, distinct from whether it actually announces correctly once wired
  to a real save failure. Score 0 if this is missing entirely, or is only
  listed under deferred/not-yet-verifiable items rather than as a current
  finding; 1 if flagged now with a specific role/attribute suggested.
focus: last_message
---

Tests check 8 (live region declared in markup), the second addition made
to `SKILL.md` after real dogfooding — and specifically tests that the
skill's "confirmable now vs. deferred" split is applied correctly: the
*attribute's presence* is checkable today even though whether it
*announces correctly* is not.
