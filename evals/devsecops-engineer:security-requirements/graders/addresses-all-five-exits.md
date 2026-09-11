---
type: llm
criteria: |
  The skill names five exits a sensitive data class can leak through:
  logs, exception messages/stack traces, error responses returned to a
  caller, monitoring/telemetry/analytics, and test fixtures/sample data —
  and says each is a candidate criterion, with anything not written as a
  criterion said to be "considered and dismissed, with reasons" so the
  next person doesn't re-derive it.

  PASS requires the output to address all five exits within this document
  itself for the sensitive data it identifies (the connection
  credential/token, at minimum) — each exit either gets a concrete
  criterion, or is explicitly named and dismissed with a stated reason
  (e.g. "no telemetry exists in this slice, so this exit doesn't apply").
  Silently never mentioning an exit is a fail even if the omission would
  be defensible if stated — the requirement is that it's addressed
  in-document, not merely that the right answer happens to be "doesn't
  apply."

  Score 0 if any of the five exits (logs, exceptions/stack traces, error
  responses, monitoring/telemetry/analytics, test fixtures) is never
  mentioned anywhere in the output — as a criterion or as a dismissal; 1
  if all five are addressed one way or the other.
focus: last_message
---

Added after auditing `evals/example/security-requirements-001.md` against
this skill directly (not assuming it was correct because it was real
output). That document has criteria or dismissals for four of the five
exits, but never addresses monitoring/telemetry/analytics within the
document itself — the reasoning that no telemetry exists in that slice
only appears in the sibling `reliability-requirements-001.md`. A reader of
the security document alone doesn't get that closure, which is exactly
the failure mode this skill's own text warns about ("the exits are what
people miss"). This grader exists so a future run doesn't repeat the same
gap.
