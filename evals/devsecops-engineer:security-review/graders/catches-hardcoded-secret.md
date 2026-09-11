---
type: llm
criteria: |
  `STRIPE_SECRET_KEY` is hardcoded directly in source as a live secret
  key (`sk_live_...`). PASS requires this being flagged as a Critical
  finding (a hardcoded live credential, per the skill's own severity
  taxonomy), with the fix naming that it must come from a managed secret
  store at runtime rather than living in committed source. It should also
  note the key needs rotating, not just removing, since a secret that was
  ever committed is compromised. Score 0 if this finding is missing, rated
  below Critical/High with no justification, or the suggested fix stops at
  "remove it from the file" without mentioning rotation; 1 if flagged at
  appropriate severity with rotation named.
focus: last_message
---

Tests the skill's explicit secrets-handling rules: hardcoded live
credentials are the named Critical example, and "removing it from the
current tree doesn't remove it from history" — rotation, not deletion, is
the actual fix.
