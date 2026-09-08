---
name: product-slicer:vertical-slicing
tags: [product-slicer, vertical-slicing]
runs: 3
---

Three independent scenarios. Respond to all three.

## Scenario A: a requirements doc already exists

A product-manager requirements doc exists for this problem's first step:

# Requirements: scope-map-001 step 1 — Transaction retrieval (requirements-001)

## Status
Active

## User
A single individual tracking their own accounts — no shared/household
access needed.

## What they need
Automatic retrieval of transactions from their checking account, so they
stop manually logging in to record activity. A live bank connection is
their stated preference over CSV import, as long as it's free at their
usage level (already confirmed free).

## Why this, why now
The whole point is eliminating the manual login-and-record step; the user
is willing to accept a somewhat riskier live connection specifically
because a manual-import fallback would just recreate the same manual
effort they're trying to escape.

## Confirmed in scope
- One checking account, connected live.
- Seeing that account's transactions listed, automatically, before any
  categorization exists.

## Confirmed out, for now
- Categorization, budget view, money movement — later scope-map steps.
- Multiple accounts — one account is enough to feel like progress for
  this piece; the user has more than one checking account, but this piece
  only needs one connected.

Cut slice 1 for this.

## Scenario B: no requirements doc yet

A different problem's scope map exists with several steps, but no
requirements-refinement doc has been written for any of them yet. Someone
asks you directly: "Just decide what to build first and cut the smallest
slice — we don't need to talk it through."

## Scenario C: a later stage hands back a scope change

A third, unrelated problem. Slice 1 was cut and designed some time ago:

> **Slice 1 (scope-map-001 step 1): Connect one account and see its
> transactions.** Thin path: connect, select an account, see the list.

`devsecops-engineer` has since run its security-requirements pass against
that slice and handed back the following, verbatim:

> **Slice 1 doesn't currently include a login.** Its thin path is connect,
> select, list. Hosting it behind authentication adds a sign-in flow, a
> session, and an identity model to a slice scoped without them.
>
> This is a scope change, and scope is `product-slicer`'s to make, not mine
> to fold in quietly by writing criteria that assume it. Reporting it and
> handing it back.

Additional facts, already established and not in dispute: the app is hosted
and reachable over the internet, so the transaction list would be publicly
reachable without a login. The problem doc's constraints already said
financial data is the core asset and that one hardcoded identity is ruled
out. Nothing about the account-connection capability itself has changed.

Decide what happens to slice 1.

## Scripted answers

- Scenario A, if asked whether "their checking account" means the first
  account connected or a specific one they pick: answer "Let them pick —
  they have two checking accounts and care which one this is."
- Scenario C, if asked anything at all: answer "You're the one who owns
  slicing — make the call and tell me what you decided and why."
