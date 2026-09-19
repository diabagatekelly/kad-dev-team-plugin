PASS

Judge agent (final run): the `case-lookup.ts` fix extracts a `CaseDirectory` interface owned by the strategic side and moves `StaffingClient` behind a new adapter implementing it, keeps `findCase`'s behavior unchanged (verified via mutation spot-checks), and walks the old SDK-mocking test through an explicit cycle that replaces it with an equivalent test through the new boundary — no unrelated changes bundled in, no new `CaseLookupService` behavior invented.
