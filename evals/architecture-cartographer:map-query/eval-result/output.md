Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/.claude/worktrees/agent-a82f481ca094c6e7c/skills/map-query/SKILL.md

# Map queries (3), against the persisted map supplied inline

**Map status for all three queries below:** current as of 2026-08-02 (53 days before today, 2026-09-24). Possibly stale: a teammate reports a branch adding a `RefundLedger` module finished yesterday and hasn't gone through `map-update` yet — the map's own "Changes since the prior map" section only documents the case-assignment slice, consistent with that. `map-query` is read-only against what's already persisted and never live-scans the codebase, so `RefundLedger`'s shape can't be checked against any of these three questions from here — if it matters, that needs a `map-update` run first.

---

## Map query: persist and retrieve court-order records tied to a case

**Granularity:** structural
**Map status:** current as of 2026-08-02; possibly stale (see note above — unrelated to this query on the facts recorded, but the map is incomplete relative to yesterday's merge)

**Candidates found:**
- domain/case-directory.types.ts (tier: tier 1) — exports: `CaseDirectory` (interface), `CaseSummary`; shares: defines an interface-level boundary for records tied to a case, consumed by both a tier-1 domain module and a tier-3 infra adapter
- domain/case-directory.ts (tier: tier 1) — exports: `CaseDirectory`, `findCaseById`, `listCasesByStatus`; shares: a find-by-id / list-by-status query boundary over case-tied records
- infra/mongo-case-directory.ts (tier: tier 3) — imports domain/case-directory.types.ts; external package mongodb; exports: `MongoCaseDirectory`; shares: the persistence-adapter half of the same boundary — a concrete store implementing the domain interface above

---

## Map query: OrderRepository — find a record by ID, list records by status

**Granularity:** implementation
**Map status:** current as of 2026-08-02; possibly stale (see note above)

**Candidates found:**
- domain/case-directory.ts (tier: tier 1) — exports: `findCaseById`, `listCasesByStatus`, `CaseDirectory`; shares: exported function names shaped as find-by-id and list-by-status, the same two method shapes described for `OrderRepository`
- domain/case-directory.types.ts (tier: tier 1) — exports: `CaseDirectory` (interface), `CaseSummary`; shares: an interface named `CaseDirectory` playing the same repository-for-case-tied-records role described for `OrderRepository`
- infra/mongo-case-directory.ts (tier: tier 3) — exports: `MongoCaseDirectory`; shares: a concrete class implementing that interface against a real store, the same shape a concrete `OrderRepository` implementation would take

---

## Map query: helper that renders a case summary as a downloadable PDF

**Granularity:** implementation
**Map status:** current as of 2026-08-02; possibly stale (see note above)

**Nothing comparable found in the map.** No recorded export in any module references PDF generation, document rendering, or downloadable output. The two exports closest in subject matter — `ui/case-list-view.tsx`'s `CaseListView` (tier 3, renders case data via react) and `infra/notification-client.ts`'s `sendAssignmentEmail` (tier 3, sends via @sendgrid/mail) — don't share the recorded shape or purpose being asked about (one renders a list to UI, not a single-case summary to a document; the other sends email, not a file), so neither is reported as a candidate.

---

Handed back for architecture-design / tdd-implementation to judge fit, not for me to rank or verdict.
