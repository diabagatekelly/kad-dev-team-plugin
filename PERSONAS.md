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
| 8 | `accessibility-engineer` *(optional)* | WCAG-minded UI review — keyboard nav, semantic HTML, screen-reader correctness. One skill, `accessibility-review`, verifying what `ux-designer` already rendered rather than designing anything itself | Borrowed/synthesized (weak area) | Done — cut if you don't do frontend work; the roster's first `background: true` persona, since its one skill never blocks on `AskUserQuestion` |
| 9 | `ux-designer` *(optional)* | Visual & interaction design — screen layout, component composition, and interaction flow for a slice's UI-touching parts, decided before code is written. Two skills, establish-once/apply-per-slice like `software-architect`'s: `design-system` (once per project, also handles review/evolve) and `screen-design` (per slice) | Borrowed/synthesized (weak area) | Done — cut if you don't do frontend work; hands off to `accessibility-engineer` for WCAG-correctness review, doesn't verify compliance itself (that persona doesn't exist yet) |

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
and must run inline, so there's nothing to spawn or parallelize for them;
routing means adopting each persona's own instructions in turn, in the
same conversation. `ux-designer` is also `background: false` for the same
reason (both its skills block on `AskUserQuestion`); `accessibility-engineer`
is the first exception — see "Next to build" below — but `orchestrator`
still executes it inline like every other row today, since v1's routing is
sequential by construction, not because every persona it invokes requires it.

**v1 scope**: sequential stage routing across the full spine as it stands
today (problem-framing-doc → scope-map → requirements-refinement → slicing
→ user-story-writeup → architecture-design → security-requirements →
reliability-requirements → design-system → screen-design →
accessibility-review → technology-bootstrap), one step at a time, human
checkpoint after each — and a hard stop once a slice is designed, its
runtime-safety criteria are filled, its screen designed and accessibility
criteria filled if UI-touching, and the project has a stack to build on,
since the next stage (`tdd-coach` implementing that design) doesn't exist
yet. `devsecops-engineer`'s four review/posture
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
  One of the three now exists, and `accessibility-engineer` — not one of
  the original three, but a real reviewer with the same shape — is the
  first persona in this roster with nothing blocking async launch at the
  *agent* level, not just some skills within it. `devsecops-engineer` is
  still `background: false` because its requirements skills block on
  `AskUserQuestion`, so the per-skill-vs-per-agent parallelizability
  question this note originally raised still isn't answerable against a
  real mixed-behavior persona — that needs a persona with both an asking
  half and a non-asking half to actually test whether the two halves
  should carry different flags, and none exists yet. What a second
  reviewer does resolve: there are now two independent reviewers that
  *could* run against the same artifact concurrently, which is the actual
  prerequisite this note named as blocking — reconciling their findings
  into one synthesis is still unbuilt.
- **impl vs review split per persona**: several existing agent sets come in
  pairs (`*-impl` doing the work, `*-review` critiquing it). Decide per-persona,
  once built, whether that split earns its complexity here, or whether one
  agent that can do both is enough for personal use.
- **Dev-agent quarantine/grade/combine cycle**: once execution-phase personas
  exist, have `orchestrator` spin off 2-3 implementer instances per slice,
  each in its own isolated worktree with no visibility into siblings' work,
  each carrying the full dev skillset (TDD, dependency-rule, etc.). Grade
  each implementation against those same skills in a scoring/critique mode —
  one grader per skill the persona is expert in, not one generic reviewer.
  For the combine step: dev-agents should surface their grading feedback to
  each other, but the actual merge into one submission needs to stay a
  single accountable step (the orchestrator, or one fresh combiner agent
  given every implementation plus every grade) rather than joint/collective
  authorship by the dev-agents themselves — several agents editing one
  shared artifact reintroduces the same anchoring/coordination failure mode
  quarantine exists to prevent. Re-grade the combined version pass/fail; on
  fail, loop scoped only to the named failures, not a full re-open —
  mirrors a ratification-vote pattern seen in other installed multi-agent
  tooling. Blocked on execution-phase personas existing at all (today, only
  `devsecops-engineer`'s review skills take an artifact and return a report
  without asking), and on every current persona being `background: false` —
  none of today's personas can run as parallel/independent instances, so
  this needs either dev-agent definitions that don't block on
  `AskUserQuestion`, or the same per-skill-not-per-agent parallelizability
  model already flagged as open under Orchestrator v2.

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

**The eight-case stale-eval backlog is fully cleared** (`evals/README.md`'s
own backlog table, now all struck through). Two real skill bugs were found
and fixed along the way: `orchestrator` was narrating a post-resolution
forward-resumption plan after a backward route, which
`single-step-not-chained` treats as the same chaining the forward case
already forbids; `scope-map` was reading a cross-cutting constraint's
literal wording ("AI categorization must be free") too narrowly instead of
by its underlying concern. Both fixed and re-verified.
`software-architect:architecture-design` was reworked per its own
`NOTES.md` — split into `portable-*` graders that hold for any design doc
and `fixture-*` graders for its own sync/async and premature-abstraction
content — then run for the first time ever, 8/8.

**A methodology correction mid-session, worth keeping.** Eval cases should
be derived from `AGENT.md`/`SKILL.md` directly; a real historical artifact
(`evals/example/`) is something to independently *audit* against that
spec, not a blueprint to copy content or scenario shape from. Auditing
`evals/example/security-requirements-001.md` this way (rather than
assuming real output was correct because it was real) found a genuine gap:
the skill names five exits a sensitive-data class can leak through, and
that document never addresses monitoring/telemetry as one of them within
its own text — the reasoning only exists in the sibling
`reliability-requirements-001.md`. A new grader
(`addresses-all-five-exits`) checks this now, and it caught the same
category of gap in this session's own emulated `security-requirements`
run before it shipped (missing exception/stack-traces, conflated into the
error-response criterion) — fixed and re-verified.

**All six `devsecops-engineer` skills now have a passing eval case.**
`security-requirements` (7/7), `reliability-requirements` (5/5),
`security-review` (7/7), `reliability-review` (6/6), `supply-chain-review`
(7/7), and `operational-readiness` (6/6). `security-requirements`' case is
the one this file previously called the single highest-value gap in the
plugin — it tests a clean scope hand-back (a login gap forced by a slice
hosted-and-reachable over the internet) rather than a menu of options, and
passed clean. `operational-readiness` had no source material at all; its
case tested both halves of its central judgment call at once — correctly
scaling down formal incident process and monitoring for a solo project,
while correctly *not* scaling down an untested rollback or a schema change
coupled to code, both of which the skill says hold regardless of scale —
and also passed clean. Two case-authoring gaps were caught and fixed
*before* running (missing scripted approvals for decisions the skill's own
text names as requiring the approval loop), not after — worth naming as a
now-repeated pattern: read the skill's "what counts as a decision" section
before finalizing a fixture's scripted answers, not just its main
narrative.

**`ux-designer` built, out of the planned order** — the user asked about it
directly rather than waiting for `accessibility-engineer` to go first. Two
skills, `design-system` (once per project, also the review/evolve trigger)
and `screen-design` (per slice), synthesized from all three sources for the
first time on a topic where the sources actually converged more than they
conflicted: Flexion's `flexion-frontend-design` skill (Foundation/
Constrained/Advisory modes, token/pattern structure, preferences-vs-problems,
a five-dimension critique framework, a copy checklist) and CAMS's
`cams-ux-heuristics` (Nielsen+Shneiderman's 11 consolidated heuristics,
trade-off documentation, component-catalog reuse) landed on compatible
principles from different angles. Personal skills had nothing on this
topic — noted, not fabricated, same shape as prior syntheses' silences.

