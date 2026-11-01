# Security criteria: slice 001, staff cancel a member's hold from the desk screen

Written by `devsecops-engineer` (`security-requirements`), 2026-10-21.

## In play

Staff sessions (the existing `requireRole('staff')` guard on `/holds`),
members' card numbers in the hold queue. No card data, no payment.

## Criteria

- S1: Given a staff request naming an ISBN and a card number, when the
  cancel runs, then only the hold with both that ISBN and that card number
  is removed; no other member's hold on that title changes.
- S2: Given a cancel is refused, when the refused state is shown, then the
  reason names at most the card's last four digits, never the whole
  number, and names no other member.

## Decisions

1. The refused state shows the last four digits only. Approved 2026-10-21.
