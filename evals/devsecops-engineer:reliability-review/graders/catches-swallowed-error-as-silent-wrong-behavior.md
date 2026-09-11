---
type: llm
criteria: |
  After exhausting all 5 retry attempts, `syncTransactionsForAccount`
  logs at `debug` level and returns normally (`return;`) with no
  exception, no error flag, and nothing distinguishing this account from
  one that synced successfully or genuinely had nothing new. PASS
  requires this being flagged as a swallowed error per the skill's
  explicit framing: a catch that "logs at debug and continues has
  converted a failure into wrong behavior, which is strictly worse — the
  system now proceeds on bad state and nobody knows." Score 0 if this is
  missing, or if it's framed only as a logging-level nitpick ("should log
  at error level") without naming that the caller (`syncAllAccounts`) has
  no way to know this account failed at all; 1 if the silent-failure
  behavior itself is flagged, not just the log level.
focus: last_message
---

Tests the skill's distinction between a logging-level complaint and the
actual finding: the caller has no signal that anything went wrong at
all, regardless of what level the debug line logs at.
