---
type: llm
criteria: |
  PASS only if the output's module table (or equivalent structured
  listing) correctly reflects what the seven given source files actually
  contain: `domain/refund-ledger.ts` and `domain/credit-ledger.ts` each
  show an internal edge to `domain/order-directory.ts` (both literally
  `import { OrderDirectory } from './order-directory'`); `domain/assign-refund.use-case.ts`
  shows an internal edge to `infra/mongo-refund-store.ts`;
  `infra/mongo-order-directory.ts` and `infra/mongo-refund-store.ts` each
  show an external package reference to `mongodb`; `util/currency-format.ts`
  shows no edges and exports only `formatCurrency`. Exports listed per
  module should match what's actually exported in the source (e.g.
  `RefundLedger` exports the class itself, not its private constructor
  parameter). FAIL if an edge or export is fabricated (not present in the
  given source), a real edge or export is missing, or an external package
  is confused with an internal edge (or vice versa).
focus: last_message
---

Checks the mechanical extraction is faithful to the actual given source
text — the core of what makes this skill's output a fact rather than a
narrated guess.
