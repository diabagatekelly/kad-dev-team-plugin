---
type: llm
criteria: |
  PASS only if the `case-lookup.ts` fix is applied as a structural change
  (extract an interface owned by the strategic side, move `StaffingClient`
  behind an adapter implementing it) with `findCase`'s observable behavior
  unchanged, and the response explicitly re-runs/re-verifies
  `case-lookup.test.ts` (updating its mock to target the new adapter
  boundary if needed) rather than skipping verification because "it's
  just a refactor." The response should not invent new behavior for
  `CaseLookupService` while making this change, and should not require a
  brand-new failing test to justify the extraction itself, since no new
  behavior is being added. FAIL if the fix changes `findCase`'s behavior,
  if it's applied without re-verifying the existing test, or if it's
  bundled with unrelated changes to the same file.
focus: last_message
---

Checks a reviewer-named fix is applied through the same discipline
(verified before and after, behavior-preserving) rather than as a
free-form patch, and that a structural-only fix is correctly recognized
as REFACTOR work rather than requiring an invented new test.
