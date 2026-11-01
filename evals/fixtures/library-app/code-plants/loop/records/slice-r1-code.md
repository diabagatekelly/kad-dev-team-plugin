# Code review: slice 001, fix round 1

Range `@HEAD@..@FIX@` (the fix's diff only); file lending/cancel-hold-notice.ts, test/cancel-hold-notice.test.ts.

## Findings

### `reason` is optional on both statuses

**Severity:** Medium
**Location:** lending/cancel-hold.ts:32
**Category:** primitive obsession

**What's happening:** unchanged by the fix: `CancelHoldResult` still lets a cancelled result carry a reason and a failed or rejected one omit it.

**Why it matters:** as in round 0.

**Suggested fix:** the discriminated union from round 0.

Counts: C0 H0 M1 L0.
