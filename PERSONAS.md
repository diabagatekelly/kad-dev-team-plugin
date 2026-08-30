# Persona Roster Plan

The living plan `kad-dev-team` is built against, one persona at a time: a
personal Claude Code plugin assembling the narrow-focus personas you'd find
on a strong delivery team, each a thin agent (`agents/<name>/AGENT.md`)
backed by one or more skills (`skills/<name>/SKILL.md`). The "Status" column
tracks progress as each persona gets its AGENT.md/SKILL.md written. Not
every skill belongs to a persona, though — see "Orchestrator" below for the
one exception so far, a skill the main agent loads directly with no owning
agent.

## Design conventions

- **Agent** = `agents/<slug>/AGENT.md`, YAML frontmatter (`name`, `description`
  with 2-3 usage examples, `model`, `color`, `tools`, `skills:` list) + a
  second-person persona system prompt.
- **Skill** = `skills/<slug>/SKILL.md`, YAML frontmatter (`name`, `description`)
  + body. Use `references/`, `patterns/`, or `templates/` subfolders for
  material too long to keep inline.
- **One skill per trigger, not per persona.** A persona referencing several
  distinct triggers (e.g. `docs-writer` writing an ADR vs. a PR description)
  gets one narrow skill per trigger, not one bundled skill — a skill loads
  as a whole unit, and a persona's `skills:` list only pulls in the one that
  actually matches the current task. Cross-cutting guidance that applies to
  every trigger (e.g. a persona's core stance) belongs in the agent's own
  system prompt, not duplicated across skills.
- **Planning personas ask, they don't just guess.** A persona that shapes
  work before it exists (`product-manager`, `product-slicer`,
  `software-architect`, and any future persona like them) asks a
  clarifying question when an ambiguity would change the shape of its
  output. Deferring-as-an-open-question is only for ambiguity that
  wouldn't. Silently picking an assumption on something load-bearing is
  worse than asking once.
- Personas stay **narrow**: one clear mandate, not a generalist. Overlap
  between personas is a smell — if two personas would flag the same thing,
  merge them or sharpen the boundary.
- **Where artifacts get saved is a parameter, not a hardcoded path.** No
  fixed directory-naming convention is baked into any skill — this plugin
  is portable, and a fixed path would either collide with how a given
  project already organizes docs or force one convention on every project
  it's installed into. `orchestrator` is invoked with the artifacts
  directory as a parameter, or not: given one, that's the target, no
  second-guessing; not given one, it asks once — "where do this problem's
  artifacts already exist, or where should they be created?" — and passes
  the answer to whichever persona it invokes for that problem, this
  session and any future one. A persona invoked directly (bypassing
  orchestrator) follows the same rule: use whatever location is given or
  obviously implied, ask if not. **Never search the project for a
  location instead of asking** — a location that wasn't given or implied
  gets asked for, not discovered.
- This plugin is **portable**, not tied to any one employer or project.
  Skills here should read as general engineering principles, applicable on
  any project — project-specific plugins remain the place for
  project-specific procedure (custom query DSLs, org-specific deployment
  scripts, ticket-format conventions, etc.).

## Attribution philosophy

Every persona — regardless of how strong my own knowledge of the domain is —
is synthesized from three reference sources, consulted every time, not just
for weak areas:

1. **Flexion plugin** — `github.com/flexion/flexion-ai-claude-plugin`,
   local mirror `~/.claude/plugins/marketplaces/flexion-plugins`.
2. **Personal skills** — global `~/.claude/skills`, plus project-level
   `.claude/skills` scattered across `~/Documents/*`.
3. **CAMS** — `github.com/flexion/ustp-cams-fdp`, local checkout
   `~/Documents/DOJ/ustp-cams-fdp`, also mirrored under
   `~/.claude/plugins/{cache,marketplaces}/cams-team-plugins`.

**Process, per persona:**
1. Read each source's relevant material in full (not just structure) for the
   persona's focus area.
2. Synthesize into a working note under `.synthesis/<persona>.md`: the
   principles worth capturing, which source(s) each came from, and any place
   sources disagree (with how it was resolved). This is the only place a
   source is ever named.
3. Write the persona's `SKILL.md`/`AGENT.md` from that synthesis, in
   original wording — never copy prose, checklist wording, severity
   taxonomy, or file structure verbatim from any source, and never name a
   source in the shipped files.

`.synthesis/` is internal scaffolding, not part of the shipped plugin. Once
the full roster is built, delete it and scrub any remaining source mentions.

## Roster

| # | Persona (slug) | Narrow focus | Expertise | Status |
|---|---|---|---|---|
| 1 | `docs-writer` | Purposeful documentation — problem framing docs, light scope maps for problems too big to slice blind, ADRs, WHY-not-WHAT comments, user-story/PR write-ups, user-facing feature docs, avoiding stale/ceremonial docs | Core strength | Done |
| 2 | `product-manager` | Pinning down WHAT before HOW — asking the user directly who benefits, what they want, and why for one unit of work, before any slice gets cut | Core strength | Done |
| 3 | `product-slicer` | Vertical slicing & scenario-driven delivery — smallest end-to-end shippable unit for a confirmed requirement, acceptance-criteria quality, feature-shape YAGNI, scope-creep pushback | Core strength | Done |
| 4 | `software-architect` | Option-Enabling/Clean Architecture watchdog — dependency direction, module boundaries, screaming architecture, catching both premature *and* missing abstraction | Core strength | Planned |
| 5 | `tdd-coach` | Red-Green-Refactor discipline — test quality over coverage-as-theater, catching over-mocked tests and false positives | Core strength | Planned |
| 6 | `code-reviewer` | Readability/DRY/simplicity triage — self-documenting code over comments, a severity taxonomy for findings | Core strength | Planned |
| 7 | `security-engineer` | Threat-aware review — OWASP-style checks, secrets/PII hygiene, dependency & supply-chain risk, least privilege | Borrowed/synthesized (weak area) | Planned |
| 8 | `reliability-engineer` | Deployability & operability — IaC review, observability (logs/metrics/traces), safe rollout/rollback, incident-readiness | Borrowed/synthesized (weak area) | Planned |
| 9 | `accessibility-engineer` *(optional)* | WCAG-minded UI review — keyboard nav, semantic HTML, screen-reader correctness | Borrowed/synthesized (weak area) | Planned — cut if you don't do frontend work |

## Orchestrator

`skills/orchestrator/SKILL.md` — routes a problem to whichever persona/skill
applies next, by inspecting existing artifacts (problem doc, scope map,
requirements, slices) instead of requiring the user to name the right
persona each time. Built as a **skill the main agent loads**, not a
persona/agent — `docs-writer`, `product-manager`, and `product-slicer` are
all `background: false` and must run inline, so there's nothing to spawn
or parallelize; routing means adopting each persona's own instructions in
turn, in the same conversation.

**v1 scope**: sequential stage routing across today's three planning
personas (problem-framing-doc → scope-map → requirements-refinement →
slicing → user-story-writeup), one step at a time, human checkpoint after
each — and a hard stop once a slice is written up, since the next stage
(`software-architect` designing that slice) doesn't exist yet. Never
cascades to the next scope-map step automatically — each unit of work
needs design/implementation before the next one's shape gets decided, the
same reason CAMS's own per-slice workflow iterates rather than deciding
every slice up front. Parallel review-synthesis orchestration —
reconciling several specialist reviewers examining the same artifact — is
a different, larger problem, deferred below until it has real personas to
synthesize across.

## Deferred / phase-2 ideas

- **Orchestrator v2 — parallel review synthesis**: launching several
  execution-phase specialists (`code-reviewer`, `security-engineer`,
  `tdd-coach`, `reliability-engineer`) against the same artifact and
  reconciling their findings, mirroring the parallel-review pattern seen in
  other installed plugins. Needs at least two of those personas to actually
  exist first — designing it earlier means designing against a shape
  nothing has confirmed yet.
- **impl vs review split per persona**: several existing agent sets come in
  pairs (`*-impl` doing the work, `*-review` critiquing it). Decide per-persona,
  once built, whether that split earns its complexity here, or whether one
  agent that can do both is enough for personal use.

## Next to build

Decided at the end of each work session — only the persona(s) coming next,
never a full future ordering. Building in the order a real problem actually
moves through the SDLC, dogfooding each persona against one running example
(`evals/example/`) as it's built. Update this section before ending a
session; it should never describe more than what's actually next.

(`examples/budgeting-app/` was the original dogfood location but is listed
in `.gitignore` — anything placed there never gets tracked. Real dogfooding
now lives in `evals/example/` instead, which is tracked.)

**Next:** `software-architect` — strategic design for slice-01, confirmed by
cross-checking CAMS's `cams-new-feature` Phase 2 and Flexion's orchestrator
ordering ("foundation first: software-architect → specialists"). This is
also the stage `orchestrator` currently stops at (slice written up, no
architect to hand off to) — building it is what lets the pipeline continue
past that point instead of just stopping there.
