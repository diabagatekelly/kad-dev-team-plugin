
### Chunk 1: Cancel a member's hold on a title
- **Built**: `HoldQueue.remove(isbn, cardNumber)` on the port, implemented by `InMemoryHoldQueue` (removes the first hold with that card number on that title, drops the title's entry when empty); `CancelHold.run(isbn, cardNumber)` returning `{status: 'cancelled'}` or `{status: 'rejected', reason}`; five tests, the seam test through the real in-memory queue first.
- **Decided**: the rejection reason names the card and the ISBN; the design leaves the wording open and the requirement only asks for a reason.
- **Escalated**: none
- **Deviation**: @DEVIATION@
- **Commit**: this commit; 7 tests green
