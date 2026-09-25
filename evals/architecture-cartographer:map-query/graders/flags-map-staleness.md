---
type: llm
criteria: |
  The setup mentions, before the three questions, that a `RefundLedger`
  module finished on a branch yesterday and hasn't gone through a
  `map-update` run yet — so the given map is known to be incomplete
  relative to the real codebase. PASS if the response acknowledges,
  somewhere across its answers (a single mention covering all three
  questions is enough — it doesn't need to be repeated three times), that
  the map may not reflect very recent changes like this and that a
  negative or partial result should be read with that in mind. FAIL if the
  response treats the given map as a complete, current picture of the
  codebase with no caveat at all, or if it claims to have gone and
  checked the actual current codebase itself rather than reading only the
  given map (this skill is read-only and never regenerates from source).
focus: last_message
---

Checks the skill treats a known-stale map honestly rather than silently
trusting it as complete, and doesn't cross into regenerating live (that's
map-update's job, not this skill's).
