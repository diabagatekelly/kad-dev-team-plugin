# Synthesis: product-slicer

Internal only — never referenced from `agents/product-slicer/AGENT.md` or
any of its backing skills. Delete once the full roster is built.

Output was later split from one `skills/product-slicer/SKILL.md` into two
skills: `vertical-slicing` (everything that serves cutting/defending one
slice — not further split, since those parts are used together, not
independently) and `acceptance-criteria` (genuinely standalone — usable
without a slice in play). The principle table below still reflects the
original research; it's unaffected by that split.

## Sources consulted

1. **Flexion plugin** — `flexion-product-base/skills/user-story-writer/SKILL.md`,
   its `references/vertical-slicing-philosophy.md`, `examples/good-vertical-slice.md`,
   `examples/bad-horizontal-slice.md`, `examples/good-example-case-search-preferences.md`,
   `assets/user-story-template.md`. Skimmed `technical-task-writer/SKILL.md` +
   `assets/definition-of-done.md`.
2. **Personal skills** — checked `~/.claude/skills/code-review`, `tests-audit`,
   `coach` — **none cover slicing or acceptance criteria**; no personal
   material to draw on here, noted rather than fabricated.
3. **CAMS** — `cams-vertical-slicing/SKILL.md`, `cams-acceptance-criteria/SKILL.md`.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| A slice cuts through all layers, isn't a task list | own draft; flexion vertical-slicing-philosophy; cams-vertical-slicing | already-covered |
| Pick the smallest slice that resolves/defers open questions from the problem doc | own draft | already-covered |
| Feature-shape YAGNI: too big vs. too thin to demo | own draft | already-covered |
| Given/When/Then, concrete and testable | own draft | already-covered |
| **AC pitfall: specifies HOW not WHAT** (implementation leaking into criteria) | cams-acceptance-criteria Procedure 3; flexion "Bad Examples" (Kafka, Apache config) | **gap → added** |
| **AC pitfall: happy-path-only**, missing error/edge coverage | cams-acceptance-criteria Procedure 3 | **gap → added** |
| **AC pitfall: overly prescriptive UI detail** (colors, pixel sizes, timing) | cams-acceptance-criteria Procedure 3; flexion "Anti-Pattern: Prescriptive Acceptance Criteria" | **gap → added** |
| **AC pitfall: criteria contradict each other** | cams-acceptance-criteria Procedure 3 | **gap → added** |
| AC completeness checklist (happy path, authorization, validation, not-found, duplicate, concurrency) | cams-acceptance-criteria Procedure 3 Step 2 | **gap → added, generalized beyond CAMS's list** |
| Menu of slicing techniques (happy-path-first, input variations, workflow steps, reduce scope, defer non-functional) | cams-vertical-slicing Procedure 1 (technique names only — original descriptions written) | **gap → added** |
| Handling scope-creep pushback: "need error handling," "architecture requires layers," "first slice takes longer" | cams-vertical-slicing Procedure 4 (concepts only — original wording) | **gap → added** |
| Error handling itself gets tiered across slices (essential now, common next, rare later), not all-or-nothing | cams-vertical-slicing Challenge 1 | **gap → added, folds into pushback-handling** |
| Slice size is relative to team/tooling context, not an absolute minimum | flexion user-story-writer ("with AI coding assistants, teams can handle larger slices") | **gap → added as a caveat on "smallest"** |
| Shared/infra work isn't its own slice — it rides on the first slice that actually needs it | flexion vertical-slicing-philosophy ("Tasks" section); cams-vertical-slicing Challenge 3 | **gap → added to "Explicitly deferred" guidance** |
| Acceptance criteria and Definition of Done are different documents — AC is user-observable behavior, DoD is shippability (test/review/deploy readiness) | flexion vertical-slicing-philosophy + technical-task-writer/definition-of-done.md | **gap → added as a boundary note, DoD stays out of product-slicer's mandate** |
| Actor must be a real user, not "the system"/"a developer" | flexion vertical-slicing-philosophy "Bad Examples"; user-story-writer Anti-Patterns | **gap → added as a quick check** |

## Contradictions — flagged and resolved

**1. Accessibility/security timing.** Flexion is explicit and absolute:
accessibility and security must be in every slice's acceptance criteria from
the start; deferring either to a "follow-up story" is called out by name as
an anti-pattern. My original draft said to bias slice one *away from* the
riskiest unknowns (which, for the budgeting-app example, reads as
"security-engineer's concerns can wait").

These aren't actually opposed once separated: deferring an entire
**capability** that isn't in slice one yet (e.g., live bank-credential
aggregation) is fine — there's no security surface to secure until that
capability exists. But whatever a slice *does* ship must have the *need*
for security/access review flagged in that slice, not bolted on later.

Resolution folded into the skill, revised after review: product-slicer has
no security/accessibility expertise, so it doesn't author those criteria
itself — Flexion's "own it directly" reading was rejected. Instead:
add a placeholder acceptance criterion flagging what needs review, and
delegate to `security-engineer`/`accessibility-engineer` once those
personas exist to author the real criteria. Same end state as Flexion's
rule (it ends up in the AC) at lower cost today, since those personas
don't exist yet.

**2. Acceptance-criteria format rigor.** CAMS mandates strict Gherkin
(Given/When/Then, `.feature` files, no alternative format permitted) —
explicitly because of its own BDD test-pipeline integration, a CAMS-specific
tooling reason, not a universal claim. Flexion's philosophy doc uses a much
lighter bar: each AC should be phrasable as "User can `<X>`," no Gherkin
ceremony required.

Resolution: keep Given/When/Then as the default (it forces preconditions
into the open and stays testable either way), but the bar for "good enough"
is the underlying testability, not keyword-perfect Gherkin — note that a
criterion which already reads naturally as "User can X" doesn't need to be
artificially expanded into full Gherkn scenarios to satisfy this skill.

## Top gaps folded into skills/product-slicer/SKILL.md

1. Four new AC pitfalls (HOW-not-WHAT, happy-path-only, prescriptive UI,
   self-contradicting) plus a completeness checklist.
2. A concrete slicing-technique menu.
3. A pushback-handling section (error handling tiering, layered-architecture
   objection, "first slice takes longer").
4. Accessibility/security-need-flagged-from-the-start rule (placeholder +
   delegate to the owning persona, not authored directly), replacing the
   defer-everything-risky framing.
5. Real-user-actor check; infra-rides-along-with-first-need rule; AC-vs-DoD
   boundary note; slice size is context-relative.
