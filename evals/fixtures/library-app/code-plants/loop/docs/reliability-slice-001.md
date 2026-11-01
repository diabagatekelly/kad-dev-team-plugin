# Reliability criteria: slice 001, staff cancel a member's hold on a title

Written by `devsecops-engineer` (`reliability-requirements`), 2026-10-21.
Security criteria: `security-slice-001.md` is not a separate document for
this slice; the one security criterion is in `slice-001.md` and shares no
failure path with the rows below.

## Target

Desk staff cancel a few holds a day. A cancel that fails loudly and can be
retried by hand is acceptable; a cancel that reports success without
removing the hold is not.

## Failure modes

| Failure | What the member or staff see | What the system does |
|---|---|---|
| The hold queue cannot be reached when a cancel is asked for | Staff see that the cancel did not happen | The result is a failure the caller sees, not a rejection; nothing is half-removed |
| The same cancel is asked for twice in a row | Staff see the second request turned down | The hold is removed once; the second request is a rejection with a reason, never an error |

## Criteria

- R1: Given the hold queue cannot be reached, when a cancel is asked for,
  then the result is a failure the caller can tell from a rejection, and
  the queue is as it was.
- R2: Given a hold that was just cancelled, when the same cancel is asked
  for again, then the result is a rejection with a reason, never an
  error, and no other hold changes.

## Decisions

1. A queue failure is not retried inside the use case: the desk retries
   by hand, and the queue is in memory today. Approved 2026-10-21.
