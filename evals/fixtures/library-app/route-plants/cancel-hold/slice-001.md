# Slice 1: Staff cancel a member's hold on a title

## Thin path

Given a title with a member's hold on it, cancelling that member's hold
removes it from the title's queue, and the use case says it was cancelled.

## Acceptance criteria

- Given a member with a hold on a title, when it is cancelled, the hold is
  gone from that title's queue and the result says cancelled.
- Given a member with no hold on a title, when cancelling is asked for, the
  result is a rejection with a reason, and the queue is unchanged.
- Security: only the hold named by the card number and ISBN given is
  removed; no other member's hold on that title or any other changes.
- Reliability: a cancel asked for twice in a row removes the hold once and
  the second request is a rejection, never an error; if the hold queue
  can't be reached, the result is a failure the caller sees, and nothing is
  half-removed.

## Explicitly deferred

- The staff HTTP route (slice 2).
- Member self-service cancelling.
