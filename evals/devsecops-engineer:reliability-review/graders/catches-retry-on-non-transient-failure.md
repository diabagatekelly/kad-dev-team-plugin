---
type: llm
criteria: |
  The retry loop in `syncTransactionsForAccount` retries on ANY thrown
  error from `fetchTransactions`, including a 401 (revoked authorization)
  — a state the prompt explicitly says can't be fixed by retrying. PASS
  requires this being flagged per the skill's explicit framing: "retrying
  something that isn't transient... is amplification: it turns one
  failure into several, adds latency to a request already doomed." The
  finding should note that the retry logic doesn't distinguish which
  failures are worth retrying. Score 0 if this is missing, or if the
  retry loop's blanket retry-on-any-error behavior is only mentioned in
  passing without being named as a reliability problem in its own right;
  1 if flagged as retrying a non-transient failure.
focus: last_message
---

Tests the skill's own most-emphasized resilience-pattern mistake ("the
finding to look for hardest") against a fixture with a concrete
non-transient failure (401) folded into a blanket retry loop.
