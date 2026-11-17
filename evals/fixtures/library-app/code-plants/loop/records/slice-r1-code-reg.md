# Code review: slice 001, fix round 1

Range `@HEAD@..@FIX@` (the fix's diff only); file lending/cancel-hold-notice.ts, test/cancel-hold-notice.test.ts.

## Findings

### The fix's escaping of quotes is held by no test

**Severity:** Medium
**Location:** lending/cancel-hold-notice.ts:36
**Category:** tests: a changed line nothing asserts

**What's happening:** the fix adds five replacements and its one test feeds a reason with `<` and `>` only; the `&quot;` and `&#39;` lines can be deleted and the suite stays green.

**Why it matters:** the reason is the member-facing text most likely to carry a quote (a title in quotes), and the next edit to `escapeHtml` has nothing to stop it.

**Suggested fix:** one test with a reason that holds both quote characters and an ampersand.

### `reason` is optional on both statuses

**Severity:** Medium
**Location:** lending/cancel-hold.ts:32
**Category:** primitive obsession

**What's happening:** unchanged by the fix: `CancelHoldResult` still lets a cancelled result carry a reason and a failed or rejected one omit it.

**Why it matters:** as in round 0.

**Suggested fix:** the discriminated union from round 0.

Counts: C0 H0 M2 L0.
