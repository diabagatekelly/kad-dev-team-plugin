---
type: llm
criteria: |
  Once `syncTransactionsForAccount` gives up after retries, there is
  nothing in the code that would let anyone tell apart: an account that
  failed to sync, an account that synced successfully with no new
  transactions, and an account that failed for a permanent reason (401)
  versus a transient one. PASS requires the review to frame this as an
  undiagnosable failure mode per the skill's explicit question — "for
  each way this can fail, could someone determine that it failed, and
  tell it apart from the other ways?" — rather than as a generic
  "needs more logging" suggestion. Score 0 if this angle is absent, or if
  the fix offered is generic ("add more logging/metrics") without naming
  which specific outcomes need to be distinguishable; 1 if the review
  names the specific outcomes that currently can't be told apart.
focus: last_message
---

Tests that observability gets reviewed as diagnosability (per the
skill's own explicit instruction not to review it as coverage) rather
than defaulting to "add more logs," which is the easier and less useful
thing to write.
