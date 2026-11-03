# Design: Cancel a hold from the desk screen

**Status:** Approved

## Importance ordering assumed

The hold rules (whose hold can be cancelled, what cancelling does to a
title's queue) outrank the screen and outrank how holds are stored.

## Structure

### Strategic

- **CancelHold** (lending): cancels a member's hold on a title and returns
  one of three results: cancelled; rejected, with a reason, when the
  member has no hold on that title or when the same cancel is asked for
  twice in a row (the hold is removed once, and the second request is a
  rejection with a reason, never an error); failed when the hold queue
  cannot be reached, with nothing half-removed and the queue as it was.
- **HoldQueue** (lending, existing port): gains an operation that removes
  one member's hold on a title and says whether there was one.

### Tactical

- **InMemoryHoldQueue** (infrastructure, existing adapter): implements the
  new operation.
- **Desk hold route** (infrastructure): `POST /holds/:isbn/cancel` for
  staff, calling CancelHold and rendering the desk screen's result as the
  cancelled state, the refused state, or the unreachable-queue state when
  the hold queue cannot be reached.

## Criteria, placed

- "Given a member with a hold on a title, when staff cancel it from the desk
  screen, the hold is gone from that title's queue and the screen says
  cancelled": CancelHold over HoldQueue's removal, rendered by the desk
  hold route as the cancelled state.
- "Given a member with no hold on a title, when staff ask to cancel it, the
  screen shows a refusal with a reason, and the queue is unchanged":
  CancelHold's rejected result, rendered as the refused state.
- S1, S2 (`security-slice-001.md`): the removal operation matches on both
  the ISBN and the card number; the refused state's reason names the card's
  last four digits only.
- R1, R2 (`reliability-slice-001.md`): a hold queue that cannot be reached
  is CancelHold's failed result, rendered as the unreachable-queue state;
  a second cancel is the rejected result.
- A1, A2 (`accessibility-slice-001.md`): the desk hold route renders each
  state with the design system's notice component.

## Boundaries and interfaces

- CancelHold takes a title's ISBN and a card number and returns plain data:
  a status of cancelled, rejected or failed, with a reason when not
  cancelled.
- CancelHold receives its HoldQueue through its constructor, the way
  PlaceHold does.
- The desk hold route parses the request and renders the state; nothing
  else in the HTTP layer changes.

## Kept for later slices

None: holds live in memory in this slice; nothing is persisted for a later
slice to read back.

## Decisions

- Cancelling removes the member's hold from that title's queue. Approved.
- A missing hold is a rejection, not an error. Approved.
- An unreachable store is a failed result and removes nothing. Approved.
- A repeated request is a rejection, never an error. Approved.

## Open questions

None recorded.
