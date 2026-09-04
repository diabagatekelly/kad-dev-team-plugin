---
type: llm
criteria: |
  `domain/gateways.types.ts` imports `MongoClientOptions` from `mongodb`
  and exposes it on the `AccountGateway` interface — a types file that
  looks clean from the caller's side (`link-account.use-case.ts` only
  imports the interface, not Mongo directly) but is itself contaminated.
  PASS only if the review identifies `gateways.types.ts` itself as the
  actual violation site (not just "the use case imports something bad"),
  explains or clearly implies the two-direction reasoning (forward check
  on the use case looks clean; the violation is in what the types file
  itself depends on), and rates it High severity or higher given it
  contaminates every strategic file that depends on the interface. FAIL if
  the review misses this violation entirely, misattributes it to the use
  case rather than the types file, or rates it Low/Medium without
  justification.
focus: last_message
---

Checks the two-direction dependency check actually gets applied, not just
described as a principle.
