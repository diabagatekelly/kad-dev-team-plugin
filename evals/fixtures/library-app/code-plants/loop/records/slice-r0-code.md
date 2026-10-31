# Code review: slice 001, the whole slice (round 0)

Range `@BASE@..@HEAD@`; files lending/cancel-hold.ts, lending/cancel-hold-notice.ts, lending/hold-queue.ts, infra/memory/in-memory-hold-queue.ts and their tests.

## Findings

### `reason` is optional on both statuses

**Severity:** Medium
**Location:** lending/cancel-hold.ts:32
**Category:** primitive obsession

**What's happening:** `CancelHoldResult` lets a cancelled result carry a reason and a failed or rejected one omit it; every caller reads `reason ?? ''`.

**Why it matters:** the type says nothing about which status carries a reason, so each new caller re-derives the rule.

**Suggested fix:** a discriminated union, one member per status.

### `cancelNotice` picks the heading with a ternary that reads "not cancelled" for a failure too

**Severity:** Low
**Location:** lending/cancel-hold-notice.ts:31
**Category:** naming

**What's happening:** a `failed` result gets the heading "Hold not cancelled", the same as a rejection, so the desk cannot tell the two apart from the heading.

**Why it matters:** the status exists to tell them apart; the heading hides it again.

**Suggested fix:** a heading per status.

## Pre-existing, not blocking

None.

Counts: C0 H0 M1 L1.
