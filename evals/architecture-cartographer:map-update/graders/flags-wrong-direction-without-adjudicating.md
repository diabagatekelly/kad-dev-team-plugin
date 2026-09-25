---
type: llm
criteria: |
  `domain/assign-refund.use-case.ts` (tier 1, per the design doc) directly
  imports `infra/mongo-refund-store.ts` (tier 3) — a more-important module
  depending on a less-important one, the wrong direction. PASS only if
  this edge is flagged as a wrong-direction candidate, naming both modules
  and their tiers as the mechanical basis for the flag. The flag must be
  reported as a candidate fact, not an adjudicated violation the response
  insists must be fixed now, and not something the response asks the user
  about — no clarifying question, no "should I flag this as a problem."
  FAIL if the edge is missed, if it's declared a definite violation
  requiring an immediate fix rather than a flagged candidate, or if the
  response asks a question about it instead of just reporting it.
focus: last_message
---

Checks the wrong-direction check fires correctly and stays mechanical —
flagged, not adjudicated, not asked about.
