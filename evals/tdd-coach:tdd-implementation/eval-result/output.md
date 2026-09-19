Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/tdd-implementation/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/test-quality-review/SKILL.md

*Dry run notice: per this run's instructions I'm not touching the filesystem or a real shell. Every "RED"/"GREEN" run below is narrated — what the test runner would report given the code shown at that point — not a claim that a runner actually executed. Everything else (Test List discipline, escalation calls, review passes, mutation spot-checks) is the real work product, just captured as text instead of applied to files.*

---

## Before touching code: escalations and visible assumptions

Two things came up in the task that the design doc doesn't cover, plus one I found while filling a mechanical gap. Handling each per how load-bearing it actually is:

**1. Reassignment (case already assigned to a different attorney) — not escalated as a blocker, but not silently decided either.** The design's own Decisions list only two rules: case must be "open," attorney must be "available." It says "Open questions: None recorded" — which is slightly inconsistent with the fact that this question exists at all, worth naming rather than smoothing over. Rather than inventing reassignment as a new capability (overwrite semantics, notifying the previous attorney), I'm treating "case already assigned to someone else" as **already covered for free by the existing "must be open" rule** — on the assumption that a case moves out of "open" status once it's assigned to anyone. That assumption is visible here, not buried in the diff. Two things follow from the "recognizing an existing rule already covers this" pattern that the persona treats as two separate notes, not one:
   - *No new rule needed* — an already-assigned case fails the existing open-check, no new Test List entry for "reassignment detection."
   - *Reuse-of-messaging flag, named separately* — the rejection reason this produces will be `"case not open"`, the same string used for a case that was simply never opened or already closed. That's technically true but doesn't say *why* — "already assigned to attorney X" is a different situation than "closed" or "never existed." Nothing in the design says the caller needs that distinction, so I'm not building it, but flagging it explicitly rather than letting a reused message pass as obviously correct for a case it wasn't written to describe.
   - *What's genuinely load-bearing and out of scope*: whether this slice should actually **support** reassignment (allow it, notify the outgoing attorney) is a real capability question with real alternatives, not a wording question. That's `acceptance-criteria`'s call, not mine — I'm not building notification or overwrite behavior, and I'm naming that gap rather than guessing either direction.

**2. Rejection-reason wording — not load-bearing, made the call, noting it.** Task says nothing hangs on the exact string. I'm using `"attorney not available"` (mirrors the design doc's own adjective, "available"/"not available," rather than switching to "unavailable") and `"case not open"` (mirrors "must be in 'open' status"). Assumption, stated, not escalated.

**3. Missing collaborator for "is the case open" — filled, not escalated, *but* one real structural fork inside it does get escalated.** The design says `AssignCase` "validates the case is open" but names no collaborator that reads case status — the same gap this roster's own materials use as the canonical example of "the doc implies a collaborator must exist without naming it." I'm filling it with a minimal placeholder, `CaseRepository.isOpen(caseId): boolean`, shaped exactly like `AttorneyDirectory.isAvailable(attorneyId): boolean` — same ownership (interface lives with `AssignCase`, its caller), same single-predicate shape, same convention already established in this doc. That's a naming gap, not an open fork, so I filled it rather than stopping.

   What I won't fill silently: **case-lookup.ts's finding (below) introduces `CaseDirectory`, an interface explicitly backed by the external staffing SDK, that also reads case data by `caseId`.** Is `CaseRepository.isOpen` reading the same underlying case store as `CaseDirectory.getCase`, or a genuinely separate one? If it's the same store, two independent lookups for the same entity is a coupling problem — possibly one interface, not two. That's exactly the fork this persona's own guidance calls out by name ("a second lookup for the same underlying data is a coupling question, not a naming one") as something to escalate to `architecture-design`, not decide unilaterally, while still building the minimal placeholder in parallel so `AssignCase` isn't blocked on the answer. **Escalating that question by name; building `CaseRepository` as a separate interface in the meantime is the placeholder, not the final word.**

