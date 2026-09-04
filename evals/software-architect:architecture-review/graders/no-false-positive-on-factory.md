---
type: llm
criteria: |
  `LinkAccountUseCase` obtains its gateway via `getAccountGateway()`, a
  composition-root factory that returns the interface type; the use case
  never imports the concrete Mongo-backed class. PASS only if the review
  does NOT flag this factory call itself as a Dependency Rule violation —
  at most it may separately note the real violation inside
  `gateways.types.ts` (graded elsewhere), but the factory-call pattern
  itself must be treated as correct composition-root wiring, not business
  code depending on infrastructure. FAIL if the review flags
  `getAccountGateway()` or the use case's use of it as a violation.
focus: last_message
---

Checks the composition-root exception is actually applied, not just
stated as a principle — this is the false positive a naive dependency
scan would produce.
