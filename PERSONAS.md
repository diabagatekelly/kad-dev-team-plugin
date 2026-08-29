# Persona Roster Plan

This is the design plan for `kad-dev-team`: a personal Claude Code plugin that
assembles the narrow-focus personas you'd find on a strong delivery team, each
one a thin agent (`agents/<name>/AGENT.md`) backed by one or more skills
(`skills/<name>/SKILL.md`), following the agent/skill pattern already used by
other plugins installed on this machine.

Nothing below is built yet — this is the plan to build against, one persona
at a time. Check off the "Status" column as personas get their AGENT.md/SKILL.md
written.

## Design conventions

- **Agent** = `agents/<slug>/AGENT.md`, YAML frontmatter (`name`, `description`
  with 2-3 usage examples, `model`, `color`, `tools`, `skills:` list) + a
  second-person persona system prompt.
- **Skill** = `skills/<slug>/SKILL.md`, YAML frontmatter (`name`, `description`)
  + body. Use `references/`, `patterns/`, or `templates/` subfolders for
  material too long to keep inline.
- Personas stay **narrow**: one clear mandate, not a generalist. Overlap
  between personas is a smell — if two personas would flag the same thing,
  merge them or sharpen the boundary.
- This plugin is **portable**, not tied to any one employer or project.
  Skills here should read as general engineering principles, applicable on
  any project — project-specific plugins remain the place for
  project-specific procedure (custom query DSLs, org-specific deployment
  scripts, ticket-format conventions, etc.).

## Attribution philosophy

For personas in my strike zone (architecture, TDD, code review, vertical
slicing, docs) the content comes from my own working knowledge — no borrowing
needed.

For personas outside my expertise (security, reliability/infra, accessibility)
the process is:
1. Read the relevant existing skill to learn **what topics/checks it covers
   and why** (its table of contents, not its prose).
2. Write original checklists, examples, and structure from that topic list —
   own wording, own severity taxonomy, own code samples.
3. Note the conceptual lineage once, in the skill's own doc (a short "informed
   by established security/SRE practice" line), instead of copying text.

Never copy prose, checklist wording, or file structure verbatim from an
installed plugin into this one.

## Roster

| # | Persona (slug) | Narrow focus | Expertise | Status |
|---|---|---|---|---|
| 1 | `software-architect` | Option-Enabling/Clean Architecture watchdog — dependency direction, module boundaries, screaming architecture, catching both premature *and* missing abstraction | Core strength | Planned |
| 2 | `tdd-coach` | Red-Green-Refactor discipline — test quality over coverage-as-theater, catching over-mocked tests and false positives | Core strength | Planned |
| 3 | `code-reviewer` | Readability/DRY/simplicity triage — self-documenting code over comments, a severity taxonomy for findings | Core strength | Planned |
| 4 | `product-slicer` | Vertical slicing & scenario-driven delivery — smallest end-to-end shippable unit, acceptance-criteria quality, feature-shape YAGNI | Core strength | Planned |
| 5 | `docs-writer` | Purposeful documentation — problem framing docs, ADRs, WHY-not-WHAT comments, PR/issue write-ups, avoiding stale/ceremonial docs | Core strength | Done |
| 6 | `security-engineer` | Threat-aware review — OWASP-style checks, secrets/PII hygiene, dependency & supply-chain risk, least privilege | Borrowed/synthesized (weak area) | Planned |
| 7 | `reliability-engineer` | Deployability & operability — IaC review, observability (logs/metrics/traces), safe rollout/rollback, incident-readiness | Borrowed/synthesized (weak area) | Planned |
| 8 | `accessibility-engineer` *(optional)* | WCAG-minded UI review — keyboard nav, semantic HTML, screen-reader correctness | Borrowed/synthesized (weak area) | Planned — cut if you don't do frontend work |

## Deferred / phase-2 ideas

- **Orchestrator persona/skill**: a lead-engineer agent that routes work to
  the right personas and synthesizes their findings, mirroring the
  orchestrator pattern seen in other installed plugins. Worth adding once 3+
  personas exist and the coordination pain is real — not before.
- **impl vs review split per persona**: several existing agent sets come in
  pairs (`*-impl` doing the work, `*-review` critiquing it). Decide per-persona,
  once built, whether that split earns its complexity here, or whether one
  agent that can do both is enough for personal use.

## Build order — revised

Superseded the original pattern-first order below. Instead, building in the
order a real problem actually moves through the SDLC, dogfooding each
persona against one running example (`examples/budgeting-app/`, a personal
finance web app to replace manual Excel accounting) as it's built:

1. **`docs-writer`** — Done. Problem exists, no issue/slice/code yet →
   produced `examples/budgeting-app/problem.md`.
2. **`product-slicer`** — next. Turn the problem doc into a first vertical
   slice.
3. **`software-architect`**, **`tdd-coach`**, **`code-reviewer`** — as the
   first slice gets designed and implemented.
4. **`security-engineer`**, **`reliability-engineer`** — as soon as the
   example touches account credentials/data and any deployment/sync
   infrastructure, which it will almost immediately.
5. **`accessibility-engineer`** — once the example has a UI to review.

<details>
<summary>Original pattern-first order (superseded)</summary>

1. `code-reviewer` first — best-known domain, good persona to nail the
   AGENT.md/SKILL.md pattern on before repeating it seven more times.
2. `security-engineer` and `reliability-engineer` next — highest-leverage
   gaps, done early while the pattern is fresh.
3. Round out `software-architect`, `tdd-coach`, `product-slicer`,
   `docs-writer`.
4. Decide on `accessibility-engineer` and the phase-2 ideas once the core
   seven feel solid.

</details>
