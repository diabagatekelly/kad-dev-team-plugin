# Requirements: problem: Holds can only be cancelled at the desk (requirements-001)

## Status
Active

## User
Desk staff acting for a member who asks to drop a hold.

## What they need
Staff cancel one member's hold on one title from the desk screen, and the
member leaves that title's queue.

## Why this, why now
Unwanted holds keep other members waiting; staff handle a few a day, and
today it means a database console.

## Confirmed in scope
- Cancelling a member's hold on a title from the desk screen.
- Asking to cancel a hold the member doesn't have is turned down, with a
  reason, on the same screen.

## Confirmed out, for now
- Members cancelling from the portal: staff do it for now.
- Telling the next member they moved up the queue.

## Constraints in force
- One developer maintains the service: no new service or scheduled job; the
  change lives in the existing lending module and the staff screens.
