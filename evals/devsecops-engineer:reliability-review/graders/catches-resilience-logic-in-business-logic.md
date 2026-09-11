---
type: llm
criteria: |
  The retry-with-backoff loop lives directly inside
  `syncTransactionsForAccount` — a domain/use-case function — rather than
  inside the `bankClient` adapter that actually talks to the provider.
  PASS requires this being flagged per the skill's explicit framing:
  "resilience logic belongs in the adapter, not in business logic... when
  you find retry or circuit-breaker logic interleaved with domain
  decisions, that's a finding." Score 0 if this placement issue is never
  mentioned; 1 if the review notes the retry logic is in the wrong layer
  and should move to the adapter.
focus: last_message
---

Tests the skill's explicit cross-reference to the same boundary
`software-architect` draws — checking the review applies it as its own
finding rather than only checking failure-handling correctness in the
abstract.
