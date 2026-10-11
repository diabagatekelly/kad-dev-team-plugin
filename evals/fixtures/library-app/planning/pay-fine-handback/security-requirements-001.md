# Security requirements: Slice 1 — A member pays an outstanding fine from the portal

Replaces the security placeholder in slice-001. Written against design-001.

## What's in play
Members' session tokens, the Stripe card token, each member's fine records.
Members are individuals; a member sees only their own fines.

## Acceptance criteria
- Given a signed-in member, when they request their fines, only fines
  recorded against their own card number are returned.
- Given a member pays a fine, the application never receives, stores or
  logs a card number or security code; only the Stripe token crosses in.

## Handed back to product-slicer — blocking

A member who disputes a charge, or is charged for a fine that was then
waived at the desk the same day, has no way to get the money back: refunds
exist only as a staff action, and nothing in this slice or the scope gives
members a path to one. Shipping online payment without any refund path for
members is not acceptable to the library. That is a capability nobody
scoped; whether this slice grows to include it, or a new slice comes
first, is a scope decision for product-slicer, not something this pass
resolves.
