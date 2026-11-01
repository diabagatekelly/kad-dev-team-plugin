# Reliability criteria: slice 001, staff cancel a member's hold from the desk screen

Written by `devsecops-engineer` (`reliability-requirements`), 2026-10-21.
Read with `security-slice-001.md`: the refused state's wording is S2's;
nothing here changes it.

## Target

Desk staff cancel a few holds a day. A cancel that fails loudly and can be
retried is acceptable; a cancel that reports success without removing the
hold is not.

## Failure modes

| Failure | What staff see | What the system does |
|---|---|---|
| The hold queue cannot be reached when a cancel is asked for | The unreachable-queue state | The result is a failure, not a rejection; nothing is half-removed |
| The same cancel is asked for twice in a row | The refused state | The hold is removed once; the second request is a rejection with a reason, never an error |

## Criteria

- R1: Given the hold queue cannot be reached, when a cancel is asked for,
  then the route retries the cancel a few times before showing the
  unreachable-queue state, and the queue is as it was.
- R2: Given a hold that was just cancelled, when the same cancel is asked
  for again, then the screen shows the refused state with a reason, never
  an error, and no other hold changes.

## Decisions

1. A queue failure is retried by the route, not by the use case. Approved
   2026-10-21.
