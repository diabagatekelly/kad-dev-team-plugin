# Problem: Members can only pay fines at the desk

## What's happening

About 3,000 members borrow from one branch. When a loan goes overdue the
nightly job assesses a fine, and the only way to clear it is in person at
one of the two staff desks. Members who can renew and see their loans in
the portal still have to come in to pay, and desk staff spend part of every
shift taking small card payments.

## Who it affects

Members with an outstanding fine, and the staff at both desks.

## Constraints

- Card payments already go through Stripe; nothing about that changes.
- One developer maintains the service.

## Open questions

- Should a member who pays online get a receipt, by email or on the page,
  the way the desk prints one today?
- Does the desk keep taking card payments once members can pay online, or
  does it stop?
