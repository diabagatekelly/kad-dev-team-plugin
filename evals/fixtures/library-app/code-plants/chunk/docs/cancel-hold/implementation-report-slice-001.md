# Implementation report: slice 001, staff cancel a member's hold on a title

Policy: heavy (`tdd-implementation`). Branch `slice-001-cancel-hold`.

## Chunk plan

### Chunk 1
- **Title**: Cancel a member's hold on a title
- **Delivers**: Acceptance "Given a member with a hold on a title, when it is cancelled, the hold is gone from that title's queue and the result says cancelled"; Acceptance "Given a member with no hold on a title, when cancelling is asked for, the result is a rejection with a reason, and the queue is unchanged"; Security "only the hold named by the card number and ISBN given is removed; no other member's hold on that title or any other changes"
- **Files**: lending/hold-queue.ts; lending/cancel-hold.ts; infra/memory/in-memory-hold-queue.ts; test/cancel-hold.test.ts; test/in-memory-hold-queue.test.ts
- **Done when**: `cancels the member's hold and says cancelled`, `rejects a cancel when the member has no hold on the title`, `removes only that member's hold on that title`, `in-memory queue removes one member's hold and says whether it was there` are green
- **Touches**: storage

### Chunk 2
- **Title**: Surface a queue failure without a half-removed hold
- **Delivers**: Reliability "if the hold queue can't be reached, the result is a failure the caller sees, and nothing is half-removed"
- **Files**: lending/cancel-hold.ts; test/cancel-hold.test.ts
- **Done when**: `a queue that cannot be reached fails the cancel and leaves the queue as it was` is green
- **Touches**: storage; error handling

### Chunk 3
- **Title**: Reject a second cancel of the same hold
- **Delivers**: Reliability "a cancel asked for twice in a row removes the hold once and the second request is a rejection, never an error"
- **Files**: lending/cancel-hold.ts; test/cancel-hold.test.ts
- **Done when**: `a second cancel of the same hold is a rejection, not an error` is green
- **Touches**: none
