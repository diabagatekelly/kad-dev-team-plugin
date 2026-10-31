# Reliability review: slice 001, fix round 1

Range `@HEAD@..@FIX@` (the fix's diff only); file lending/cancel-hold-notice.ts, test/cancel-hold-notice.test.ts.

## Findings

### `slice(-4)` on a card number shorter than four characters prints it whole

**Severity:** Medium
**Location:** lending/cancel-hold.ts:55
**Category:** unguarded input

**What's happening:** unchanged by the fix, which touched the notice only.

**Why it matters:** as in round 0.

**Suggested fix:** as in round 0.

Counts: C0 H0 M1 L0.
