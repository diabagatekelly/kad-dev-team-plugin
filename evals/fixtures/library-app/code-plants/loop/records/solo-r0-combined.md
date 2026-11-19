# Combined review: slice 001, the whole slice (round 0)

Range `@BASE@..@HEAD@`; read once, then `code-review`, `test-quality-review`, `architecture-review`, `security-review` and `reliability-review`.

## Findings

### A cancel for one card removes another member's hold

**Severity:** High
**Location:** infra/memory/in-memory-hold-queue.ts:21
**Category:** security: authorization

**What's happening:** `remove` finds the hold by its card number; read against `place`, two cards that share a prefix look as if the shorter one matches the longer, so a cancel for card 1001 would take card 10017's hold.

**Why it matters:** the security criterion says only the hold named by the card and ISBN is removed.

**Suggested fix:** compare the whole card number, and add a test with two cards sharing a prefix.

### `reason` is optional on both statuses

**Severity:** Medium
**Location:** lending/cancel-hold.ts:32
**Category:** code: primitive obsession

**What's happening:** `CancelHoldResult` lets a cancelled result carry a reason and a failed or rejected one omit it; every caller reads `reason ?? ''`.

**Why it matters:** the type says nothing about which status carries a reason, so each new caller re-derives the rule.

**Suggested fix:** a discriminated union, one member per status.

### The failure reason is a fixed string with nothing about which queue or title

**Severity:** Medium
**Location:** lending/cancel-hold.ts:50
**Category:** reliability: diagnosability

**What's happening:** every queue failure reports `hold queue unavailable`; the error the adapter threw is dropped.

**Why it matters:** when the queue moves to Postgres, the desk and the logs will see one message for a timeout, a bad connection string and a dropped table.

**Suggested fix:** keep the adapter's message in the result or log it before returning the fixed reason.

### `cancelNotice` picks the heading with a ternary that reads "not cancelled" for a failure too

**Severity:** Low
**Location:** lending/cancel-hold-notice.ts:31
**Category:** code: naming

**What's happening:** a `failed` result gets the heading "Hold not cancelled", the same as a rejection, so the desk cannot tell the two apart from the heading.

**Why it matters:** the status exists to tell them apart; the heading hides it again.

**Suggested fix:** a heading per status.

## Pre-existing, not blocking

None.

Counts: C0 H1 M2 L1.
