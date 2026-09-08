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
  `software-architect`, `devsecops-engineer`, and any future persona like
  them) asks a
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
| 4 | `software-architect` | Option-Enabling/Clean Architecture watchdog — dependency direction, module boundaries, screaming architecture, catching both premature *and* missing abstraction; also owns technology selection, recommending rather than deciding — the starting set a first test forces, and what sits behind each boundary once one forces it | Core strength | Done |
| 5 | `tdd-coach` | Red-Green-Refactor discipline — test quality over coverage-as-theater, catching over-mocked tests and false positives | Core strength | Planned |
| 6 | `code-reviewer` | Readability/DRY/simplicity triage — self-documenting code over comments, a severity taxonomy for findings | Core strength | Planned |
| 7 | `devsecops-engineer` | A system's runtime safety properties — whether it can be attacked, and whether it can stay up. Threat-aware requirements & review, secrets/PII hygiene, least privilege, dependency & supply-chain risk, observability, resilience & failure handling, safe rollout/rollback | Borrowed/synthesized (weak area) | Done |
| 8 | `accessibility-engineer` *(optional)* | WCAG-minded UI review — keyboard nav, semantic HTML, screen-reader correctness | Borrowed/synthesized (weak area) | Planned — cut if you don't do frontend work |
| 9 | `ux-designer` *(optional)* | Visual & interaction design — screen layout, component composition, and interaction flow for a slice's UI-touching parts, decided before code is written | Borrowed/synthesized (weak area) | Planned — cut if you don't do frontend work; hands off to `accessibility-engineer` for WCAG-correctness review, doesn't verify compliance itself |

