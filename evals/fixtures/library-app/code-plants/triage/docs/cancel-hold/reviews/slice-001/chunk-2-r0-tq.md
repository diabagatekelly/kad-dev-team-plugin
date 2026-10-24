# Test-quality review: chunk 2 (round 0)

Range `4f2a9c1..9b7e2c5`; file test/cancel-hold.test.ts.

## Findings

### Low: `queueWith` builds every hold with the same fixed date
`test/cancel-hold.test.ts:11`. Fine for these tests, which never order by date; a clock parameter would let a later test pin ordering without rewriting the helper.

## Not findings
- Every test asserts through `CancelHold`'s result and the queue's public operations; nothing reads the adapter's private map.
- `a queue that cannot be reached is a rejection` uses a hand-written `HoldQueue` whose `remove` throws, so it exercises the catch for real.

Counts: C0 H0 M0 L1.