Three contradictions resolved, all toward decisions the roster already
holds elsewhere: Flexion's source treats design and implementation as the
same act (writes production component code); resolved toward keeping this
persona pre-code — it renders a mockup, not the final component, mirroring
how this roster already separates deciding from implementing. All three
sources blend accessibility into the same design pass; resolved toward the
roster's pre-existing split with `accessibility-engineer` — this persona
designs *accessible by construction*, verification is a different
persona's job. CAMS's numeric severity scale doesn't apply at all, since
pre-code design has no findings to rate, the same reason
`architecture-design` carries none either.

**`ux-designer` dogfooded against `evals/example/` and eval-covered.**
Several real runs against slice 1 surfaced concrete gaps the synthesis
alone hadn't caught — see Durable findings below for the three that
generalize beyond this persona. One addition landed alongside the fixes,
not in response to a bug: `design-system` can now work from a concrete
reference (a screenshot, or a named comparison like "make it feel like
Stripe") instead of always generating candidates from scratch, asking
which mode applies before doing either. `orchestrator` is wired in (two
new routing rows between `reliability-requirements` and
`technology-bootstrap`, plus a rationale paragraph on why screen design
runs after both runtime-safety rows and before `technology-bootstrap`)
and checks both the artifacts root and a `visual-ux/` subfolder for
existing `design-system`/`screen-design` artifacts, since where this
persona saves its own write-ups has genuinely varied run to run.

Both skills now have a passing eval case, written from `AGENT.md`/
`SKILL.md` text before either was checked against real dogfood output,
per this plugin's established methodology: `design-system` (9 graders,
three-phase — reference-vs-generate, then the candidate choice — 9/9
after one re-run) and `screen-design` (9 graders, single-phase, 9/9). The
re-run wasn't a skill-text gap: the first pass's three generated
candidates varied by color and type but shared one layout, exactly what
the skill already warns against ("not three variations on the same idea
wearing different colors") — a single-run quality miss, confirmed by a
clean re-run with structurally distinct candidates rather than a fix to
the skill.

**`accessibility-engineer` built, out of the planned order relative to
`code-reviewer`/`tdd-coach` but exactly where the roster's own "Next"
note already pointed.** One skill, `accessibility-review` — no
establish-once/apply-per-slice split like `ux-designer`'s, since the
mandate is a single trigger: verify what `ux-designer` already rendered,
don't design anything. Synthesized from `built-in-wcag-subset.md` (the
file `ux-designer`'s own synthesis explicitly deferred here), a SCORM-domain
Flexion agent (`accessibility-inclusive-reviewer`) that turned out to be
the corpus's only source reviewing *driven, built* content rather than
static markup, and CAMS's `cams-testing-a11y` (read past its
Playwright/axe-core procedure for the principles underneath — the
automated/manual layering, a severity taxonomy, and a
disable-with-accountability pattern). Personal skills had nothing on this
topic, same finding shape as every weak-area synthesis before it.

