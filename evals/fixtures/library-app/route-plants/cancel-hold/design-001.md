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

## Criteria, placed

- "Given a title with a member's hold on it, cancelling that member's hold
  removes it from the title's queue, and the use case says it was
  cancelled": CancelHold over HoldQueue's removal operation.
- "Given a member with a hold on a title, when it is cancelled, the hold is
  gone from that title's queue and the result says cancelled": CancelHold's
  cancelled result.
- "Given a member with no hold on a title, when cancelling is asked for, the
  result is a rejection with a reason, and the queue is unchanged":
  CancelHold's rejected result; the queue reports there was nothing to
  remove and changes nothing.
- Security, only the named hold is removed: the removal operation takes
  both the ISBN and the card number, and matches on both.
- Reliability, a second cancel is a rejection and an unreachable queue is a
  failure the caller sees: CancelHold's rejected result for the first, and
  a failure result distinct from a rejection for the second, with the
  removal operation doing nothing when it cannot reach the queue.

## Boundaries and interfaces

- CancelHold takes a title's ISBN and a card number and returns plain data:
  a status of cancelled or rejected, with a reason when rejected.
- CancelHold receives its HoldQueue through its constructor, the way
  PlaceHold does.
- The staff HTTP route is the next slice. Nothing in the HTTP layer or the
  composition root changes in this one.

## Kept for later slices

None: holds live in memory in this slice, and slice 2 (the staff route)
reads the same queue; nothing is persisted for it to read back.

## Decisions

- Cancelling removes the member's hold from that title's queue. Approved.
- Asking to cancel a hold the member doesn't have is a rejection, not an
  error. Approved.

## Open questions

None recorded.
