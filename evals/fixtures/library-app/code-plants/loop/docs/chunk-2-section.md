
### Chunk 2: Surface a queue failure without a half-removed hold
- **Built**: a queue that throws is caught in `CancelHold.run` and returned as `{status: 'failed', reason: 'hold queue unavailable'}`, a third status the caller can tell from a rejection; two tests, the seam test (a queue that fails once, then the real in-memory queue) first.
- **Decided**: the failure is its own status rather than a rejection, so the desk can tell "no hold" from "try again"; the slice asks for a failure the caller sees.
- **Escalated**: none
- **Deviation**: none
- **Commit**: this commit; 9 tests green
