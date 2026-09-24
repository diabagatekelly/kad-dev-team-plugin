---
type: llm
criteria: |
  `formatLineItem` and `getLineItemIcon` in `pricing.ts` both switch on
  `item.kind` with the same three cases (physical/digital/subscription)
  plus a default — the same type-code switch duplicated twice in the same
  file. PASS requires this being flagged as a finding (a candidate for a
  lookup table or polymorphism), AND treated as a local, same-file fix —
  NOT handed off to `architecture-review` as a module-boundary/structural
  question, since consolidating two functions already sitting in the same
  file doesn't require introducing a new module. FAIL if this duplication
  is missed entirely, or if it's deferred to `architecture-review` instead
  of graded as one of this skill's own findings.
focus: last_message
---

Tests the type-switch-duplication check specifically, and the "stays local
unless the fix needs a new module" half of the architecture-review
boundary — the mirror image of the Stripe-SDK case, which correctly does
need to be handed off.
