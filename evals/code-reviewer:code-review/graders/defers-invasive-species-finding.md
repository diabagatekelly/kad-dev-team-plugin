---
type: llm
criteria: |
  `processOrder` instantiates `new Stripe(process.env.STRIPE_KEY)` and calls
  it directly inline in business logic — a high-lock-in third-party SDK used
  directly rather than behind an adapter, which is `architecture-review`'s
  Invasive-Species/Dependency-Rule territory, not this skill's own DRY/
  naming/comment scope. PASS requires one of: (a) this isn't mentioned at
  all, or (b) it's named in a separate section clearly marked as outside
  this review's scope and handed to `architecture-review`, NOT ranked
  alongside this skill's own Critical/High/Medium/Low findings list. FAIL
  if it's graded as one of this skill's own severity-ranked findings (i.e.
  treated as if code-reviewer itself is rendering the architectural
  verdict).
focus: last_message
---

Checks the boundary this persona's synthesis explicitly holds: it may
notice something structural, but it doesn't grade it — that stays
architecture-review's call.
