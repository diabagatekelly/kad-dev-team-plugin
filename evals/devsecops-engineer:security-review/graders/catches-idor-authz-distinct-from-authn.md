---
type: llm
criteria: |
  `GET /invoices/:id` runs behind `requireAuth`, which establishes WHO the
  caller is, but nothing checks that the authenticated user owns or may
  access the specific invoice ID they supplied — any authenticated user
  can read any invoice by guessing or incrementing IDs. PASS requires this
  being flagged as an authorization gap distinct from authentication (the
  skill's own framing: "knowing who someone is doesn't establish that they
  may touch this record"), at High or Critical severity given it exposes
  another user's data. Score 0 if this finding is missing, if it's
  conflated with "no authentication" (which is present and correct here),
  or if severity is Low/Medium with no justification; 1 if the missing
  per-record ownership check is identified as its own finding at
  appropriate severity.
focus: last_message
---

Tests the skill's explicit authorization-distinct-from-authentication
check against a fixture built so authentication is genuinely present and
correct, isolating whether the review still catches the authorization gap
underneath it.
