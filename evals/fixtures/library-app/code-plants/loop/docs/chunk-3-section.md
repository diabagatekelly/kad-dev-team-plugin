
### Chunk 3: Reject a second cancel and give the desk its notice
- **Built**: two tests pinning that a second cancel of the same hold is a rejection through the real queue (the behaviour falls out of chunk 1); `cancelNotice(result)` in `lending/cancel-hold-notice.ts`, the heading, body and desk-screen markup for a result, with two tests.
- **Decided**: the notice markup carries its own dismiss script so the next slice's route can serve it as is.
- **Escalated**: none
- **Deviation**: none
- **Commit**: this commit; 13 tests green
