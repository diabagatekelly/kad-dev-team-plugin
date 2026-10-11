# Design: Cancel a hold

**Status:** Approved

## Importance ordering assumed

CancelHold is strategic (tier 1), alongside the rest of `lending/`. The
in-memory hold queue stays tactical (tier 3).

## Structure

- **CancelHold** (lending): cancels a member's hold on a title.
- **HoldQueue** (lending, existing port): gains a removal operation.
- **InMemoryHoldQueue** (infrastructure, existing adapter): implements it.
