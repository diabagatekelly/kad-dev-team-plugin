---
name: tdd-coach:tdd-implementation
tags: [tdd-coach, tdd-implementation]
runs: 3
---

Design's approved for the case-assignment slice. Implement `AssignCase`
via TDD. Design doc (already approved, don't redecide it):

```markdown
# Design: Case Assignment

## Importance ordering assumed
Business rules for who can be assigned a case outrank the external
attorney-availability lookup — swapping that lookup system wouldn't
change assignment rules.

## Structure
- `AssignCase` (strategic) — validates the case is open, checks attorney
  availability, assigns, returns a result.
- `AttorneyDirectory` interface (strategic, owned by `AssignCase`) —
  `isAvailable(attorneyId): boolean`.
- `AttorneyDirectoryGateway` (tactical) — implements `AttorneyDirectory`,
  calls the external staffing system's SDK.

## Boundaries and interfaces
`AssignCase.execute(caseId: string, attorneyId: string): AssignmentResult`.
`AssignmentResult` is plain data: `{ status: "assigned" | "rejected",
reason?: string }`. `AttorneyDirectory` is owned by `AssignCase` (interface
lives with its caller); `AttorneyDirectoryGateway` implements it and is
the only place that imports the staffing SDK.

## Third-party isolation
The staffing SDK is isolated entirely behind `AttorneyDirectoryGateway`.

## Decisions
- A case must be in "open" status to be assigned. Approved.
- The attorney must be "available" per `AttorneyDirectory`. Approved.

## Open questions
None recorded.
```

Two things came up that the design doc doesn't cover:

1. What should happen if `caseId` refers to a case that's already assigned
   to a *different* attorney (not the one in this call)? Nobody's decided
   whether this slice supports reassignment at all, whether the previous
   attorney needs to be notified, or whether it's even in scope.
2. What exact string should the rejection reason use when the attorney
   isn't available — `"attorney unavailable"` vs. `"attorney not
   available"` vs. something else? Nothing hangs on the exact wording.

Separately, `architecture-review` flagged something unrelated but already
in this codebase, in `case-lookup.ts`:

```typescript
// case-lookup.ts
import { StaffingClient } from 'staffing-sdk';

export class CaseLookupService {
  private client = new StaffingClient(process.env.STAFFING_API_KEY);

  async findCase(caseId: string) {
    return this.client.getCase(caseId);
  }
}
```

**Finding:** `CaseLookupService` directly imports `staffing-sdk`'s
`StaffingClient` instead of depending on an interface owned by the
strategic side — a Dependency Rule violation. There's an existing test,
`case-lookup.test.ts`, covering `findCase`'s current behavior (it mocks
`StaffingClient` directly today). Apply the fix: extract an interface
owned by the strategic side, move the SDK import behind an adapter that
implements it, and don't change `findCase`'s observable behavior.

Implement both. Show your actual work — the Test List, each test, each
implementation, and what running them told you — not just a summary of
what you'd do.
