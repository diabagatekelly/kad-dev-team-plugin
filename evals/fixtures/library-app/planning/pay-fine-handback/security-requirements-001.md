# Security requirements: Slice 1 — A member pays an outstanding fine from the portal

Replaces the security placeholder in slice-001. Written against design-001.

## What's in play
Members' session tokens, the Stripe card token, each member's fine records.
Members are individuals; a member sees only their own fines.

## Acceptance criteria
- Given a signed-in member, when they request their fines, only fines
  recorded against their own library card number are returned.
- Given a member pays a fine, the application never receives, stores or
  logs a card number or security code; only the Stripe token crosses in.

## Handed back to product-slicer — blocking

The library's merchant agreement, confirmed with the finance officer,
requires that a cardholder paying online receives a receipt showing the
amount, the date and the library's name, and that the library keeps a
copy. Desk payments get a till receipt. Nothing in this slice or the scope
gives a member any record of a portal payment beyond the fine showing as
paid, and no document says what a receipt is here. Shipping online payment
without one is not acceptable to the library. That is a capability nobody
scoped, and it is handed back rather than resolved here.
