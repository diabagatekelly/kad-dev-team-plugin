---
type: llm
criteria: |
  `OrderSummaryFormatter.describe` in `pricing.ts` never reads `this.locale`
  (the only field on its own class) but reaches deeply into `order` six
  separate times (`order.customer.firstName`, `order.customer.lastName`,
  `order.items.length`, `order.totals.grandTotal`,
  `order.shipping.address.city`, `order.shipping.address.state`). PASS
  requires this being flagged as feature envy — a method that reads far
  more of another object's data than its own, suggesting it may belong
  somewhere else (e.g. on `Order` itself). FAIL if this is missed entirely,
  or if it's flagged only as an unrelated issue (e.g. just "long line")
  without naming the actual feature-envy shape (reads mostly another
  object's data, not its own).
focus: last_message
---

Checks the feature envy check specifically — never exercised by any prior
grader in this case.
