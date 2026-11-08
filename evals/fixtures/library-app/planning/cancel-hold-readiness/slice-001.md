# Slice 1: Staff cancel a member's hold from the desk screen

## Thin path

A staff member opens the desk screen for a title, sees the holds on it,
and cancels one member's hold; the hold leaves the queue and the screen
says it was cancelled.

## Acceptance criteria

- Given a member with a hold on a title, when staff cancel it from the desk
  screen, the hold is gone from that title's queue and the screen says
  cancelled.
- Given a member with no hold on a title, when staff ask to cancel it, the
  screen shows a refusal with a reason, and the queue is unchanged.
- Security: see `security-slice-001.md` (S1, S2).
- Reliability: see `reliability-slice-001.md` (R1, R2).
- Accessibility: see `accessibility-slice-001.md` (A1, A2).

## Explicitly deferred

- Member self-service cancelling. Usable without it: members ask the desk, as they do today.
- Telling the next member they moved up the queue. Usable without it: the queue order is already right; the member learns of it on their next visit or notice, as today.
