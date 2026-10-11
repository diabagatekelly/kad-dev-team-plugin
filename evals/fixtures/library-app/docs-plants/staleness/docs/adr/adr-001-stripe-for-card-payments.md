# ADR-001: Take card payments through Stripe

## Status
Accepted

## Context
Fines are paid by card at the desk. The library needs a card processor
that handles card data so the library's own systems never hold it.

## Decision
Card payments go through Stripe, with cards tokenised before they reach
the library's systems.

## Alternatives considered
- The county's merchant account: needs card data on library hardware,
  which brings PCI scope the library cannot staff.
- Square terminals only: covers the desk but leaves no path to online
  payment later.

## Consequences
The library never stores card numbers. It depends on one provider for
every card payment and pays Stripe's per-transaction fee.
