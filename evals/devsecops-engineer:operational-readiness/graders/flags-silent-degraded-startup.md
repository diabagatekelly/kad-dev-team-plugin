---
type: llm
criteria: |
  The app currently starts even when a required environment variable
  (the database connection string) is missing, and returns a 500 for
  every request instead of failing to start. PASS requires this being
  flagged as a finding, per the skill's explicit, near-verbatim example:
  "Startup fails loudly on missing configuration rather than starting
  degraded and failing later on a code path nobody exercises
  immediately." Score 0 if this is never mentioned; 1 if the
  silently-degraded-startup behavior is identified as a finding, with
  fail-fast-on-missing-config as the fix.
focus: last_message
---

Tests a specific, concretely-named check from the skill's
"Configuration and environment" section against a fixture built to have
exactly that gap.