**Rows 7 and 8 were merged.** The roster originally planned
`security-engineer` (threat-aware review) and `reliability-engineer`
(deployability & operability) as separate personas. Building them revealed
the split didn't survive contact: both sources ship them bundled, and the
overlap is structural rather than accidental — an over-permissive
deployment role and a missing timeout live in the same file, are found by
the same read, and are fixed in the same change. Per this roster's own
convention ("if two personas would flag the same thing, merge them or
sharpen the boundary"), they merged. The narrowness moved into the skills:
six of them, three per half, one per trigger. See
`.synthesis/devsecops-engineer.md` Contradiction 1.

## Orchestrator

`skills/orchestrator/SKILL.md` — routes a problem to whichever persona/skill
applies next, by inspecting existing artifacts (problem doc, scope map,
requirements, slices, design docs) instead of requiring the user to name
the right persona each time. Built as a **skill the main agent loads**,
not a persona/agent — `docs-writer`, `product-manager`, `product-slicer`,
`software-architect`, and `devsecops-engineer` are all `background: false`
and must run inline,
so there's nothing to spawn or parallelize; routing means adopting each
persona's own instructions in turn, in the same conversation.

**v1 scope**: sequential stage routing across today's five planning
personas (problem-framing-doc → scope-map → requirements-refinement →
slicing → user-story-writeup → architecture-design → security-requirements
→ reliability-requirements → technology-bootstrap), one step at a time,
human checkpoint after each — and a hard stop once a slice is designed, its
runtime-safety criteria are filled, and the project has a stack to build
on, since the next stage (`tdd-coach` implementing that design) doesn't
exist yet. `devsecops-engineer`'s four review/posture
skills sit outside this spine entirely: they run against code or a repo
that already exists, which the spine never reaches. Never cascades to the next scope-map step
automatically — each unit of work needs design/implementation before the
next one's shape gets decided, the same reason CAMS's own per-slice
workflow iterates rather than deciding every slice up front. Parallel
review-synthesis orchestration — reconciling several specialist reviewers
examining the same artifact — is a different, larger problem, deferred
below until it has real personas to synthesize across.

## Deferred / phase-2 ideas

- **Orchestrator v2 — parallel review synthesis**: launching several
  execution-phase specialists (`code-reviewer`, `devsecops-engineer`,
  `tdd-coach`) against the same artifact and reconciling their findings,
  mirroring the parallel-review pattern seen in other installed plugins.
  One of the three now exists. Still blocked on a second, and on a real
  constraint the merge just surfaced: `devsecops-engineer` is
  `background: false` because its requirements skills block on
  `AskUserQuestion`, so it can't currently be launched in parallel with
  anything. Its four review/posture skills never ask, though — whether a
  persona's parallelizability should be a per-skill property rather than a
  per-agent one is the actual design question here, and it isn't answerable
  until a second reviewer exists to parallelize against.
- **impl vs review split per persona**: several existing agent sets come in
  pairs (`*-impl` doing the work, `*-review` critiquing it). Decide per-persona,
  once built, whether that split earns its complexity here, or whether one
  agent that can do both is enough for personal use.

## Next to build

Decided at the end of each work session — only what's coming next, never a
full future ordering. Building in the order a real problem actually moves
through the SDLC, dogfooding each persona against one running example
(`evals/example/`) as it's built. Update this section before ending a
session; it should never describe more than what's actually next, and
session-by-session narrative gets condensed into "Durable findings" below
rather than accumulating here.

(`examples/budgeting-app/` was the original dogfood location but is listed
in `.gitignore` — anything placed there never gets tracked. Real dogfooding
lives in `evals/example/`, which is tracked.)

### Where things stand

Five personas done. `software-architect` also gained an unplanned third
skill, `technology-bootstrap`, and the roster gained its first **advisor
consult** — `software-architect` loading a `devsecops-engineer` skill
inline for a narrow runtime-safety question and handing control straight
back. It is not a spawn and can't be; every persona here is
`background: false`, so it reuses `orchestrator`'s adopt-inline pattern.

**Benchmarking is the live problem, not the roster.** The last dogfood run
was graded 16/16 against the eval cases' own graders
(`evals/example/summary.md`), and the ordering failure that drove this
session's fixes did not recur. But that is real artifacts graded against
adapted graders — *not* the eval cases passing. Every case covering changed
code is currently stale; `evals/README.md` tracks last-result and staleness
as separate columns.

### Next: eval cases for `devsecops-engineer`'s six skills

A deliberate break from the persona-per-session rhythm. That persona was the
largest single addition to the plugin — one agent, six skills, on a weak
area — and two of the six (`security-requirements`' threat pass and
`operational-readiness`) had **no source material at all** and were written
from a gap rather than synthesized. Those two can only be checked by running
them. Building `accessibility-engineer` next would stack a second weak-area
persona on top of six untested skills.

Two of the six have now been exercised in a real run
(`security-requirements` and `reliability-requirements`), and both produced
findings that reshaped the run — which is evidence the remaining four will
move things too, not evidence they're fine.

Priority: the two requirements skills first (they block on
`AskUserQuestion`, so they need the two-phase runner), then the four
review/posture skills, which are simpler to grade because they take an
artifact and return a report.

**The single highest-value case anywhere in the plugin right now** is a
`security-requirements` case testing that the persona *produces a clean
hand-back* rather than presenting the user a menu of options. The receiving
side is covered (`vertical-slicing` Scenario C, `orchestrator` Directory L);
the producing side — the actual observed failure — is not.

Its fixture shape, so this doesn't get re-derived:

- **A slice already cut and designed**, whose thin path deliberately omits
  some capability. (The observed case: connect, select, list — no login.)
- **An established fact in the prompt that forces that capability**, stated
  as settled background rather than as a question. (The observed case: the
  app is hosted and reachable over the internet, and the slice displays
  financial data — so the list is publicly reachable without a login.)
- **Scripted answers** for the skill's own ask-first step: what data is in
  play, what obligations apply, who the users are.

Correct behaviour is four things at once, and the graders should test them
separately: it writes real criteria for what *is* in scope; it detects the
forced-but-unscoped capability; it reports that to `product-slicer` by name;
and — the primary, **negative** grader — it does *not* enumerate resolution
options for the user to choose between, because laying out the menu is
itself the scope decision. A fifth failure worth catching: silently writing
criteria that assume the missing capability exists.

Write the two requirements cases against `evals/example/`'s real output
(`security-requirements-001.md`, `reliability-requirements-001.md`) as
reference — that's genuine output from two of the six skills, and it's what
a case author would otherwise have to imagine.

Also outstanding: `software-architect:architecture-design`'s graders are
bound to a CSV-export fixture and won't port to any other design, which is
why the last dogfood run's design doc couldn't be graded at all. The rework
is specified in that case's own `NOTES.md`.

**Before or alongside any of this, eight existing cases need running** —
none of the plugin's scores currently describe the code. `evals/README.md`
carries the ordered backlog; `orchestrator` is first, since it's the only
case currently failing and holds the untested backward-routing fixtures.

### Then `accessibility-engineer`, then `ux-designer`, then `tdd-coach`

Evidence for the first two is still live: `evals/example/slice-001.md` still
carries an unfilled accessibility placeholder, and nothing in the roster
decides what a UI-touching slice's screen looks like before code exists —
`architecture-design` deliberately stops at "renders whatever the strategic
side hands it," and `accessibility-engineer` reviews for WCAG correctness
rather than generating a design.

`tdd-coach` will move the orchestrator's terminal row again, to
"implemented," and needs a fresh no-cascade check when it does.

## Durable findings

Kept because re-deriving them is expensive; not a session log.

**Rows 7 and 8 merged into `devsecops-engineer`.** Scoped as
`security-engineer` alone, merged with `reliability-engineer` mid-build once
the boundary question was worked: both sources ship them bundled, and the
overlap is structural — an over-permissive deployment role and a missing
timeout live in the same file, are found by the same read, and are fixed in
the same change. The narrowness moved into the skills instead: six of them,
three per half, one per trigger. See `.synthesis/devsecops-engineer.md`
Contradiction 1.

**Two corpus-wide silences drove design rather than any source
disagreement.** Threat modeling and safe rollout/rollback are named as
responsibilities by every source and taught by none, so both methods were
supplied rather than synthesized (Contradictions 6 and 11). The single
substantive rollback statement in the entire corpus appears in proposal
collateral, not engineering guidance.

**Two-for-two on declining quantitative apparatus bolted onto qualitative
judgment.** Rejected for `software-architect`: a numeric architecture-health
score. Rejected for `devsecops-engineer`: a `security-reviewer` source that
progressively *skips* checks which have never found anything, reaching a
"fast mode" scanning only for vulnerability classes already seen — a
security control that gets quieter the longer it finds nothing is one that
fails silently (Contradiction 3).

**Source-independence caveat.** CAMS's devsecops and SRE agents are
near-verbatim copies of Flexion's (`diff` shows only an added `skills:`
list). For anything from those six files, "both sources agree" is one source
stated twice.

