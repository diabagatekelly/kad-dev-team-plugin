# Implementation report: slice 001, staff cancel a member's hold on a title

Policy: lite (`tdd-implementation-lite`). Branch `slice-001-cancel-hold`, base `7d1f0a2`.

## Chunk plan

### Chunk 1
- **Title**: Cancel a member's hold on a title
- **Delivers**: Acceptance "Given a member with a hold on a title, when it is cancelled, the hold is gone from that title's queue and the result says cancelled"; Acceptance "Given a member with no hold on a title, when cancelling is asked for, the result is a rejection with a reason, and the queue is unchanged"; Security "only the hold named by the card number and ISBN given is removed"
- **Files**: lending/hold-queue.ts; lending/cancel-hold.ts; infra/memory/in-memory-hold-queue.ts; test/cancel-hold.test.ts
- **Done when**: `cancels the member's hold and says cancelled`, `rejects a cancel when the member has no hold on the title`, `removes only that member's hold on that title` are green
- **Touches**: storage

### Chunk 2
- **Title**: Keep a repeated or failed cancel from erroring
- **Delivers**: Reliability "a cancel asked for twice in a row removes the hold once and the second request is a rejection, never an error; if the hold queue can't be reached, the result is a failure the caller sees, and nothing is half-removed"
- **Files**: lending/cancel-hold.ts; test/cancel-hold.test.ts
- **Done when**: `a second cancel of the same hold is a rejection, not an error`, `a queue that cannot be reached is a rejection` are green
- **Touches**: storage; error handling

### Chunk 1: Cancel a member's hold on a title
- **Built**: `HoldQueue.remove(isbn, cardNumber)` on the port, implemented by `InMemoryHoldQueue` (removes the first hold with that card number on that title, drops the title's entry when empty); `CancelHold.run(isbn, cardNumber)` returning `{status: 'cancelled'}` or `{status: 'rejected', reason}`; three tests.
- **Decided**: the rejection reason names the card and the ISBN ("card 1001 has no hold on 9780140449136"); the design leaves the wording open and the requirement only asks for a reason.
- **Escalated**: none.
- **Deviation**: none.
- **Commit**: `c81e3d7`
- **Fix r1**: `4f2a9c1`; Mask the card number in the rejection reason (security-review, Medium: a full card number in a message that reaches logs and the screen)

### Chunk 2: Keep a repeated or failed cancel from erroring
- **Built**: a second cancel falls out of chunk 1 (the hold is gone, so the queue says false and the result is a rejection); a queue that throws is caught in `CancelHold.run` and returned as a rejection with the fixed reason "hold could not be cancelled"; two tests.
- **Decided**: a queue failure is reported with the same `rejected` shape as a missing hold so the staff screen has one message shape to render; the reason text tells them apart.
- **Escalated**: none.
- **Deviation**: none.
- **Commit**: `9b7e2c5`

### Lows
- test/cancel-hold.test.ts:11 `queueWith` builds holds with a fixed date; a clock parameter would let a test pin ordering (test-quality-review)
- lending/cancel-hold.ts:7 `reason` is optional on both statuses; a discriminated union would make "cancelled has no reason" a type fact (code-review)