Two contradictions resolved, both toward decisions this roster already
holds elsewhere: three incompatible severity vocabularies (axe's
critical/serious/moderate/minor, a binary clear-problem/preference split,
a blocking/non-blocking-plus-evidence-type scheme) resolved toward this
plugin's own existing Critical/High/Medium/Low scale, the same one
`devsecops-engineer`/`architecture-review` share, mapped here by
completeness of exclusion rather than by category. Whether suppressing a
failing check is ever legitimate — CAMS alone allows it, the other two
don't — resolved toward adopting CAMS's underlying accountability
discipline (visible, dated, justified, owned) without its
Playwright-specific file mechanism: a finding that can't be fixed now
stays visible as accepted-for-now, the same "carry forward, never drop"
convention this roster already applies to every other unresolved item.
Full reasoning in `.synthesis/accessibility-engineer.md`.

**Dogfooded for real against `evals/example/`'s actual rendered
mockups — not described, actually driven in a browser** (keyboard focus
via programmatic `.focus()` plus computed-style inspection, since
synthetic `Tab` keydown events weren't reliably reaching page focus in
that session; contrast computed from real rendered color values). Found
eight real findings the mockups' own text hadn't surfaced, written up in
the roster's first `accessibility-review-001.md`: the nav rail and
quick-action control are non-semantic `<div>`s with no keyboard path at
all; the design system's declared focus treatment was never actually
implemented in any of the seven screens' CSS (the one real interactive
element falls back to the browser's bare default outline); five of the
seven screens' status-block titles are `<strong>` text rather than a
heading, invisible to heading navigation, unlike the one screen that
established the pattern with a real `<h2>`; a retry button's text fails
contrast at 4.38:1; none of the status containers declare a live-region
role; decorative icons carry no `aria-hidden`; and every interactive
control's touch target — confirmed via the real rendered
`getBoundingClientRect()`, not just the declared CSS — falls below 44×44,
which turned out to be `design-system-001.md`'s own declared values
working exactly as declared, routed back to `ux-designer:design-system`
as a token fix rather than patched per screen. Slice-001's
accessibility-criteria placeholder is now genuinely filled, five
criteria confirmed against the real mockups and two deferred until real
code exists to check them against.

