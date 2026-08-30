# Synthesis: orchestrator

Internal only — never referenced from `skills/orchestrator/SKILL.md`. Delete
once the full roster is built.

Scoped to v1 only: sequential stage-routing between planning-phase personas
(`docs-writer`, `product-slicer`) that already exist. Parallel review
synthesis across execution-phase personas (`code-reviewer`,
`security-engineer`, `tdd-coach`, etc.) is a different problem, deferred
until those personas exist — see "Declined for v1" below.

## Sources consulted

1. **Flexion plugin** — `flexion-engineer-base/skills/orchestrator/SKILL.md`
   (full skill, ~880 lines).
2. **Personal skills** — `~/.claude/skills/handoff/skill.md`,
   `~/.claude/skills/deep-pr-review/SKILL.md`.
3. **CAMS** — `cams-workflow-tracking/SKILL.md` (phase/slice state machine +
   progress-file pattern), skimmed `cams-new-feature/SKILL.md` for the phase
   structure it tracks.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Orchestrator is a **skill the main agent loads**, not a spawnable agent — it changes the main agent's own behavior rather than delegating to a separate process | Flexion orchestrator (it's `skills/orchestrator/`, despite the name) | **adopted**, and load-bearing here for a reason Flexion's version doesn't share: both `docs-writer` and `product-slicer` are `background: false` — they block on `AskUserQuestion` and must run inline, never as async `Agent` spawns. An orchestrator that tried to launch them the way Flexion launches impl/review subagents would violate that rule outright, not just be a style mismatch. |
| Identify current position → decide one next step → execute it → report → stop (don't blitz an entire multi-stage pipeline unattended) | own draft, informed by Flexion's per-goal loop structure (goal → execute → review → next goal) with the parallel-subagent mechanics stripped out | **adopted**, adapted |
| Explicit "when NOT to orchestrate" gate — trivial/single-domain tasks bypass the router | Flexion orchestrator "When NOT to Use This Skill" | **adopted** |
| Stage/phase state machine: one-time upfront stage, then a repeating per-unit loop | CAMS `cams-workflow-tracking` (Phase 1 once → Phase 2/3 loop per slice) | **adopted**, maps directly onto this roster's own shape: problem-framing-doc (once) → scope-map (once, occasionally revised) → per-step slicing (repeating) |
| Durable state tracked in a dedicated, hand-maintained progress file, updated after every transition | CAMS `cams-workflow-tracking` (`.workflow-progress.md`) | **declined, resolved differently** — see Contradictions below |
| Fixed, hardcoded artifact directory convention (CAMS: `.ustp-cams-fdp/ai/specs/<TICKET>_<feature-name>/`) | CAMS `cams-workflow-tracking` Procedure 1 | **declined** — CAMS can hardcode a path because it's a single-project plugin; this roster is explicitly portable (see PERSONAS.md's design conventions), and a fixed path would either collide with how a given project already organizes docs or force one convention on every project it's installed into. Resolved instead as a parameter-or-ask contract: `orchestrator` is invoked with the artifacts directory as a parameter, or not — given one, that's the target, no second-guessing; not given one, it asks once and passes the answer to whichever persona it invokes. Deliberately **not** "search the project for existing artifacts first" — that was an earlier draft of this same decision, reverted because "somewhere findable" is an unbounded, unspecified search (findable how? how deep? by what means?) where a single upfront question is simpler and just as cheap. A persona invoked directly (bypassing orchestrator) follows the same rule: given-or-implied, else ask — never search instead of asking. |
| Freeze-frame / "why," not just "what," when capturing state for continuity | personal `handoff` skill | **partially adopted** — informs what to report back to the user after each routed step (what got produced and why that was the next step), not adopted as a separate tracking artifact |
| Parallel multi-agent launch + synthesis across specialist reviewers (findings aggregation, conflict resolution by priority weighting, adversarial verification of BLOCKER/HIGH claims) | Flexion orchestrator (Parallel Review Pattern, Conflict Resolution); personal `deep-pr-review` (Phase 0/2/4) | **declined for v1** — see below |

## Contradictions — flagged and resolved

**Durable progress file vs. derive state from existing artifacts.** CAMS's
`cams-workflow-tracking` is explicit and absolute: create a progress file
before any work starts, update it after every transition, never let it go
stale. This roster's own `staleness-audit` skill takes the opposite default
stance elsewhere — a doc that must be manually kept in sync with reality is
a liability, not an asset, and the fix for staleness is almost always
"delete the doc," not "add a review cadence."

Resolved in favor of `staleness-audit`'s stance: v1 derives current stage by
inspecting the artifacts that already exist (is there a problem framing
doc? a scope map, and what does its `Status` header say? which scope-map
steps already have a slice written?) rather than maintaining a parallel
tracking file that could drift from what's actually true. This does mean a
slice needs to name which scope-map step (if any) it was cut from, or
inspection can't tell — folded into `product-slicer`'s existing "standard
format" instruction rather than introducing new tracking machinery.

## Declined for v1

**Parallel review-synthesis orchestration** (Flexion's Parallel Review
Pattern + Conflict Resolution; `deep-pr-review`'s Phase 0/2/4 dedup,
cross-validation, and adversarial-verification machinery). This is a real,
well-sourced pattern, but it solves a different problem than what exists
today: reconciling several *specialist reviewers* examining the *same
artifact* in parallel. This roster has no such personas yet — `code-reviewer`,
`security-engineer`, `tdd-coach`, and `reliability-engineer` are all still
"Planned." Building this now means designing against a shape none of the
real future personas have confirmed yet. Revisit as orchestrator v2 once at
least two review-phase personas exist and can actually be run against the
same slice.

## Top gaps folded into skills/orchestrator/SKILL.md

1. Stage-detection logic scoped to exactly the two existing personas'
   trigger conditions (problem doc existence, scope-map presence +
   Status, per-step slice presence) — original to this project, not
   borrowed, since no source's state model matches this roster's actual
   artifact shape.
2. One-step-then-stop loop, explicit gate against auto-chaining the full
   pipeline unattended.
3. `product-slicer`'s slice format gets a one-line addition: name the
   source scope-map step, if any, so state can be derived by inspection.