**Technology ownership: the sources disagreed and the split matters.**
Flexion treats the tech stack as a human-owned spec with a hard halt if
missing ("technology choices are yours, not the AI's"); CAMS folds the same
decisions into the per-slice design doc. Resolved toward Flexion on
*ownership* (recommend with trade-offs, wait for approval, never pick) and
toward CAMS on *timing* ("infrastructure emerges from feature slices" —
Anti-Pattern 3, Technical Plumbing Slice). Their synthesis is the demand
test: ask only what the slice's first failing test can't be written without,
and leave everything else explicitly open with a named owner.

**A review skill has no notion of choosing.** `supply-chain-review` covers
the pinning *standard* well but scopes itself to auditing an existing
repository, so the selection criterion — prefer the package manager where
strict pinning is the default rather than an opt-in flag — went into
`technology-bootstrap` instead. Both end states audit identically, which is
exactly why review can't catch the difference and selection must.

**The propagation lesson, and the five fixes it produced.** A real run
failed because `problem.md`'s Constraints already contained the facts that
forced a login, and nothing carried them forward: `requirements-001`
propagated only the constraint that obviously concerned its own step, and
`scope-map` had blessed the drop in advance by routing cross-cutting
constraints to "made concrete per slice as each is designed." The constraint
resurfaced at security time, when the only fixes left were re-slicing or
growing a slice — and the persona that found it laid out a menu of options,
which *is* the scope decision, made by a persona that doesn't own scope.

The fix was propagation, not a new artifact — an earlier proposal for a
"system facts" document was dropped once it became clear `problem.md`'s
Constraints section already is that artifact. The five changes:

1. `requirements-refinement` reconciles every problem-doc constraint against
   the current unit, stating what each *forces* — consequences, not
   quotations.
2. `scope-map` may set a cross-cutting constraint aside as not-a-step, but
   must route it to each step's requirements pass.
3. `orchestrator` gained **backward routing, taking precedence over the
   whole table**: route to the persona that *owns* an invalidated artifact,
   not the one that found the problem. The spine had been forward-only.
4. Downstream personas hand scope changes to `product-slicer`; "the slice
   grows" is never offered as a neutral option among equals.
5. `vertical-slicing` names the whole slice set for a unit and specifies
   only the first — which both other sources already did, making the
   one-slice-at-a-time behavior this plugin's own divergence.
