# Requirements: problem: Holds can only be cancelled at the desk (requirements-001)

## Status
Active

## User
Desk staff acting for a member who asks to drop a hold.

## What they need
Staff can cancel one member's hold on one title, and the member leaves that
title's queue. When a copy is already waiting for that member on the pickup
shelf, it goes back into circulation.

## Why this, why now
Unwanted holds keep other members waiting; staff handle a few a day.

## Confirmed in scope
- Cancelling a member's hold on a title.
- Asking to cancel a hold the member doesn't have is turned down, with a reason.
- A copy set aside for the cancelled hold is released by the branch's shelf
  system before the hold leaves the queue.

## Confirmed out, for now
- Members cancelling from the portal: staff do it for now.
- Telling the next member they moved up the queue.
- Recording a copy as lost or withdrawn: the catalogue team does that in
  the shelf system itself, on their weekly round.

## Constraints in force
- One developer maintains the service: no new service or scheduled job; the
  change lives in the existing lending module.
- The shelf system is the branch's, reached over its HTTP API; this service
  does not own its records.
