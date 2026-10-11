# Design: Cancel a hold

**Status:** Approved

## Importance ordering assumed

The hold rules (whose hold can be cancelled, what cancelling does to a
title's queue) outrank how holds are stored. Moving holds from memory to
Postgres would not change them.

## Structure

- **CancelHold** (lending, strategic): cancels a member's hold on a title
  and says whether it did.
- **HoldQueue** (lending, strategic, existing port): gains an operation that
  removes one member's hold on a title and says whether there was one.
- **InMemoryHoldQueue** (infrastructure, tactical, existing adapter):
  implements the new operation.

## Boundaries and interfaces

- CancelHold takes a title's ISBN and a card number and returns plain data:
  a status of cancelled or rejected, with a reason when rejected.
- CancelHold receives its HoldQueue through its constructor, the way
  PlaceHold does.
- The staff HTTP route is the next slice. Nothing in the HTTP layer or the
  composition root changes in this one.

## Decisions

- Cancelling removes the member's hold from that title's queue. Approved.
- Asking to cancel a hold the member doesn't have is a rejection, not an
  error. Approved.

## Open questions

None recorded.
