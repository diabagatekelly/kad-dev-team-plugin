# Problem: Members have to come to the desk for routine account tasks

## The problem

About 3,000 members borrow from one branch. The portal lets them see and
renew their loans, but everything else happens at one of the two staff
desks:

- Paying an outstanding fine.
- Placing a hold on a book that is checked out.
- Updating an address, phone number or email after a move.

Desk staff spend a large part of every shift on these, and members who
can't get in during opening hours wait days to do any of them.

## Why now

The branch is cutting desk hours from 60 to 45 a week in the spring.

## Constraints

- Card payments already go through Stripe; nothing about that changes.
- One developer maintains the service.
- Contact details changed online must be visible only to that member and
  to staff. The library's privacy policy covers all of a member's personal
  data, including what they borrow and what they have on hold.

## Open questions

- Should a hold placed online notify the member when the book comes back,
  the way a desk hold does today?
