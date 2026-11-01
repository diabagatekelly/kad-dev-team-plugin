# Test quality review: slice 001, the whole slice (round 0)

Range `@BASE@..@HEAD@`; test/cancel-hold.test.ts, test/cancel-hold-again.test.ts, test/cancel-hold-notice.test.ts, test/in-memory-hold-queue.test.ts.

## Seam check

Each chunk's seam test runs `CancelHold` over the real `InMemoryHoldQueue`, the adapter `main/wiring.ts` wires for holds; the composition root itself does not change in this slice. Satisfied.

## Fake inventory

| Double | Replaces | Verdict |
|---|---|---|
| a `HoldQueue` whose `remove` throws | the in-memory queue, for the unreachable branch | fine: named for its branch, used by two tests only |

## Padding measures

Test-to-source non-blank lines: 1.6:1. Tests asserting on source text, manifests or script bodies: 0 of 4 files.

## Findings

### `queueWith` builds every hold with the same fixed date

**Severity:** Low
**Location:** test/cancel-hold.test.ts:15
**Category:** fixture

**What's happening:** every hold is placed at the same instant, so no test can tell whether the queue's order is by position or by date.

**Why it matters:** a future ordering bug in the adapter would pass every test here.

**Suggested fix:** a clock parameter on the helper, and one test that places holds at different times.

Counts: C0 H0 M0 L1.
