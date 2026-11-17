# Combined chunk review: chunk 1, fix round 1

Range `@C1@..@F1@` (the fix's diff only); files lending/cancel-hold.ts, test/cancel-hold.test.ts; lenses `code-review`, `test-quality-review`, `reliability-review`.

## Fake inventory

| Double | Replaces | Verdict |
|---|---|---|
| none | — | the new test runs the real `InMemoryHoldQueue` |

## Findings

### A cancel for one card removes another member's hold

**Severity:** High
**Location:** infra/memory/in-memory-hold-queue.ts:29
**Category:** code: wrong match

**What's happening:** not in the fix's diff, seen while running its new test against the real queue: `remove` finds the hold with `hold.cardNumber.startsWith(cardNumber)`, so a cancel for card `10` removes the hold of card `1001` when that one is ahead in the queue. Run: enqueue a hold for `1001`, cancel for `10` on the same ISBN, and the queue is empty.

**Why it matters:** staff cancel one member's hold and another member loses their place, with a "Hold cancelled" answer.

**Suggested fix:** compare the whole card number, and add a test with two cards where one is the start of the other.

Counts: C0 H1 M0.