No `AttorneyDirectoryGateway` implementation in this pass. The design names it, but the task never shows the staffing SDK's attorney-availability method — only `StaffingClient.getCase`, which is a different concern (case lookup, not attorney availability). Inventing a method name on a third-party SDK I haven't seen isn't a small gap-fill, it's a guess at an external contract. Scoping it out and flagging it rather than fabricating an SDK surface.

No commit discipline invented — the task didn't specify one for this slice, so none is assumed (per skill: "don't invent a commit discipline the project hasn't asked for").

Assumed file layout (nothing in the task implies an existing structure for this fictional slice, so I'm picking a conventional one and naming it): `src/case-assignment/AssignCase.ts` + `.test.ts`; `case-lookup.ts`/`case-lookup.test.ts` stay where the snippet found them, with a new `case-directory-gateway.ts`/`.test.ts` alongside.

---

## Part 1 — `AssignCase`

### Test List (written before the first RED)

1. Rejects when the case is not open — and never consults attorney availability (short-circuit; this is the design's own "Importance ordering assumed" section made concrete: the business rule must not depend on reaching the swappable external lookup). Also the scenario that absorbs "already assigned to someone else," per the escalation note above — no separate entry for that.
2. Rejects when the case is open but the attorney is not available.
3. Assigns when the case is open and the attorney is available.

That's the full list — both approved Decisions, plus the one ordering property the design doc explicitly names as an assumption worth preserving. Nothing speculative added.

### Cycle 1 — case not open

**RED**

```ts
// src/case-assignment/AssignCase.test.ts
import { AssignCase, CaseRepository, AttorneyDirectory } from './AssignCase';

function makeAssignCase(overrides: { isOpen?: boolean; isAvailable?: boolean } = {}) {
  const caseRepository: CaseRepository = {
    isOpen: jest.fn().mockReturnValue(overrides.isOpen ?? true),
  };
  const attorneyDirectory: AttorneyDirectory = {
    isAvailable: jest.fn().mockReturnValue(overrides.isAvailable ?? true),
  };
  const assignCase = new AssignCase(caseRepository, attorneyDirectory);
  return { assignCase, caseRepository, attorneyDirectory };
}

describe('AssignCase', () => {
  it('rejects when the case is not open, without checking attorney availability', () => {
    const { assignCase, attorneyDirectory } = makeAssignCase({ isOpen: false });

    const result = assignCase.execute('case-1', 'attorney-1');

    expect(result).toEqual({ status: 'rejected', reason: 'case not open' });
    expect(attorneyDirectory.isAvailable).not.toHaveBeenCalled();
  });
});
```

Running this now: fails with `Cannot find module './AssignCase'` — no implementation file exists yet. Right reason (missing implementation), not a typo or bad setup. Confirmed RED.

**GREEN**

```ts
// src/case-assignment/AssignCase.ts
export interface CaseRepository {
  isOpen(caseId: string): boolean;
}

export interface AttorneyDirectory {
  isAvailable(attorneyId: string): boolean;
}

export interface AssignmentResult {
  status: 'assigned' | 'rejected';
  reason?: string;
}

export class AssignCase {
  constructor(
    private readonly caseRepository: CaseRepository,
    private readonly attorneyDirectory: AttorneyDirectory
  ) {}

  execute(caseId: string, attorneyId: string): AssignmentResult {
    if (!this.caseRepository.isOpen(caseId)) {
      return { status: 'rejected', reason: 'case not open' };
    }
    return { status: 'assigned' };
  }
}
```

The `{status: 'assigned'}` fallback past the guard is the minimum that compiles and satisfies the one active test — nothing about attorney availability is built yet because no test requires it.

Running the suite: 1 test, 1 pass. Confirmed GREEN.

**REFACTOR:** nothing to restructure — one guard clause, no duplication yet. Skipped for this cycle.

**REVIEW — `test-quality-review`, inline:** Read the test and `AssignCase.ts`. Both collaborators are constructor-injected test doubles standing in for genuine external dependencies (`AttorneyDirectory`, `CaseRepository`) — normal test infrastructure, not a violation. One judgment call worth naming rather than waving through silently: `expect(attorneyDirectory.isAvailable).not.toHaveBeenCalled()` is a call-count assertion, which is usually the shape of an implementation-detail finding ("would this break from a refactor that changed nothing about output?" — yes, it would, if a future refactor called `isAvailable` and discarded the result). I'm keeping it anyway because the design doc names this ordering as an explicit architectural decision ("swapping the lookup system wouldn't change assignment rules"), not incidental structure — it's a real promise of this unit, not how it happens to be coded today. Flagging that reasoning explicitly rather than let it pass as an unexamined pattern. No Critical/High findings. **PASS.**

### Cycle 2 — attorney not available

**RED**

```ts
it('rejects when the case is open but the attorney is not available', () => {
  const { assignCase } = makeAssignCase({ isOpen: true, isAvailable: false });

  const result = assignCase.execute('case-1', 'attorney-1');

  expect(result).toEqual({ status: 'rejected', reason: 'attorney not available' });
});
```

Running now: with the current implementation, `isOpen: true` skips the only guard and falls through to `{status: 'assigned'}`. Actual `{status: 'assigned'}` vs. expected `{status: 'rejected', reason: 'attorney not available'}` — assertion mismatch. Right reason, confirmed RED.

**GREEN**

```ts
execute(caseId: string, attorneyId: string): AssignmentResult {
  if (!this.caseRepository.isOpen(caseId)) {
    return { status: 'rejected', reason: 'case not open' };
  }
  if (!this.attorneyDirectory.isAvailable(attorneyId)) {
    return { status: 'rejected', reason: 'attorney not available' };
  }
  return { status: 'assigned' };
}
```

Running the suite: 2 tests, 2 pass.

**REFACTOR:** two structurally identical rejection branches now exist — bounded, worth extracting while I'm here:

```ts
private reject(reason: string): AssignmentResult {
  return { status: 'rejected', reason };
}
```

with both guards calling `this.reject(...)`. Re-ran the suite after this step: still 2/2 green, no behavior touched — pure structure.

**REVIEW — inline:** Both branches now exercised by distinct tests with exact-value (`toEqual`) assertions, not loose bound checks. No excessive mocking (still exactly two collaborators, both legitimate). No wrong-boundary reach into either double's internals. **PASS.**

### Cycle 3 — assigned

**RED (attempted)**

```ts
it('assigns when the case is open and the attorney is available', () => {
  const { assignCase } = makeAssignCase({ isOpen: true, isAvailable: true });

  const result = assignCase.execute('case-1', 'attorney-1');

  expect(result).toEqual({ status: 'assigned' });
});
```

Running this against the current implementation: it **passes immediately** — no code change needed. Both guards evaluate false, execution falls through to `{status: 'assigned'}`, which is exactly what's expected. This isn't a shortcut I'm taking; it's the honest result of running it, worth reporting as-is rather than performing a fake failure. It happens here because cycle 2's fallback already generalized to the correct final behavior, not because I wrote the test loosely — the assertion is exact (`toEqual`, not a truthy check).

**GREEN:** no change required.

Running the full suite: 3 tests, 3 pass.

**REFACTOR:** naming the two magic strings, since they now appear in both branches and the test file:

```ts
const CASE_NOT_OPEN = 'case not open';
const ATTORNEY_NOT_AVAILABLE = 'attorney not available';

export class AssignCase {
  constructor(
    private readonly caseRepository: CaseRepository,
    private readonly attorneyDirectory: AttorneyDirectory
  ) {}

  execute(caseId: string, attorneyId: string): AssignmentResult {
    if (!this.caseRepository.isOpen(caseId)) {
      return this.reject(CASE_NOT_OPEN);
    }
    if (!this.attorneyDirectory.isAvailable(attorneyId)) {
      return this.reject(ATTORNEY_NOT_AVAILABLE);
    }
    return { status: 'assigned' };
  }

  private reject(reason: string): AssignmentResult {
    return { status: 'rejected', reason };
  }
}
```

Re-ran the suite: 3/3 still green, no behavior changed.

**REVIEW — inline, full file now that the list is exhausted:** Missing-coverage check: the fourth logical combination (case not open + attorney available) doesn't need its own test — cycle 1 already proves `isAvailable` is never even called in the not-open case, so that combination collapses into cycle 1's coverage, not a gap. Dependency-rule check: `AssignCase.ts` imports nothing beyond its own interfaces — no tactical/SDK import anywhere in the strategic file. **PASS**, nothing Critical/High/Medium outstanding beyond the ordering-assertion note already logged in cycle 1.

### Completion — false-positive spot-check

Before calling this goal done, three targeted mutations, each reverted immediately after confirming the expected failure:

- Flipped `!this.caseRepository.isOpen(caseId)` to drop the negation → cycle-1 test failed (case falsely treated as open) → confirms the guard is load-bearing → reverted.
- Flipped `!this.attorneyDirectory.isAvailable(attorneyId)` the same way → cycle-2 test failed → reverted.
- Typo'd `ATTORNEY_NOT_AVAILABLE` to `'attorney unavailable'` → cycle-2 test failed on the exact-string `toEqual` → confirms the assertion isn't a loose match doing nothing → reverted.

**On completion:** Test List exhausted (3/3), full suite green (3 tests), coverage is 100% of both branches by construction (every branch has a driving test, nothing padded after the fact), `test-quality-review` run inline after every cycle with nothing Critical/High outstanding (one Low-severity judgment call logged and justified, not silently passed), spot-check done. `AttorneyDirectoryGateway` intentionally not built this pass — scoped out above, not silently dropped.

---

## Part 2 — `case-lookup.ts` Dependency Rule fix

This is a named fix handed back from `architecture-review`, so it goes through the same loop: confirm current state, make the change, re-verify green — not a special-cased patch.

**Starting point.** The task describes but doesn't show `case-lookup.test.ts` verbatim ("mocks `StaffingClient` directly today"). Reconstructing its likely shape from that description and the given source, to establish a baseline — flagging this as an inference, not literal given content:

```ts
// case-lookup.test.ts — existing, before the fix (reconstructed)
import { StaffingClient } from 'staffing-sdk';
import { CaseLookupService } from './case-lookup';

jest.mock('staffing-sdk');

describe('CaseLookupService', () => {
  it('returns the case from the staffing client', async () => {
    const mockCase = { id: 'case-1', name: 'Test Case' };
    const getCase = jest.fn().mockResolvedValue(mockCase);
    (StaffingClient as jest.Mock).mockImplementation(() => ({ getCase }));

    const service = new CaseLookupService();
    const result = await service.findCase('case-1');

    expect(result).toEqual(mockCase);
    expect(getCase).toHaveBeenCalledWith('case-1');
  });
});
```

Running this as-is against the current `case-lookup.ts`: 1 test, 1 pass. Baseline confirmed green.

### Test List for the fix

1. `CaseLookupService.findCase` delegates to an injected `CaseDirectory` and returns its result — replaces the SDK-mocking test with one that goes through the boundary the fix creates. Same observable behavior, verified correctly instead of by mocking the SDK directly.
2. `CaseDirectoryGateway.getCase` delegates to `StaffingClient.getCase` and returns its result — the only place `StaffingClient` still gets mocked, because it's now the only place that imports it.
3. Retire the old SDK-mocking test in `case-lookup.test.ts` once (1) covers the same guarantee — not left in place disabled, and not left in place still mocking a dependency `CaseLookupService` no longer has (that would become exactly the "mock that doesn't intercept anything" pattern once the import moves).

Not on this list: a dedicated test asserting `STAFFING_API_KEY` is passed into `StaffingClient`'s constructor. The reconstructed original test didn't assert on that either, and the fix only relocates that exact line into the gateway — it's a structural move, not new behavior needing new coverage. Adding one now would be coverage the task didn't ask for.

### Cycle 1 — `CaseLookupService` via injected `CaseDirectory`

**RED**

```ts
// case-lookup.test.ts — new
import { CaseLookupService, CaseDirectory } from './case-lookup';

describe('CaseLookupService', () => {
  it('returns the case from its CaseDirectory', async () => {
    const mockCase = { id: 'case-1', name: 'Test Case' };
    const caseDirectory: CaseDirectory = {
      getCase: jest.fn().mockResolvedValue(mockCase),
    };
    const service = new CaseLookupService(caseDirectory);

    const result = await service.findCase('case-1');

    expect(result).toEqual(mockCase);
    expect(caseDirectory.getCase).toHaveBeenCalledWith('case-1');
  });
});
```

Running against today's `case-lookup.ts`: fails to compile — `CaseDirectory` isn't exported, and `CaseLookupService`'s constructor takes no parameters. Right reason (missing implementation / type mismatch). Confirmed RED.

**GREEN**

```ts
// case-lookup.ts — strategic side, fixed
export interface CaseDirectory {
  getCase(caseId: string): Promise<unknown>;
}

export class CaseLookupService {
  constructor(private readonly caseDirectory: CaseDirectory) {}

  async findCase(caseId: string) {
    return this.caseDirectory.getCase(caseId);
  }
}
```

Running the new test: pass. Running the *old* SDK-mocking test against this same file: now fails to compile — `new CaseLookupService()` with zero arguments no longer satisfies the constructor. That's expected and is exactly why cycle 3 (retire it) exists — not an unrelated regression, the direct consequence of the fix the old test was never structured to survive.

### Cycle 2 — `CaseDirectoryGateway`

**RED**

```ts
// case-directory-gateway.test.ts
import { StaffingClient } from 'staffing-sdk';
import { CaseDirectoryGateway } from './case-directory-gateway';

jest.mock('staffing-sdk');

describe('CaseDirectoryGateway', () => {
  it('delegates getCase to the staffing client', async () => {
    const mockCase = { id: 'case-1', name: 'Test Case' };
    const getCase = jest.fn().mockResolvedValue(mockCase);
    (StaffingClient as jest.Mock).mockImplementation(() => ({ getCase }));

    const gateway = new CaseDirectoryGateway();
    const result = await gateway.getCase('case-1');

    expect(result).toEqual(mockCase);
    expect(getCase).toHaveBeenCalledWith('case-1');
  });
});
```

Running now: fails — `./case-directory-gateway` doesn't exist yet. Right reason, confirmed RED.

**GREEN**

```ts
// case-directory-gateway.ts — the only file that imports staffing-sdk
import { StaffingClient } from 'staffing-sdk';
import { CaseDirectory } from './case-lookup';

export class CaseDirectoryGateway implements CaseDirectory {
  private readonly client = new StaffingClient(process.env.STAFFING_API_KEY);

  async getCase(caseId: string) {
    return this.client.getCase(caseId);
  }
}
```

Running: pass. Running everything together: new `case-lookup.test.ts` test — pass; new `case-directory-gateway.test.ts` test — pass; old SDK-mocking test — still broken as expected, pending cycle 3.

**REFACTOR:** both classes are minimal, single-method, single-responsibility — nothing to restructure.

**REVIEW — inline, cycles 1-2:** `CaseDirectoryGateway`'s mock of `StaffingClient` is the one place in the codebase where mocking that SDK is still correct — it's the adapter whose entire job is wrapping it. `CaseLookupService`'s new test stubs `CaseDirectory`, a boundary it owns, not an SDK it no longer touches. Flagging the old broken test explicitly as a known, pending item rather than a silently-ignored failure — it gets resolved next, not left red. **PASS** on the new code; the known-broken old test is tracked, not swept under.

### Cycle 3 — retire the old test

Removed the SDK-mocking test from `case-lookup.test.ts`; it's superseded by cycle 1's test, which verifies the same guarantee ("`findCase` returns what the case source provides, called with the right id") through the boundary that now actually exists — not deleted without replacement, and not left disabled/commented out as dead weight.

Running the full suite across both files: `case-lookup.test.ts` — 1 test, pass; `case-directory-gateway.test.ts` — 1 test, pass. 2 total, 2 passing, 0 failing, 0 skipped.

**REVIEW — inline, final pass on the fix:** Re-read all four files. No mocking-the-subject, no excessive mocking (one stub per test), assertions are behavior-level (return value + forwarded argument), not internal state. Dependency check: `case-lookup.ts` no longer imports `staffing-sdk` at all — confirmed by inspection, only `case-directory-gateway.ts` does now. Import direction: `case-directory-gateway.ts` (tactical) imports both the SDK and the `CaseDirectory` interface it implements (owned by strategic `case-lookup.ts`) — correct direction, tactical depends inward and outward-to-framework, strategic depends on neither. Finding resolved. **PASS.**

### Completion — false-positive spot-check

- Changed `CaseLookupService.findCase` to return a hardcoded literal instead of delegating → cycle-1 test failed (returned value no longer matched the stub's mock case) → reverted.
- Changed `CaseDirectoryGateway.getCase` to call `this.client.getCase('wrong-id')` instead of forwarding `caseId` → cycle-2 test's `toHaveBeenCalledWith('case-1')` failed → reverted.

**On completion:** findCase's observable behavior is unchanged (same input, same output, same delegation-and-return shape) — only how it gets there changed, which was the entire point. Constructor signature did change (now requires a `CaseDirectory`), which is unavoidable to extract the interface at all; flagging explicitly that whatever composition root currently calls `new CaseLookupService()` needs a one-line update to `new CaseLookupService(new CaseDirectoryGateway())` — that call site wasn't shown in the task, so I'm naming exactly what needs to change rather than guessing at unseen code or silently leaving it broken.

---

## Summary of what's built vs. escalated

**Built:** `AssignCase` (3/3 tests green, both approved Decisions plus the design's stated ordering property), `CaseRepository` interface (minimal placeholder, named), the `case-lookup.ts` Dependency Rule fix (`CaseDirectory` interface + `CaseDirectoryGateway` adapter, old SDK-mocking test retired, 2/2 tests green, import direction verified).

**Not built, scoped out with reasons stated above:** `AttorneyDirectoryGateway` (would require guessing an unseen SDK method), reassignment/notification behavior (real capability question, not this persona's call).

**Escalations to carry forward, by name:**
- To `architecture-design`: does `CaseRepository.isOpen` (AssignCase's case-status check) read the same underlying case data as `CaseDirectory.getCase` (now backed by the staffing SDK via `CaseDirectoryGateway`)? If yes, two independent lookups for one entity is a coupling problem worth collapsing into one interface — not decided here, `CaseRepository` built as a separate placeholder in the meantime so `AssignCase` isn't blocked.
- To `acceptance-criteria`: does this slice support reassignment as a capability (overwrite an existing assignment, notify the outgoing attorney)? Currently an already-assigned case is rejected under the existing "case not open" rule with no reassignment-specific behavior — flagged as reused messaging, not a decision that reassignment is out of scope forever.
- Not escalated, but visible: whoever wires `CaseLookupService` in production needs to update its call site to pass a `CaseDirectoryGateway` now that the constructor requires one.
