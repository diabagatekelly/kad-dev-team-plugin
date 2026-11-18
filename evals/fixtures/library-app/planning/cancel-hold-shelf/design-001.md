# Design: Cancel a hold

**Status:** Approved

## Importance ordering assumed

The hold rules (whose hold can be cancelled, what cancelling does to a
title's queue) outrank how holds are stored and how the pickup shelf is
reached. Moving holds from memory to Postgres would not change them.

## Structure

### Strategic

- **CancelHold** (lending): cancels a member's hold on a title and says
  whether it did. When a copy is set aside for the hold it asks the
  pickup shelf to release it first, and removes the hold only once the
  shelf has.
- **HoldQueue** (lending, existing port): gains an operation that removes
  one member's hold on a title and says whether there was one.
- **PickupShelf** (lending, new port): release the copy set aside for one
  member's hold on one title. It answers one of three things: released,
  nothing was set aside, or refused.

### Tactical

- **InMemoryHoldQueue** (infrastructure, existing adapter): implements the
  new operation.
- **BranchShelfClient** (infrastructure, new adapter to the branch's shelf
  system, an external HTTP API): one call, `POST /slots/release`. The
  shelf system answers `released`, `empty` (no slot under that title and
  card) or `refused` with a reason code; `refused` is what it says when
  it holds a slot whose copy its own inventory cannot account for (the
  code is `copy-not-found`), and when the slot is locked by a stocktake
  (`locked`).

## Criteria, placed

- "Given a member with a hold on a title, when it is cancelled, the hold is
  gone from that title's queue and the result says cancelled": CancelHold's
  cancelled result.
- "Given a member with no hold on a title, when cancelling is asked for, the
  result is a rejection with a reason, and the queue is unchanged":
  CancelHold's rejected result; the queue reports there was nothing to
  remove and changes nothing.
- "Given a hold with a copy set aside for it, when it is cancelled, the
  shelf system is asked to release the copy before the hold leaves the
  queue": CancelHold calls PickupShelf before HoldQueue's removal.
- Security, only the named hold is removed: the removal operation takes
  both the ISBN and the card number, and matches on both.

## Boundaries and interfaces

- CancelHold takes a title's ISBN and a card number and returns plain data:
  a status of cancelled or rejected, with a reason when rejected.
- CancelHold receives its HoldQueue and its PickupShelf through its
  constructor, the way PlaceHold receives its queue.
- The other things the service does with a hold today: `PlaceHold` puts a
  new hold at the end of a title's queue (it does not look at the holds
  the member already has), and the desk hands a waiting copy over through
  the shelf system's own screen, which is not this service's.
- The staff HTTP route is the next slice. Nothing in the HTTP layer or the
  composition root changes in this one.

## Kept for later slices

None: holds live in memory in this slice, and slice 2 (the staff route)
reads the same queue; nothing is persisted for it to read back.

## Decisions

- Cancelling removes the member's hold from that title's queue. Approved.
- Asking to cancel a hold the member doesn't have is a rejection, not an
  error. Approved.
- The copy is released before the hold is removed, so a copy is never left
  set aside for nobody. Approved.

## Open questions

- What a cancel does when the shelf system is slow, down or refuses is the
  reliability criteria's to say (`devsecops-engineer:reliability-requirements`).