**Two of those findings weren't covered by the skill as first written,
so the skill got fixed before the dogfood output was called
final** — the same order this plugin's methodology already
requires (fix the skill, not just the one output). `accessibility-review`
gained two more checks past its original six-from-the-source baseline:
anything that looks interactive must actually be a real interactive
element (worse than a missing focus style, since there's no focusable
element to put one on), and dynamic status content must declare its
live-region role in markup now, checkable today independent of whether
real transitions exist yet to fire it.

**A stale claim in the existing corpus surfaced along the way, and got
corrected.** `screen-design-001.md`'s own "Open questions" section said
"None left open," while `slice-001.md` itself still listed the
accessibility placeholder as genuinely open at the time — the exact
silent-drop failure mode PERSONAS.md's own durable finding below already
names, caught here by the very persona that finding predicted would need
to watch for it. Corrected in place with a note explaining the claim was
wrong when written, not that the gap is still open today.

**The eval case ran: 8/9 PASS**, written from `AGENT.md`/`SKILL.md` text
before checking the real dogfood output, per this plugin's established
order (9 graders, single-phase, against a synthetic reorder-accounts
fixture built to test each of the persona's named rules directly,
including a deliberate escalation trap — a claimed "fully accessible
version available elsewhere" — meant to tempt an under-flag). All eight
substantive `llm` graders passed clean. The one failure, `skill-invoked`,
is a genuine emulation-fidelity gap worth its own line: this environment
can't actually restrict a spawned `general-purpose` agent to
`Read`/`Grep`/`Glob` the way `agent-eval`'s own procedure assumes, so the
emulated persona used real browser automation instead of reasoning over
the HTML as text — driving the fixture live (real `Tab` keypresses,
computed-style contrast math, real `getBoundingClientRect` calls), and,
plausibly a symptom of the same distraction, never wrote the harness's
mandated "Skills consulted:" self-report line. Scored FAIL on the letter
of that mechanical check regardless, not smoothed over — full reasoning,
including why the substantive output is still strong independent evidence
the skill was genuinely read and applied, in
`evals/accessibility-engineer:accessibility-review/eval-score/summary.md`.
Recorded as a general harness limitation in `evals/README.md`'s "Known
coverage gaps," since any future case for a persona whose skill instructs
real tool use should expect the same.

**The real dogfood artifact was then graded separately, against the same
case's graders, borrowed the way `evals/example/`'s own method section
already prescribes.** `accessibility-review-001.md` — the actual review
of all seven of this directory's real rendered mockups, not the eval
case's synthetic fixture — scored **6/6 graded PASS**, with two graders
honestly skipped rather than force-fit (neither an "accessible version
elsewhere" claim nor a requirement-vs-accessibility tension exists
anywhere in this real slice's eight findings) and two adapted to test the
same underlying property against what's actually there instead of the
fixture's specifics. Full table and reasoning in
`evals/example/summary.md`'s new section. The adaptation worth keeping:
`catches-no-keyboard-path-on-required-interaction-critical`'s literal
premise didn't hold (the nav-rail controls have zero accessible path but
aren't *required* by this slice yet, so High rather than Critical is
correct) — but the finding still demonstrated the rule was a live test
against this artifact's facts, not a memorized label, by naming both why
Critical doesn't apply yet and exactly what would flip it. Independent of
any grader, the touch-target finding traced its own root cause to
`design-system-001.md`'s declared token values and routed the fix back to
`ux-designer:design-system` rather than proposing a per-screen patch —
this persona's own artifact-ownership boundary, held correctly on the
first real case that actually presented the choice.

### Next: `tdd-coach`

`accessibility-engineer` was the roster's last planned "weak area" build
before returning to the two originally-planned "core strength" personas.
`tdd-coach` will move the orchestrator's terminal row again, to
"implemented," and needs a fresh no-cascade check when it does — the
terminal row now also carries the UI-touching accessibility-criteria
condition this session added, worth confirming that check still holds
once there's an implementation stage after it.

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

**A rendered choice needs a real pause, not a past-tense narration.**
`design-system` said to render candidates and "let the user pick," but a
live run generated three, screenshotted all three, and wrote one up as
"chosen" without ever actually stopping for an answer — the same
silent-decision failure this whole roster exists to prevent, just worded
in the past tense so it reads as though it wasn't one. Fixed by requiring
an explicit blocking question at the exact moment of choice, in both
`design-system` and `screen-design`. The lesson generalizes past this
persona: "present options" and "the user chose" are not the same
sentence, and a skill that only ever states the second can silently drop
the first.

**Draft renders are scratch until chosen; only the winner gets a
permanent record.** Fixing the finding above created a second problem:
every candidate's HTML and screenshot got persisted to the project's
artifacts *before* any question was even asked, cluttering the record
with options nobody picked. Now candidates render to a location outside
the project's own artifacts, open as live tabs for comparison, and only
after a real choice is made does the winner's HTML+screenshot get written
into `visual-ux/` — rejected candidates get a prose description and a
reason, never a saved file. The general shape: a comparison step and a
persistence step are different moments, and collapsing them means every
option gets treated as if it were the answer.

**An unresolved item that isn't this skill's job to fix is still this
skill's job to keep visible.** `screen-design` correctly never claims to
close the accessibility-criteria placeholder its slices carry (that's
`accessibility-engineer`'s job, once it exists) — but one run reported "no
open questions" anyway, making a real, still-unowned gap disappear from
view. Not owning something doesn't license hiding it: any unresolved item
named in an upstream artifact has to be carried forward into a
downstream one's own "Open questions" every time, or a project's own
stated policy (a placeholder stays visible until someone can actually
close it) gets violated by omission rather than by decision. Worth
checking any future persona that consumes an artifact with a known,
unowned gap for the same silent-drop risk.

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

**The predicted silent-drop risk materialized, in the exact artifact that
predicted it.** The finding above ends "worth checking any future persona
that consumes an artifact with a known, unowned gap for the same
silent-drop risk" — and `accessibility-engineer`'s own first real run
found exactly that: `screen-design-001.md`'s "Open questions" section
claimed "None left open" while the accessibility placeholder was still
genuinely open at the time it was written. Corrected in place rather than
left stale, with a note that the claim was wrong when written rather than
that the gap is still open now. Worth keeping as a second data point that
this failure mode isn't hypothetical — it has now actually happened once,
been named as a risk, and then actually happened again in a different
artifact before the risk note was even fully written.

**A markup-only accessibility check misses defects a driven one catches —
confirmed, not assumed.** `accessibility-review`'s synthesis named
"drive the artifact, don't just read it" as a principle before any real
run tested it. The dogfood run against `evals/example/` confirmed it
concretely: reading the mockups' CSS alone would have missed that the
design system's declared focus treatment was never actually implemented
(the one real interactive element silently falls back to the browser's
bare default outline) — a gap only a real `.focus()` call plus computed-
style inspection surfaces, since the *absence* of a rule doesn't look
different from its presence failing to render until something actually
asks the browser what it computed. The general shape: for any review
persona whose subject is "does this actually work," a check that only
reads source is a weaker claim than one that runs it, whenever running it
is genuinely possible.

**First `background: true` persona in the roster, and a partial answer to
the parallelizability question "Orchestrator v2" left open.**
`accessibility-engineer` has exactly one skill, and that skill never
blocks on `AskUserQuestion` (an ambiguous or AAA-level finding gets logged
as a preference, not escalated into a question) — the first persona here
where the *agent* itself, not just some of its skills, can be launched
async. This doesn't fully resolve the open question from "Orchestrator
v2" below (whether parallelizability should be a per-skill or per-agent
property still isn't testable against a real mixed-behavior persona,
since `devsecops-engineer` remains the only one of those and stays
`background: false` for its requirements half) — but it does mean a
second real reviewer now exists to eventually parallelize against, which
that note named as the actual blocker.
