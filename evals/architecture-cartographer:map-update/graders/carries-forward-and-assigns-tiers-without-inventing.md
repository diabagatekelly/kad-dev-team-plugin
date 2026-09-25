---
type: llm
criteria: |
  PASS only if: (1) `domain/order-directory.ts` keeps tier 1 and
  `infra/mongo-order-directory.ts` keeps tier 3, both carried forward
  from the prior map without being re-derived from their imports; (2)
  `domain/refund-ledger.ts`, `domain/credit-ledger.ts`, and
  `domain/assign-refund.use-case.ts` are recorded as tier 1, and
  `infra/mongo-refund-store.ts` as tier 3, exactly matching the design
  doc's stated importance ordering; (3) `util/currency-format.ts` — named
  in neither the prior map nor the design doc's ordering — is recorded
  explicitly as untiered (or equivalent unambiguous "no tier assigned"
  language), not silently omitted, not guessed at, and not defaulted to
  match a neighboring module's tier. FAIL if any of the three fails, or if
  a tier is justified by reasoning about the import graph itself rather
  than by the prior map or the design doc.
focus: last_message
---

Checks tiers are carried forward and applied exactly as given, and that a
genuinely untiered module is reported honestly rather than guessed.
