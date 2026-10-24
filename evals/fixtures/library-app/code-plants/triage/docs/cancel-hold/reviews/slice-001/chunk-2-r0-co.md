# Code review: chunk 2, Keep a repeated or failed cancel from erroring (round 0)

Range `4f2a9c1..9b7e2c5`; files lending/cancel-hold.ts, test/cancel-hold.test.ts.

## Findings

### Low: `reason` is optional on both statuses
`lending/cancel-hold.ts:3`. `CancelHoldResult` lets a cancelled result carry a reason and a rejected one omit it. A discriminated union (`{status: 'cancelled'} | {status: 'rejected'; reason: string}`) would make the shape a type fact. Low: every caller today is a test.

## Not findings
- Naming: `run` matches `PlaceHold.run`, `RenewLoan.run` and `ReturnBook.run`; the project's use cases all expose `run`.
- The comment on the catch explains why the two cases share a shape (a WHY comment), so it earns its place.

Counts: C0 H0 M0 L1.
