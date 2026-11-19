# Requirements: problem: Members have to come to the desk to keep a book longer (requirements-001)

## Status
Active

## User
A member with at least one book on loan, using the member portal.

## What they need
To renew a loan from the portal without coming in, and to be told
plainly when a renewal is not allowed.

## Why this, why now
Desk staff spend part of every shift on routine renewals. The member
asked for the plain renewal first; everything else can follow.

## Confirmed in scope
- A member renews one of their loans from the portal, and its due date
  moves on by the loan period.
- A renewal is refused when another member has a hold on that title.
- A loan can be renewed twice at most.
- An overdue loan cannot be renewed until its fine is paid.
- A member can renew all of their loans in one action.
- Staff can override a refused renewal from the desk screen.

## Confirmed out, for now
- Renewal reminders by email.
- Changing the loan period.

## Constraints in force
- One developer: nothing here may need a new service to run.

## Outside systems and lasting things
none
