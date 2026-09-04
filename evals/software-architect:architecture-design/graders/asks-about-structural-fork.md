---
type: llm
criteria: |
  Grading phase 1 — the first response. Under the current behavior, every
  real decision (not just genuine ambiguities) must be presented one at a
  time with a recommendation, the alternative(s) considered and rejected,
  and an explicit request for approval — never decided silently and only
  mentioned in the final doc. PASS only if this response: (a) presents
  exactly one decision (the synchronous-vs-asynchronous export question),
  not multiple decisions bundled together; (b) states a clear
  recommendation (synchronous) with a reason; (c) names the alternative
  considered (an async job queue) and why it's not preferred here; (d)
  explicitly asks for the user's approval/choice rather than proceeding.
  FAIL if it silently assumes an answer instead of asking, presents more
  than one decision in this single response, asks without a
  recommendation (a bare "which do you want?" with no stated lean), or
  asks about something the slice already answered elsewhere (e.g. which
  export format — CSV is already decided).
focus: last_message
target: phase1
---

Checks the persona presents a decision with a recommendation and
alternative, not just a bare ambiguity question — the sharper "surface
every decision for approval" bar, not the old "only ask when genuinely
stuck" bar.
