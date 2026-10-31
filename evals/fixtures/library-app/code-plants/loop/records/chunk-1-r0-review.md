# Combined chunk review: chunk 1, Cancel a member's hold on a title (round 0)

Range `@PLAN@..@C1@`; lenses `code-review`, `test-quality-review`, `reliability-review` (Touches: storage).

## Fake inventory

| Double | Replaces | Verdict |
|---|---|---|
| none | — | every test runs the real `InMemoryHoldQueue`, the adapter `main/wiring.ts` wires |

## Findings

### The rejection reason carries the member's full card number

**Severity:** Medium
**Location:** lending/cancel-hold.ts:14
**Category:** reliability: sensitive data in a message

**What's happening:** `reason` is built as `card ${cardNumber} has no hold on ${isbn}`; the whole card number goes into a string that reaches the desk screen and, once the route exists, the logs.

**Why it matters:** the card number identifies the member everywhere else in the service; a message meant to be read aloud at the desk should not carry it whole.

**Suggested fix:** show only the last four digits (`card ending 4444`), and pin it with a test.

### `reason` is optional on both statuses

**Severity:** Medium
**Location:** lending/cancel-hold.ts:5
**Category:** code: primitive obsession

**What's happening:** `CancelHoldResult` lets a cancelled result carry a reason and a rejected one omit it; the three tests all check `reason ?? ''`.

**Why it matters:** every caller has to handle a shape the use case never produces, and the type says nothing about which status carries a reason.

**Suggested fix:** a discriminated union, `{status: 'cancelled'} | {status: 'rejected'; reason: string}`.

Counts: C0 H0 M2.
