---
type: llm
criteria: |
  Two separate findings expected. (1) `PayInvoiceUseCase` branches inline
  across three concrete payment SDKs (Stripe, PayPal, Square) with no
  shared interface — three concrete implementations already exist right
  now, so this is a missing abstraction (under-engineering), not a
  hypothetical one, and each SDK is also a high-lock-in third-party
  dependency used directly in business logic (Invasive Species). PASS
  requires this use case being flagged as needing a
  payment-provider-shaped interface/adapter, described as a real
  already-visible need rather than speculative. (2) The directory
  structure (`controllers/`, `services/`, `models/`, `repositories/` as
  top-level groupings) organizes by technical role rather than business
  concept — PASS requires this being flagged as a Screaming Architecture
  violation. FAIL if either finding is missing, or if the payment use
  case is only described as an over-engineering/YAGNI concern rather than
  a missing-abstraction one (it should be the "under-engineering" side of
  the two-sided check, since the implementations already exist today).
focus: last_message
---

Checks the review catches the "missing abstraction" half of the two-sided
mandate (not just premature abstraction, which the architecture-design
eval already covers) and the Screaming Architecture violation.
