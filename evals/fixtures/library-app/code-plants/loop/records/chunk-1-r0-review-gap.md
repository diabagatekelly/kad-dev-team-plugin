# Combined chunk review: chunk 1, Cancel a member's hold on a title (round 0)

Range `@PLAN@..@C1@`; lenses `code-review`, `test-quality-review`, `reliability-review` (Touches: storage).

## Fake inventory

| Double | Replaces | Verdict |
|---|---|---|
| none | — | every test runs the real `InMemoryHoldQueue`, the adapter `main/wiring.ts` wires |

## Findings

### What a cancel does when the queue throws mid-remove is undecided

**Severity:** needs-decision (devsecops-engineer:reliability-requirements)
**Location:** lending/cancel-hold.ts:12
**Category:** reliability: unhandled failure path

**What's happening:** `run` awaits `queue.remove` with nothing around it; a queue that throws surfaces as a rejected promise with the adapter's own error. The slice says an unreachable queue is "a failure the caller sees", and `reliability-slice-001.md` says it is not retried inside the use case, but no document says what shape that failure takes (a thrown error, a third status) or whether a failure that happens after the hold was removed counts as removed.

**Why it matters:** chunk 2 builds this path; a fixer cannot rate the current behaviour without the rule.

**Suggested fix:** `devsecops-engineer` decides, in `reliability-slice-001.md`: the result shape for an unreachable queue, and whether a failure after removal is reported as cancelled or as failed.

### The rejection reason carries the member's full card number

**Severity:** Medium
**Location:** lending/cancel-hold.ts:14
**Category:** reliability: sensitive data in a message

**What's happening:** `reason` is built as `card ${cardNumber} has no hold on ${isbn}`; the whole card number goes into a string that reaches the desk screen and, once the route exists, the logs.

**Why it matters:** the card number identifies the member everywhere else in the service; a message meant to be read aloud at the desk should not carry it whole.

**Suggested fix:** show only the last four digits (`card ending 4444`), and pin it with a test.

Counts: C0 H0 M1, needs-decision 1.
