# Synthesis: docs-writer

Internal only — never referenced from `agents/docs-writer/AGENT.md` or any
of its backing skills. Delete once the full roster is built.

Output was later split from one `skills/docs-writer/SKILL.md` into six
narrow skills (`problem-framing-doc`, `adr`, `why-comments`,
`pr-issue-writeup`, `user-facing-docs`, `staleness-audit`) — see
PERSONAS.md's "one skill per trigger" convention. The principle table below
still reflects the original research; it's unaffected by that split.

## Sources consulted

1. **Flexion plugin** — `flexion-product-base/skills/user-documentation-writer/SKILL.md`
   (+ its `examples/`). Also checked `flexion-engineer-base/skills/option-enabling-architecture/SKILL.md`
   and `flexion-ai-architecture-principles/skills/architecture-principles/SKILL.md`
   for ADR content — **none found**, no conflict.
2. **Personal skills** — `~/.claude/skills/handoff/skill.md`,
   `~/Documents/LLMCourse/arabic-teaching-multi-agent/.claude/skills/clean-docs/SKILL.md`.
   Checked `~/.claude/skills/pgp-log/SKILL.md` — Flexion-specific PGP tooling
   (flexnet API, competency tags), not portable documentation practice, excluded.
3. **CAMS** — `cams-documentation/SKILL.md`, `cams-adr/SKILL.md`.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Default to no doc; ask "would losing this cost more than maintaining it" | own draft (aligned with CAMS's "Documentation LIES" mantra) | already-covered |
| WHY-not-WHAT comments, self-documenting code first | own draft; cams-documentation Procedure 2 + self-documenting principles | already-covered |
| ADR trigger = expensive-to-reverse / non-obvious | own draft | already-covered, **sharpened below** |
| ADR trigger should be a 3-part checklist: architectural scope, significant (costly to reverse / affects multiple areas / sets a standard), non-obvious | cams-adr Procedure 1 Step 1 | **gap → added** |
| ADR must never contain implementation details, code, file paths, or testing approaches — WHAT/WHY only, never HOW | cams-adr "Golden Rule" + Common Pitfalls | **gap → added** |
| ADR: check for/supersede existing ADRs rather than editing in place | own draft; cams-adr Procedure 4 | already-covered |
| Staleness/ceremony audit | own draft; cams-documentation Procedure 7 | already-covered |
| Skimmability governs every artifact | own draft (from user's pasted PR-writing principles) | already-covered |
| PR/issue descriptions: plain language, IDs on a trailing line | own draft (from user's pasted principles) | already-covered |
| **User-facing feature documentation** as a distinct artifact: benefit/WHY/WHEN-focused, not step-by-step HOW, durable against UI changes, no screenshots | flexion user-documentation-writer (entire skill) | **gap → added as artifact type 5**, decided explicitly. |
| **Session handoff doc** as a distinct artifact: freeze-frame the exact moment, WHY behind file changes (not just what changed), decisions & rejected alternatives with reasons, link to specs instead of duplicating, one file that overwrites | personal `handoff` skill | **declined, explicitly.** Continuity across sessions may be handled by beads (an external tracking tool) instead of a docs-writer artifact — not docs-writer's lane if so. |
| Docs-as-code: track documentation changes in the same PR/commit as the code | flexion user-documentation-writer | minor — already implied by "no doc drifts from the code it describes," not separately called out |

## Contradictions

None found. The one near-miss: CAMS treats API docs, README, and error-code
docs as in-scope for its documentation skill; this persona deliberately
excludes those (see PERSONAS.md's narrow-focus decision — README/API/error
docs stay out of docs-writer's mandate, revisit later if that changes).

## Top gaps folded into skills/docs-writer/SKILL.md

1. ADR decision criteria sharpened into a 3-question checklist.
2. Explicit "never HOW" rule for ADRs (no code, no file paths, no impl detail).
3. New artifact type: user-facing feature documentation.

## Considered and declined

4. Session handoff doc — a real, sourced gap (personal `handoff` skill), but
   declined: continuity across sessions may move to beads instead, which
   isn't docs-writer's lane. Not revisited unless that changes.
