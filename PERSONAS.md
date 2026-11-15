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
| 1 | `docs-writer` | Purposeful documentation — problem framing docs, light scope maps for problems too big to slice blind, ADRs, WHY-not-WHAT comments, user-story/PR write-ups, user-facing feature docs, the project README (`readme`, since 2026-10-25: from the manifest, the design and the slice, every command copied and run, never invented; the chunk loop's Definition of Done calls it at D and the smoke agent follows it on a clean clone), avoiding stale/ceremonial docs | Core strength | Done — `readme` is new with implementation flow v4 and has no eval case yet (PR 3); `problem-framing-doc`, `scope-map` and `user-story-writeup` have real cases (`evals/problem-framing-doc-payfine-phase1` and `-phase2`, two turns since 2026-11-15: the question, then the document; `scope-map-self-service`, `user-story-writeup-payfine-phase1` and `-phase2`, 15/15: the finished story after the filing answer) with the persona's save and skim rules moved into each skill; two fixes from them: a story isn't blocked by the slice's placeholders, and an assumed limit is an open question, not a constraint. The other five have real cases too (`adr-payment-gateway`, `adr-neg-rename`, `why-comments-collect-fine`, `pr-writeup-portal-fines`, `user-facing-docs-renewals`, `staleness-audit-docs`, plants in `evals/fixtures/library-app/docs-plants/`): `adr` opens with its three checks and stops at a "no"; `user-facing-docs` states only what it checked |
| 2 | `product-manager` | Pinning down WHAT before HOW — asking the user directly who benefits, what they want, and why for one unit of work, before any slice gets cut | Core strength | Done — `requirements-refinement` has real cases for both phases (`evals/requirements-refinement-payfine-phase1`, 14/15, which now requires the trade-off and rejected-alternatives questions; `-phase2`, 24/27: the written requirements keep the user's trade-off and draw each constraint's consequence); the persona's save, scope-boundary and first-response-is-questions rules now live in the skill. From phase 2 (2026-10-14): an answer that skips one of the questions is recorded as "Not yet confirmed" and asked again rather than filled in or dropped (3/3 record the section, 2/3 name the staff view in it), a question answered without every example is answered (the first version of the rule had the skill re-asking for a deadline after the user gave the why), and a finding names what a constraint forces and who owns it, not the code change (two runs in three had prescribed the member route; 3/3 after) |
| 3 | `product-slicer` | Vertical slicing & scenario-driven delivery — smallest end-to-end shippable unit for a confirmed requirement, acceptance-criteria quality, feature-shape YAGNI, scope-creep pushback | Core strength | Done — both skills have real cases (`evals/vertical-slicing-payfine-phase1` 18/18, `acceptance-criteria-payfine` 9/9); `vertical-slicing` gained the persona's save, hand-back-without-requirements, confirmed-scope-only and scope-map-step-in-title rules, and invokes `acceptance-criteria` before writing criteria; `acceptance-criteria` no longer settles an undecided outcome inside a rewrite. With no requirements doc it now stops before anything else, even when told to skip the conversation (`evals/vertical-slicing-no-requirements`, 12/12; before the fix it cut the slice with a note that the scope was its own call). Its hand-back path has a real case (`evals/vertical-slicing-handback`, 15/15): it had grown the slice and rewritten other stages' documents; it now decides the scope, sends any added capability to `requirements-refinement`, and edits nothing it doesn't own. The agent now lists `Skill`, which `vertical-slicing` needs to consult `acceptance-criteria` |
| 4 | `software-architect` | Option-Enabling/Clean Architecture watchdog — dependency direction, module boundaries, screaming architecture, catching both premature *and* missing abstraction; also owns technology selection, recommending rather than deciding — the starting set a first test forces, and what sits behind each boundary once one forces it | Core strength | Done — `architecture-review` is the first skill with a real `claude plugin eval` suite (`evals/library-app-*`, a shared 60-file fixture app other personas can plant defects in). Two skill-text fixes came out of it: the composition-root exemption now covers `main/` knowing both sides, not business code importing `main/` (both skills); and the shared foundation (importance test, four rules, state-the-ordering) now lives in each skill rather than only in `AGENT.md`, which the eval never loads and which a direct or inline skill invocation never loads either. `architecture-design` and `technology-bootstrap` followed (`evals/architecture-design-*`, `evals/technology-bootstrap-*`), so all three skills are on the real suite. From those: the persona rules a routed step needs (where to save, vocabulary) moved into the skills; consults invoke the consulted skill with the `Skill` tool and carry on after its answer; a delegation covers only what it names; and every design decision records its recommendation, rejected alternatives and how it was approved, fix-now-or-defer included. The agent now lists `Skill`, and its design path has a real case (`evals/architecture-design-payfine-via-agent`, 3/3 clean after a `map-query` fix). `technology-bootstrap`'s inline consult of `supply-chain-review` is now graded from the trace (18/18 kept runs). Its chain gained a rejecting ending (`evals/technology-bootstrap-phase3-reject`, 16/18: "npm and Jest", recorded as the user's choices with the recommendations declined and the pinning posture restated for npm), and the skill now defers the UI framework when the first test is domain-level, which the chain's phase 3 approves |
| 5 | `tdd-coach` | Turns a designed slice into working code test-first, and applies specifically-named fixes handed back from review, through the orchestrator's chunk loop. Two skills since 0.13.0: `tdd-implementation-lite` (the implementation contract — ownership, scope, gaps, report — as test-first with verification: tests before the code, seen failing on their assertions against a stub, shown to catch a deliberate break, the loop between left to the model; named by the chunk loop in every launch) and `test-quality-review` (critique existing tests — over-mocking, false positives, coverage-as-theater). The heavier `tdd-implementation` (TDD proper: a Test List, one test at a time, a `test-quality-review` call every cycle) was the default until 2026-11-06 and is retired: in the G2 experiment arm (2026-10-18) the first lite run cleared every contract grader and was preferred by the blind judge 18/18 on the slice case; on the second real run lite held all four verification steps unprompted. Follows Clean Architecture/OeA principles as a writing constraint (informed by `software-architect`'s already-decided boundaries); doesn't decide or verify architecture itself — `architecture-design`/`architecture-review` still own that | Core strength | Done — first persona that actually writes/edits application code, needing real execution tools (`Bash`) for it; the roster's second `background: true` persona, wired into `orchestrator` as the new terminal row. `tdd-implementation` 10/10 (three real fixes across the fill-vs-escalate rule for missing collaborators), `test-quality-review` 10/10 (a coverage-sweep fix); orchestrator's terminal row now runs the quarantine/grade/combine flow by default rather than a single inline build; not yet dogfooded against `evals/example/`. Real cases (2026-10-11): persona rules moved into both skills, `tdd-implementation-cancel-hold` 53/54 graded mechanically on the trace, `-named-fix` 3/3 clean, `test-quality-review-fines` 3/3 clean. The main agent used to write answers into the design before the skill loaded; the skill's and agent's descriptions now leave open questions to the skill (0/3 direct, 0/2 via the agent). `AGENT.md` is now the persona plus a pointer to its skills (the old TDD paraphrase predated every skill fix). Run directly, `tdd-implementation` ends with the same reviewers the orchestrator's grading step runs (architecture, code, security, reliability, accessibility for UI); under the orchestrator it skips them. Known gaps: through the agent, the subagent settles a design question the direct path leaves to its owner (`-via-agent` 48/60, the rest of its process comparable), and the quarantine flow has no case (it is proven by real runs: two so far, see H6 and I in `evals/TODO.md`). In the second real run (2026-10-19, compare policy) the lite candidate held all four verification steps unprompted on the agent path, but its tests read the adapter's private store to check the queue, which the test-quality reviewer rated High and the blind judge named as its reason for preferring heavy in both orders — the opposite of the eval's 18/18 for lite, one run against nine; the lite contract now says asserted through the public interface too, never through private state. 2026-11-06 (0.13.0): `tdd-implementation` and its five eval cases retired; `tdd-implementation-lite` is the one implementation skill, named by the chunk loop in every launch, with `test-quality-review` the builder's own check on its newest test; the heavy-versus-lite verdict waits for H5.4 only in the sense that lite's tests are audited there, and any heavy rule lite needs comes back as a lite rule |
| 6 | `code-reviewer` | Local code-level readability/DRY/naming/comments triage — not scope-YAGNI (`product-slicer`'s territory) and not structural abstraction (`architecture-review`'s), a severity taxonomy for findings; since 2026-10-24 also `external-review-triage`, one verdict per comment an external reviewer leaves on a pull request the chunk loop opened (fix, decline with the reason, defer, resolved), judged against the code as it stands, the slice's documents and this roster's own reports; since 2026-10-25 the chunk loop's one reviewer per chunk round, applying `code-review`, `test-quality-review` and by territory `reliability-review` in one launch and one report of at most eight Critical/High/Medium findings (a WHAT-comment or a planning-reference comment is Medium) | Core strength | Done — one skill, `code-review`, review-only like `accessibility-review`; the roster's third `background: true` persona; also uses the existing `why-comments` skill directly for its comment check rather than re-deriving it. Eval 17/17 (fixture expanded twice to cover the full checklist; one real fix, a duplication finding folding an exempt guard clause into "what's identical," caught, fixed, recurred on a larger fixture, then fixed for real with a concrete phrasing template). Real cases (2026-10-11): `code-review-fine-notices-pr` and `-catalog` clean, `-fines-report-pr` 13/15 after a sweep-every-function step; consults `why-comments` via `Skill`. It also flags code the change doesn't need (unused options, flags nothing sets, impossible-case checks, ceremony; `code-review-days-left-pr` 27/30), and fires on a general "review this PR" now that its description leads with the trigger |
| 7 | `devsecops-engineer` | A system's runtime safety properties — whether it can be attacked, and whether it can stay up. Threat-aware requirements & review, secrets/PII hygiene, least privilege, dependency & supply-chain risk, observability, resilience & failure handling, safe rollout/rollback | Borrowed/synthesized (weak area) | Done — all six skills are on the real `claude plugin eval` suite (`evals/security-review-*`, `evals/reliability-review-*`, `evals/supply-chain-review-*`, `evals/operational-readiness-*`, `evals/security-requirements-*`, `evals/reliability-requirements-*`, on the shared library-app fixture). Three skill-text fixes came out of it: pre-existing problems a change newly routes through still go in a separate non-blocking section; availability is a security finding only when one request costs out of proportion to its size (volume/capacity is `reliability-review`'s); an "opaque" log identifier is a surrogate id, never a card/account number or email. From `operational-readiness`: the first response is the situation questions, not a review; "how to check" steps that list everything that runs (a run that never starts needs a missing-completion alert) and every configuration variable's behaviour when absent; the output template requires a **Rehearsed** and a **Written down** line, each a finding when the answer is no. From the requirements skills: questions first, never what the code answers; decisions stay pending until approved, and a proposal already on the table is a decision whenever you'd change it; retry only transient faults; an accepted risk with a manual remedy needs its cases findable. Since 2026-10-14 approval comes before the document: after the questions, the next response is the forks (through `AskUserQuestion`, or all in one plain-text turn without it) and the document is written once, after, complete; every phase-2 run had written the whole document with its decisions pending (`evals/security-requirements-payfine-phase2` 11/12, `-phase3` 27/27 on the saved file; the reliability chain the same). A missing retry is a finding only when a transient failure loses something a retry would save; a read that fails cleanly is Low at most (`reliability-review-catalog` 2/3 vs 0/3 without the plugin, from no uplift) |
| 8 | `accessibility-engineer` *(optional)* | WCAG-minded UI review — keyboard nav, semantic HTML, screen-reader correctness. One skill, `accessibility-review`, verifying what `ux-designer` already rendered rather than designing anything itself; since 2026-10-25 also the chunk loop's smoke agent for a chunk that touches UI (start the app, drive the chunk's done check in the browser, check its criteria on the built screen, report in the shared format) and the stranger test at the slice review (a fresh clone, the README from its first command), with the full review itself running once at D | Borrowed/synthesized (weak area) | Done — cut if you don't do frontend work; the roster's first `background: true` persona, since its one skill never blocks on `AskUserQuestion`. Real cases (2026-10-11): `accessibility-review-payfine` 35/36 over 3 runs on a planted declined-state mockup (a regression guard: the baseline finds the plants too), `accessibility-review-payfine-subtle` 25/27 on defects only the cascade, a state or an id shows (the `:hover` contrast failure is found 2/3 with the plugin, 0/2 without, after the skill learned to check every state rule as its own pair), and a negative trigger; the persona's save, boundary and markup-only-fallback rules now live in the skill |
| 9 | `ux-designer` *(optional)* | Visual & interaction design — screen layout, component composition, and interaction flow for a slice's UI-touching parts, decided before code is written. Two skills, establish-once/apply-per-slice like `software-architect`'s: `design-system` (once per project, also handles review/evolve) and `screen-design` (per slice) | Borrowed/synthesized (weak area) | Done — cut if you don't do frontend work; hands off to `accessibility-engineer` for WCAG-correctness review, doesn't verify compliance itself. Real cases (2026-10-11): `design-system-payfine-phase1`–`3` (9/9, 12/12, 19/21) and `screen-design-payfine` (33/33; the baseline writes no mockups). The persona's save location, hand-backs and no-browser handling now live in both skills; calibration added a ratio for every text colour and kept scratch candidates out of `visual-ux/` |
| 10 | `architecture-cartographer` | Maintains a mechanically-derived map of the codebase's actual structure — real dependency graph, public exports, external packages, each module's importance tier as already decided by `architecture-design` — and answers "does something like this already exist" queries against it. Doesn't decide architecture, doesn't judge whether a flagged similarity is a real duplicate or coincidental, doesn't grade anything itself; supplies facts and mechanical flags, not verdicts. Two skills: `map-query` (read-only, consulted pre-write) and `map-update` (regenerate + diff against the prior map, post-write) | Infrastructure for the rest of the roster | Done — the roster's tenth and last planned persona, and its third `background: true` one; consulted inline by `architecture-design` and `tdd-implementation` the same way `software-architect` already consults `devsecops-engineer`, and wired into the quarantine flow's Grade/Finalize steps. Real cases (2026-10-11): the map has a fixed home, `docs/architecture-map.md` at the app root; `map-update-cancel-hold` 27/27, `map-query-consults` 3/3 clean, `map-query-no-map` 2/3 (3/3 after the consult fix: a consulted `map-query` hands its report back and the caller carries on, where through the architect agent the report had ended the turn) |
| 11 | `release-engineer` | Getting finished, reviewed work off the machine — push the slice branch, open the pull request with `pr-writeup`'s body, file the leftover findings as tracker issues, act on `external-review-triage`'s verdicts (push the fixes, reply to the declines, file the deferrals), and write the CI configuration a repository is missing, hardened (pinned action SHAs, least privilege). Owns git and hosting mechanics only; never decides what to build, never edits application code, never pushes to the default branch. Three skills: `delivery` (files only the standing Mediums; Lows stay in the pull request body), `ci-pipeline`, and since 2026-10-25 `repo-bootstrap` in its smallest form (`git init`, the default branch, `.gitignore`, a private `gh repo create` and the first push, each decided with the owner through `AskUserQuestion` and recorded in the technology-bootstrap document; the chunk loop's A step routes there when the target has no repository or no `origin`); `deployment` is phase 2 | Borrowed/synthesized (weak area) | Building (2026-10-24) — added with implementation flow v3 (`.synthesis/implementation-flow-v3.md` §4c, §4.E) to close the roster's post-implementation gaps; `repo-bootstrap` added with v4 after the second real run improvised the repository in the orchestrator's own turn. `devsecops-engineer` keeps its "never writes pipeline config" boundary and reviews the result through `operational-readiness` once a deployment path exists. All three skills run inline in the orchestrator's session because the push and the `gh` calls use the session's credentials and `repo-bootstrap` asks; the agent is `background: false` for that reason. No eval cases yet; the first real delivery was the first test of `delivery` and `ci-pipeline` |
| 12 | `chunk-runner` | Runs one chunk's round of the orchestrator's chunk loop on a context of its own: launches the builder, runs the gate (the builder's transcript replayed for shell edits and the commit rule), launches the combined reviewer and the smoke agent, records the rounds with `rounds_record.py`, launches the fixer and the regressions re-review, and hands back the chunk's log line and nothing else. Never asks the owner, never consults a persona, never writes the log, never commits the records; a `needs-decision` finding or a second gate failure comes back on its line. One skill, `chunk-runner`, which the agent invokes first. | Core strength | Done (0.14.1, 2026-11-08; the v4 design's D9 phase 2, built once slice 2 measured the orchestrator's thread at about 427k cache-read tokens per call and 44% of the slice's cost). Launched by the orchestrator's C step as `model: opus`, `maxTurns: 200`; the old `orchestrator-*` mid-chunk cases became `chunk-runner-*` cases (review round, one fix round, gate deviation, gate outside, the needs-decision hand-back), and two new orchestrator cases grade its side (the launch, the hand-back into the C line). Under the `light` cadence it runs the build, the gate and the smoke run only |

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
routing means invoking each routed skill in turn, in the same
conversation, with everything a routed step needs kept in the skill
itself (a persona's `AGENT.md` sits outside the project and isn't read). `ux-designer` is also `background: false` for the same
reason (both its skills block on `AskUserQuestion`); `accessibility-engineer`
is `background: true` but `orchestrator` still executes it inline like
every other row, since v1's routing is sequential by construction, not
because every persona it invokes requires it.

**`tdd-coach:tdd-implementation` is the one row that genuinely doesn't
execute inline — it runs the chunk loop (v4, 2026-10-25), wired in and
running by default.** A repository and an `origin` must exist (else
`release-engineer:repo-bootstrap`, decided with the owner). Before any of
this, and before the target question, the orchestrator's step 0 (session
setup; 0.14.0) asks nothing: the launcher `bin/kad` is the one way a flow
runs (it fences the session, turns audit mode on and approves the
permission set once per project), so a session under the sandbox runtime
is told so in one line and goes on, and a plain `claude` session is told
the one command to type (`kad` from the project's root) and stopped; a
session with no Bash cannot tell and goes on to the chunk loop's own
check. Nothing restarts, prepares or opens a window (0.13.1's relaunch
did, and lost two runs' transcripts). Before any planning document is read, the orchestrator asks the tracker
what is open (0.14.1): a pull request from a slice branch routes to the
external-review triage on every unresolved comment whoever wrote it (the
flow's own posts carry the footer `— kad-dev-team` and are the only ones
skipped), and an open Critical or High issue is one question to the owner.
The sandbox check (`skills/orchestrator/scripts/sandbox_check.py`) runs
first in the loop, before any question, and before every launch after
that: the plugin cannot ship the settings that fence an unattended code
writer, so the script probes the launcher's fence from inside it and reads
the escape hatches off in the settings; under the launcher a FAIL stops
the flow with no question. Then at most two questions, one per
`AskUserQuestion` call: the browser (a UI slice with no browser answering)
and the delegation, asked once per project and stored, whose "yes" is
written to `planning/delegation.md` and the per-slice file so a persona
can settle a mid-build decision without the owner. The A line carries the
cadence (`loop`, or `light` when the owner's message names the one
measured arm) and a budget (8 h for a UI slice, 5 h otherwise, 2 reviewer
launches per chunk, 1 fixer per scope plus 1 for regressions; consults
counted, never capped), counted at every chunk boundary. A slice branch is cut, the base recorded,
and the **design-readiness gate** (`readiness_check.py`: every criterion
and failure path homed in the design, a number on every wait, security
and reliability agreeing, a mockup per named state, no question routed to
the implementer, a "Kept for later slices" line, every open or deferred
item of the slice triaged as usable-without-it or a blocker that goes to
the owner, an unusable-reply row, and since 0.14.2 no value of a file the
owner provided anywhere in the documents or the code, which
`source_scan.py` finds from the `sources.md` listing and which goes to
the owner first) routes each failure back to the owning
persona before any builder is launched, and a new chunk-loop entry
carries the A line after the last route. One implementer (`model: sonnet`, since a plugin agent's own
`model:` line is not applied in practice) writes the chunk plan into the
implementation report, two to eight vertical chunks, each with its
criteria, files, done check (naming a **seam test** through the real
composition root with only the external service faked at its wire
boundary) and territories; then for each chunk one **chunk runner** (`chunk-runner`,
`model: opus`, 0.14.1) carries the round on a context of its own: a fresh
implementer builds the chunk on a short context, seam test first and
comments only where `why-comments` would keep one, and commits it under
the chunk's title; the mechanical gate (`validation_gate.py`: suite,
typecheck, lint, scope against the chunk's files plus the design's module
directories with in-module deviations reported rather than failed,
protected documents, coverage, report-only comment density and size
figures, the builder's transcript replayed for its shell edits and a
commit chained to its test run) runs on the commit range; then **two
launches, never more**: one combined reviewer (`code-reviewer`, `model:
opus`, applying `code-review`, `test-quality-review` and by territory
`reliability-review`, one report of at most eight Critical/High/Medium
findings) and one smoke run (`accessibility-engineer` in the real browser
with a screenshot per state for UI, `tdd-coach` over HTTP otherwise, the
app started through `scratch_run.py` with every data path inside a
scratch folder, never the owner's data). One fix round: a fresh fixer for
every finding, the gate, a regressions-only re-review on the fix's diff, a
second and last fixer for the regressions, the gate, done; pre-existing
findings stand (a Critical or High stops the loop, a Medium goes to the
pull request body); a `needs-decision` finding comes back on the runner's
line and the orchestrator launches the owning persona once with the
delegation file, which writes its own document and commits `Decision
<n>`, then relaunches the runner. `rounds_record.py` is the only thing
that parses a report; it writes the sidecar and prints the C line's
counts; the orchestrator keeps the records commit, the audit sync, the C
line and the budget. Under the `light` cadence the runner stops after the
smoke run and the findings wait for D, where each chunk's own builder is
resumed by message to fix them. At the end the map is regenerated with the shipped extractor, the
**Definition of Done** (`done_check.py`: README by `docs-writer:readme`,
linter and formatter, typecheck, no code in strings, no planning
references in code, comment density at or under 5%, persisted names, env
defaults, test padding) is met by one fixer batch, all six reviewers read
the whole slice diff once with one fix round (Lows allowed here, to the
pull request body under "Known Lows"; each criteria reviewer restates the
slice's accepted deferrals as findings), the **criteria walk** on a UI
slice (`accessibility-engineer` drives every acceptance criterion a
browser can reach in the real browser and writes the per-criterion table,
the screen-reader announcements the owner's only manual item), and the
smoke agent follows the README on a fresh clone; then `release-engineer:delivery` pushes the
branch, opens the pull request (body by `pr-writeup`) without asking,
files only the standing Mediums as issues, has
`code-reviewer:external-review-triage` judge the external reviewer's
comments (fix, decline with a reply, defer to an issue, up to five rounds),
writes CI on the first delivery that finds none (`ci-pipeline`), writes
the run's cost on the E line and syncs the audit material to the audit
repository when one is configured, all in the foreground. A context clear
mid-loop writes a handoff file the next invocation resumes from. Full
procedure in `skills/orchestrator/SKILL.md`'s own "The chunk loop"
section; the design and the evidence behind it in
`.synthesis/implementation-flow-v4.md` (v3 in `-v3.md` for what it
amends).
**Runs on every slice, no opt-in/opt-out judgment call** — no signal in
this roster's pipeline reliably predicts implementation risk, and
`product-slicer` already bounds the cost by keeping each unit at the
smallest shippable slice; a user who wants a specific slice built without
it says so directly, that's not a call this skill makes on its own.

**Why v2 (two candidates in worktrees, a blind pairwise judge, a combine
brief, a fresh finalize instance, a full re-grade) was retired.** The first
real run (personal-finance-tracker slice 1, 2026-10-19/20, reviewed
2026-10-24) showed the token sink was two heavy-loop instances whose
context grew to 788k tokens, not the reviewers; the judge was pure position
bias, each order preferring the implementation shown first; the second,
lite candidate was cheap and useful as an idea source but not worth a
judge; the one 79-file commit followed from the no-commit rule plus the
HEAD-based gate baseline; and the orchestrator's own briefs and digests
produced four of its errors. The chunk is the unit of build, validate,
commit and context reset; that one change answers all of them.

**v1 scope**: sequential stage routing across the full spine as it stands
today (problem-framing-doc → scope-map → requirements-refinement → slicing
→ user-story-writeup → architecture-design → security-requirements →
reliability-requirements → design-system → screen-design →
accessibility-review → technology-bootstrap → tdd-coach:tdd-implementation),
one step at a time, human checkpoint after each — and a hard stop once a
slice is designed, its runtime-safety criteria are filled, its screen
designed and accessibility criteria filled if UI-touching, the project has
a stack to build on, and the slice has been implemented, reviewed chunk by
chunk and whole, and delivered as a pull request (via the chunk loop above,
`code-reviewer` among its reviewers).
`devsecops-engineer`'s four review/posture skills, `code-reviewer`, and
`tdd-coach:test-quality-review` sit outside this spine entirely: they run
against code, a test file, or a repo that already exists, which most of
the spine never reaches (`test-quality-review` also runs inline inside
`tdd-implementation`'s own loop as a self-check, and again — alongside
`code-reviewer` — as one of the chunk loop's reviewers, none of which is a
spine stage).
Never cascades to the next scope-map step
automatically — each unit of work needs design/implementation before the
next one's shape gets decided, the same reason CAMS's own per-slice
workflow iterates rather than deciding every slice up front. Parallel
review-synthesis orchestration for artifacts *outside* the quarantine
flow — reconciling several specialist reviewers examining some other
single artifact — is still a different, larger problem, deferred below
until it has real personas to synthesize across.

**`orchestrator-log.md`, appended once per step 4 execution, is the
retrospective answer to "did it actually skip anything."** Raised by the
user while planning real dogfooding in a fresh project directory: a
graded final artifact proves the *output* is good, not that every stage
between problem doc and implementation actually ran rather than getting
silently skipped. One append-only entry per routed step (never edited —
a wrong entry gets a correcting entry, not a rewrite), richer sub-entries
for the quarantine row specifically (all five steps: both candidates'
worktrees/branches, per-candidate grading summary, the judge's verdict, the
combine basis and brief, the finalize artifact, the full re-grade's reviewers, findings and handed-back round) since that's the one
row a single "routed to" line would most successfully hide a skipped
step inside. Full format in `skills/orchestrator/SKILL.md`.

**Post-implementation gaps, surfaced in the same conversation, not yet
decided — four distinct things, not one, each with its own current
coverage (none) and its own reason nothing already covers it.** Distinct
from the CI/CD/hosting exclusion `technology-bootstrap` already
deliberately made ("infrastructure ahead of need") — that one is a YAGNI
call about a slice that doesn't need it *yet*; these are about a slice
that's now actually been implemented and needs to go somewhere real.

1. **Committing the code.** `tdd-implementation`'s own skill text already
   assumes an answer exists — "if the project already commits as part of
   how this work happens, keep the failing test and its implementation as
   separate, ordered commits... don't invent a commit discipline the
   project hasn't asked for." That's a real, deliberate boundary (don't
   assume a convention the project hasn't established) but it also means
   nobody decides *whether* or *how* a fresh project starts committing at
   all — the assumption only works once something already exists to
   follow.
2. **Opening a new repository.** No persona anywhere in this roster
   creates one. The whole roster assumes an "artifacts directory" already
   exists to work inside (`orchestrator` step 1 asks where one is or
   should be created, but "created" there means a directory, not a git
   remote or a hosting account) — repo creation as its own bootstrapping
   act sits entirely outside what anything here does.
3. **Writing CI/CD pipeline config.** `devsecops-engineer:operational-readiness`
   is the closest existing coverage, but it's explicitly a *review* skill
   — "Check whether something can be shipped safely," triggered "once
   there's a delivery path to review." It evaluates an existing pipeline's
   rollout/rollback/observability posture; it does not write one.
   `devsecops-engineer`'s own `AGENT.md` states outright it "never writes
   application code, infrastructure, or pipeline config" — so this isn't
   a small scope extension of an existing persona, building it would mean
   crossing a boundary that persona currently holds on purpose.
4. **Assessing infrastructure security.** `security-review` and
   `supply-chain-review` cover *code-level* security and dependency risk
   against a repo that already exists — neither reaches actual cloud
   config, IAM/least-privilege posture, or provisioned infrastructure.
   Nothing in the roster has ever looked at infrastructure-as-code or a
   live cloud account as its subject.

All four of `devsecops-engineer`'s review skills also sit outside the
orchestrator spine regardless of the above (event-triggered, hand off
only if the user asks) — so even the partial coverage that does exist
(operational-readiness's review of an *existing* path, once one's been
set up some other way) doesn't run automatically today. Decided after the first real end-to-end run (2026-10-24): gaps 1 to 3
become a new persona, `release-engineer`, because `devsecops-engineer`'s
"never writes pipeline config" boundary is held on purpose. Committing (1)
is the chunk loop's own mechanics (one commit per chunk, by the
implementer); pushing, the pull request, issue filing and external-review
triage are `release-engineer:delivery`; CI configuration (3) is
`release-engineer:ci-pipeline`, written inside the first delivery that
finds none; repository creation (2) and deployment are phase 2
(`repo-bootstrap`, `deployment`). Gap 4, infrastructure security, stays
open until a deployment exists to review.

## Deferred / phase-2 ideas

- **Orchestrator v2 — quarantine, grade, combine. Built, not deferred
  anymore.** See "Orchestrator" above for the shipped shape and
  `skills/orchestrator/SKILL.md`'s own "Quarantine, grade, combine"
  section for the real procedure. Two things from the original design
  note, settled on the way in: the Finalize step (originally an open
  question — layer fixes on the stronger candidate's worktree, or
  regenerate independently) went with **regenerate independently**, the
  user's own call when asked directly, over the cheaper layer-on-worktree
  option. Whether `tdd-implementation` is actually safe to launch async in
  practice is still confirmed only by design reasoning, not a real run —
  worth watching the first time this flow executes for real. The
  per-skill-vs-per-agent parallelizability question this note originally
  raised is still not fully answerable: `devsecops-engineer` remains the
  only mixed-behavior persona (an asking half and a non-asking half), and
  it's still `background: false` at the agent level for that reason —
  `tdd-coach` being uniformly `background: true` sidesteps the question
  for this flow rather than resolving it.
- **impl vs review split per persona — decided, for `tdd-coach` at least,
  and now settled for `code-reviewer` too: it doesn't get one.**
  `tdd-coach` gets exactly this split: `tdd-implementation` (write) and
  `test-quality-review` (critique), the same shape `software-architect`
  already uses for `architecture-design`/`architecture-review` and
  `devsecops-engineer` uses for its requirements/review pairs.
  `code-reviewer` was built review-only, one skill (`code-review`), the
  same single-trigger shape `accessibility-engineer` already uses — there's
  no corresponding write half for it to pair against inside this roster;
  the write half of the code it reviews is `tdd-implementation`'s job, a
  different persona entirely, not a sibling skill under `code-reviewer`
  itself.

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

### Current (2026-11-09): 0.14.2 merged; P5 next

The work list is `.synthesis/handoff-slice2.md`; its first section,
"Where the list stands", is the state. P1 (the launcher as the one way
in, 0.14.0, PR #41) and P2 with P3 (the criteria walk in a real browser,
the data rule, the chunk runner, the open-work routing, the triaged
deferrals, the counted shell edits, the light cadence text; 0.14.1, PR
#42) and P4 (planning data: nothing of the owner's by value; 0.14.2, PR
#44) are merged. P4 in one sentence: a planning
stage pointed at a file of the owner's lists it in `sources.md`, reads
its shape through `source_scan.py describe` and never a cell, and
invents every example; the same script finds a listed file's values in
the documents, the code or a branch's commits without printing one, as
the readiness gate's tenth check, the chunk gate's `sources` check and
`delivery`'s scan before every push; and `delivery` owns the one
procedure for taking a value out of history. Next: P5 (audit:
transcripts by session id, the cold read and the
mutation pass as tools), then slice 2's fix round on
`personal-finance-tracker-3` and slice 3 under `kad` with Chrome, the
`light` cadence and the chunk runner. The section below is the history
up to slice 2.

### Earlier: implementation flow v4 merged (PR 1 to PR 3, the launcher, the no-screen slice rule); slice 2 on 0.8.1 next

The audit of the second real run (`audit-docs`,
`personal-finance-tracker-2-slice-1/plugin-review/2026-10-25-*`) produced
`.synthesis/implementation-flow-v4.md` and the work list `TODO.md` at the
repo root. **PR 1, the loop, is merged (2026-10-26, #23)**: the
orchestrator's v4 chunk loop, the seam test and comments rule in both tdd
skills, the shared finding format and the combined review in the review
skills, the five new or changed scripts, `repo-bootstrap`, `readme`, the
agents, version 0.7.0. **PR 2, planning, is merged (2026-10-26, #24)**: the planning-skill fixes from the two
planning reviews (revise in place while the document is yours, the full
question pass, the three placeholders, a home for every criterion and
failure path, a number on every wait, owned documents stay owned, consult
answers and stage reports as visible text, one question per
`AskUserQuestion`) and `orchestrator_log_check.py` reading the v4 lines
and the chunk loop's entry across sessions; every PR 2 item in `TODO.md`
is ticked. **PR 3, evals, is merged (2026-11-01, #26)**: the twelve §11 cases as seventeen case
directories and one script check on the library-app fixture, the chunk
loop's states built for real by `code-plants/loop/state.sh` so each step
of the loop is resumed from a handoff and graded on its own, and
`cost_by_role.py`. The first calibration pass (2026-10-31) fixed two
real defects the cases caught: `rounds_record.py` read a smoke report's
bulleted Severity as no finding and said PASS, and the E step never
committed the log, so `delivery`'s clean-tree rule stopped every
delivery (E.1 now commits log and records). All seventeen bars are recorded
(2026-10-31, from the Mac once `evals/tools/gate.sh`'s `git` shims
existed; the loop cases' second pass found two more defects, the gate
command never allowing the loop's own log and a handoff resumed by
invoking `delivery` directly, both fixed). The stale re-record of the cases PR 1 and PR 2 touched is done (the evidence check green for all 68 cases), and the launcher `bin/kad` with delivery inside the fence is merged (2026-11-01, #27). What is next: (the owner's
rule being that v4 is done only once everything has been evaluated and
shown to work) slice 2 on 0.8.1, the version that carries all of v4 (PR 1 to PR 3, the launcher and the no-screen slice rule), with the budget line,
audited the same way, which decides D9's phase 2.

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
the emulated case's `eval-score/summary.md` (in git history).
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

### `tdd-coach` built, the first of the two originally-planned "core
strength" personas after the weak-area detour

**`tdd-coach`'s shape was worked out in a planning session before any
sources were read for it** — this roster's first time doing that, since
`tdd-coach` is also this roster's first persona whose scope collided with
an already-recorded deferred idea (the "Dev-agent quarantine/grade/combine
cycle") rather than starting from a clean roster row. Decided there:
`tdd-coach` stays named for the discipline it enforces, not the mechanical
act of writing code — same naming logic as every other persona here — and
gets two skills, `tdd-implementation` (write a designed slice via genuine
Red-Green-Refactor; also applies specifically-named fixes handed back from
any reviewer, through the same loop) and `test-quality-review` (critique
existing tests, standalone-capable and reused unmodified as one of several
parallel checkers grading each candidate implementation in the restored
quarantine/grade/combine flow — see the Orchestrator v2 entry above).

**The three-source synthesis ran next, and personal skills contributed
real content for the first time** — every prior synthesis in this roster
(`ux-designer`, `accessibility-engineer`, `software-architect`) reported
"nothing found" for its own topic in `~/.claude/skills` and every
project-level `.claude/skills` under `~/Documents/*`; this one found
`tests-audit` supplying mutation testing / false-positive detection and a
TDD-adherence-via-git-log method, neither present in CAMS or Flexion. Two
contradictions resolved: review cadence (CAMS runs the test-quality check
every single RGR cycle; Flexion runs it once per finished Test List —
resolved toward CAMS's tighter cadence, since a cheap static check costs
little run often and catches a bad pattern before more cycles build on
it) and coverage target (100%, the position two of three sources hold
independently, over Flexion's 95%/90%). One genuine scope boundary, not a
contradiction: Flexion's `oea-refactorings` runs no tests during its
whole-module split/merge refactorings, which only looks opposed to every
TDD source's "test after every refactor" — it's a different activity at a
different grain, governed by a different process. `tdd-implementation`'s
Refactor step stays at small, in-module Fowler-refactoring grain only;
anything crossing a module boundary escalates to `architecture-design`
rather than getting redrawn unilaterally. Full reasoning in
`.synthesis/tdd-coach.md`.

**Built and wired.** `AGENT.md` plus both `SKILL.md`s written from the
synthesis; `orchestrator` updated with a new terminal row
(`tdd-coach:tdd-implementation`, after `technology-bootstrap`) and a
fresh no-cascade check confirming the UI-touching accessibility-criteria
condition this roster's prior session added still holds now that there's
an implementation stage after it — it does, since the terminal condition
now requires implementation on top of every earlier condition rather than
replacing any of them. `tdd-coach` is `background: true`, like
`accessibility-engineer` — neither skill blocks on `AskUserQuestion`,
since a design gap escalates to whichever persona owns that decision
instead of a live question — which is the actual precondition the
Orchestrator v2 quarantine flow needs: two isolated `tdd-implementation`
instances, launched as real async `Agent` calls, blind to each other.
**Eval cases run for both skills, written from `AGENT.md`/`SKILL.md` text
before any real dogfood output existed**, per this plugin's established
order. `test-quality-review`: **10/10 PASS, reached across three runs.**
A case-authoring bug first (a bare `vi.spyOn` with no `.mockReturnValue`
chained on doesn't replace behavior, so the intended Critical-tier "mocks
the code under test" trap wasn't actually one), fixed. Then a genuine,
diagnosed skill-text gap, not smoothed over as variance: `formatReceiptLine`'s
missing coverage was caught on the first-ever run of this fixture, then
missed on the next one. The reason wasn't random — `SKILL.md`'s "Missing
coverage" category sat as one item in a prose list of things to notice
while judging individual tests, but missing coverage is structurally
different (it's about what's *absent*, not what's present in any one
test), so nothing forced a systematic sweep and it lost out to a more
novel finding that run (the model independently worked through a
validator's actual logic and found it backwards from what its own test
expected). Fixed by adding an explicit, separate "sweep for missing
coverage first, mechanically" step to `SKILL.md`, ahead of the per-test
categories — re-run, and the sweep also caught a second gap
(`calculateTotal`'s multi-item summing, never asserted) no prior run had
found at all. Full sequence in
the emulated case's `eval-score/summary.md` (in git history).

`tdd-implementation`: **10/10 PASS, reached across six runs**, three of
them real skill-text fixes rather than case-authoring corrections — the
sequence is worth keeping in full in
the emulated case's `eval-score/summary.md` (in git history) since it's a
durable lesson, not just a pass/fail log. In order: (1) a case-authoring
bug (a grader wrongly read a legitimate injected-collaborator assertion
as an implementation-detail leak), fixed. (2) A genuine gap —
`test-quality-review` ran inline every cycle but was only literally
*named* as such from partway through; `SKILL.md` already asked for this
by name, nothing enforced it — fixed with an explicit "name it every
time" instruction. (3) A second genuine, more debatable gap, surfaced to
the user before fixing since it hinged on real judgment: the persona
correctly recognized an already-approved rule covered a new-looking
scenario for free, but didn't separately flag that *reusing that rule's
messaging* for the new case was its own judgment call — fixed in
`AGENT.md`. (4) That fix over-generalized: the next run applied the same
"recognize reuse" reasoning to *structure*, silently deciding a new
interface should exist rather than escalating it — a real regression on
`stays-within-already-decided-boundaries`. (5) The first attempted
correction ("any new interface is always load-bearing, never fill it")
over-corrected the other direction — surfaced to the user before further
changes, since the evidence was concrete: the model refused to implement
`AssignCase` at all rather than fill an obviously-necessary, mechanically
implied collaborator. (6) Rewritten to split the question in two — does a
collaborator need to exist at all (often mechanically forced by an
already-approved decision, safe to fill with a minimal placeholder using
an established analog's shape) vs. is there a real structural fork about
it (reuse vs. build new, one port vs. two — escalate that, by name, while
still building the placeholder) — and the final run built `AssignCase` in
full *and* correctly escalated the one genuine structural question this
slice actually raised. This is the version shipped in `AGENT.md`. Full
detail, run by run, in the case's own `eval-score/summary.md`.

The Bash-restriction structural gap `tdd-implementation` has and
`test-quality-review` doesn't (a static read of a given test file needs
no real tool use) — a dry run can't verify "run things for real,"
only the narrated reasoning around it — is recorded in
`evals/README.md`'s "Known coverage gaps." Not yet dogfooded against
`evals/example/` — still ahead, and the only way to close that gap for
real.

### `code-reviewer` built — the second and last of the two originally-planned "core strength" personas

One skill, `code-review` — no impl/review split, review-only like
`accessibility-review`, the roster's third `background: true` persona.
Synthesized from Flexion's `code-review-protocol` and `pragmatic-reviewer`
(plus a second, differently-scoped `code-reviewer` agent template in
Flexion's `flexpowers` plugin), personal skills' own `code-review` skill,
and CAMS's `cams-refactoring` (by far the richest source — the only one
with a developed mechanical checklist at this exact granularity: function/
class size anchors, parameter-count thresholds, primitive obsession,
feature envy, data clumps) and `cams-code-review` (workflow-adjacent, read
for signal rather than as a review procedure). Full synthesis in
`.synthesis/code-reviewer.md`.

Two contradictions, both resolved toward precedent this roster had already
set before `code-reviewer` existed — confirming those calls a second time
independently rather than opening them back up. No source's severity
vocabulary or anchor survived unmodified (Flexion's L×I×E quantitative
rubric is the exact apparatus this roster had already rejected twice;
personal-skills layered three simultaneous scoring systems where one
qualitative call would do; CAMS anchored severity to whether a smell
blocks the *current* task, an implementer's-eye view rather than a
reviewer's) — resolved to this roster's existing Critical/High/Medium/Low,
re-anchored to cost to a future reader/editor, the same anchoring move
`architecture-review` and `accessibility-review` already made for their
own domains. Personal-skills' `code-review` applies its own fixes after
approval — resolved the same direction as `test-quality-review`'s
identical contradiction: report and hand back, never edit, since this
roster has a real implementer to hand back to
(`tdd-coach:tdd-implementation`) that those personal skills were never
built assuming existed. A third decision, not sourced from any
contradiction: comment review stops at the existing `why-comments` skill's
altitude rather than adopting CAMS's deeper `writing-for-agents`-gate
layer for surviving comments — a real idea, but CAMS's own ecosystem tool,
not something this portable roster already owns or has a concrete case
demanding yet.

Eval: 17/17 PASS, four runs — expanded twice past the first pass to
actually validate the whole skill rather than a sample of it. The
original fixture (`orders.ts` alone, 7 graders: duplication with an
exempt guard clause, a misleading retry-count comment, a legitimate
WHY-comment that must survive, a dead cryptically-named function,
pre-existing untouched code, a Stripe SDK instantiation that's
`architecture-review`'s call not this skill's, and `skill-invoked`) passed
6/7 on its first run, catching a real skill-text gap via an independent
judge agent, not self-grading: the duplication finding folded the exempt
guard clause into "what's identical." Fixed once, re-verified 6/6 on a
second run.

Asked directly whether that coverage actually validated the skill "in its
entirety," the honest answer was no: three checklist items (primitive
obsession, feature envy, data clumps) had no grader at all, and several
stated rules were never exercised in both directions (the 2-instance
threshold, size-as-a-prompt-not-a-gate, wrong-name-vs-vague-name severity,
test-file scope, local-vs-handed-off duplication). Expanded the fixture
with two more files (`pricing.ts`, `pricing.test.ts`) and 10 more graders
to close every one of those gaps — deliberately excluding a
`product-slicer`-handoff fixture, since no realistic code-only trigger for
"should this capability exist" was found that wasn't just relabeled
dead-code or premature-abstraction, both already covered.

Running the expanded fixture surfaced the same duplication gap again —
15/16 substantive graders passed, but the guard-clause-folded-into-
identical failure mode recurred verbatim on the larger, busier task
("same shape — null guard, weight-based cost..."), proving the first fix's
abstract wording wasn't actually robust, just untested against enough
variation. Strengthened with a concrete before/after phrasing template
(what not to write, what to write instead) rather than another abstract
rule. Final run, fully re-emulated, all 16 `llm` graders independently
re-judged (four judges, four criteria each, to avoid both self-grading and
repeating the full fixture text 16 times): 16/16 PASS, including the
twice-failed one, now correctly excluding the guard clause by name. This
run also self-reported the "Skills consulted" line correctly — an earlier
intermediate run had dropped it, the same one-off mechanical-miss category
already recorded for `accessibility-engineer:accessibility-review`, not
reproduced on the run that became canonical. Full four-run sequence in the
case's `eval-score/summary.md`.

Wired into `skills/orchestrator/SKILL.md`'s quarantine-flow Grade step,
replacing the placeholder note that had been waiting there since
Orchestrator v2 shipped, and into the event-triggered-skills list
alongside `test-quality-review`.

### Next: the real end-to-end dogfood run

Both of the roster's two remaining builds are done: `code-reviewer` above,
and `architecture-cartographer` below — built concurrently in separate
sessions against this same plan. With the full ten-persona roster built,
one real next step is left, already decided rather than invented fresh:

1. **A real end-to-end dogfood run, in a fresh project directory the user
   is setting up for this — not `evals/example/`.** `evals/example/` is
   markdown artifacts up through `screen-design`, never real running code
   or a real git history, so it can't exercise the part that actually
   needs testing now: real async `Agent` worktree launches, real parallel
   grading, a real `orchestrator-log.md`, and `code-reviewer` actually
   sitting in the Grade step instead of a placeholder note. This is the
   first time the quarantine flow, the audit log, and every reviewer —
   including `architecture-cartographer:map-update`'s own two invocation
   modes inside it — run together instead of being reasoned about.
2. **Post-implementation gaps (commit / new repo / CI-CD / infra
   security)** — decided after step 1, with real evidence of what a
   finished slice actually needs next, not before. Already recorded this
   way above; restated here so this list reads as the actual plan, not
   disconnected notes.

### `architecture-cartographer`'s shape, planned ahead of its own turn

**The gap it closes, diagnosed by the user, not assumed.** Every reviewer
this roster has built so far was deliberately scoped away from
whole-codebase awareness, for good reasons that each still leave a real
hole: `architecture-review` reviews only the current diff ("On legacy
code you didn't just touch, review only what changed" — the Boy Scout
Rule, on purpose, to avoid demanding total compliance on every touch).
`code-reviewer` is scoped local — file-level DRY/naming, not
structural. `tdd-implementation` only knows what's in its own task; a
helper that already exists three modules over is invisible to it unless
something tells it. None of that was a mistake — each boundary was the
right call for what that persona owns — but stacked together they leave
nothing that knows "does this fit the shape of what's already here,"
either at write time (would this duplicate an existing module or helper)
or at review time (does this new dependency edge violate the direction
the rest of the codebase already established).

**Mandate: maintain the facts, not the verdicts.** A mechanically-derived
map of the codebase's real structure — the actual import/dependency
graph, each module's public exports, external packages in use, and each
module's importance tier as `architecture-design` already decided for it
per slice (its own "Importance ordering assumed" section, already
produced today, just never persisted anywhere past one design doc). The
map answers two kinds of question: "does something like this already
exist" (a structural query — a comparable module/interface/boundary — or
an implementation query — a comparable function/helper), and "did this
change move in the wrong direction" (a new edge pointing from a
higher-tier module toward a lower-tier one, mechanically checkable once
tiers are already recorded, not a fresh judgment call).

**Explicitly does not decide, judge, or grade — that would swallow
`architecture-design`'s and `architecture-review`'s jobs, not complement
them.** Two failure modes it's built to avoid: deciding architecture
itself (not its call, ever — it reports what's already been decided and
what's already been built, nothing more), and declaring a flagged
similarity a real violation on its own authority. Two modules that look
alike can be a real duplicate or coincidental — driven by different axes
of change, destined to diverge — and telling those apart is a judgment
call for whichever persona already owns that call downstream
(`architecture-review` for a structural flag, `architecture-design` for
a query at design time). The cartographer surfaces the candidate; it
never declares the verdict. This is also the answer to the "deterministic"
requirement from the conversation that produced this plan: the graph
itself is mechanically extracted (real imports, real exports), not an
LLM narrative summarizing the codebase from memory — a narrated
architecture summary would just be one more thing that drifts from
reality and gets trusted anyway, worse than not having one.

**Two skills, matching the two distinct triggers.** `map-query` —
read-only, consulted before code exists for a query, at whatever
granularity the asking persona already operates at. `map-update` —
regenerates the graph from the real codebase and diffs it against the
prior map, run after code changes; its own output (the diff, plus
mechanically-flagged candidate duplicates and direction changes) is what
downstream reviewers read, not a third skill built just for them.

**Three consumers, the requirement this plan was explicitly asked to
satisfy — one skill each, no overlap:**
- `architecture-design` consults `map-query` before writing a design doc,
  at the structural level it already operates at — does a comparable
  module or interface already exist, should this slice's need reuse it
  or introduce something new. This is the consult that would have
  prevented the exact mid-implementation escalation `tdd-implementation`'s
  own eval run hit (discovering only during implementation that a new
  `CaseRepository` might duplicate an existing `CaseDirectory`) by
  answering it before the design doc was ever written.
- `tdd-implementation` consults `map-query` before writing code, at the
  implementation level it already operates at — does a comparable
  function or helper already exist, below `architecture-design`'s own
  conceptual altitude ("no function signatures, no code," per its own
  scope) but squarely inside what `tdd-implementation` writes.
- Reviewers (`architecture-review`, `code-reviewer`) read
  `map-update`'s diff output after code exists — a cheap, pre-computed
  starting point instead of re-deriving the whole graph on every pass,
  the "grade a slice's fit without walking an ever-growing codebase"
  half of the original idea.

**Wiring, reusing patterns this roster already has rather than inventing
new ones.** `map-query` consults the same way `architecture-design`
already consults `devsecops-engineer` inline today — no new orchestrator
spine row, a persona loading another's narrow skill in the same
conversation and handing control back. `map-update` slots into the
quarantine flow's own existing structure: once per candidate inside Grade
(a throwaway, worktree-scoped diff informing that candidate's reviewers),
and once for real after Finalize (the persistent map, the one
`architecture-design`/`tdd-implementation` consult on the next slice).
Neither needs a new top-level spine row in `orchestrator/SKILL.md`.

**Genuinely open, deferred to synthesis and build, not guessed at now:**
the exact mechanical extraction method per language (a portable,
grep/import-statement-based approach that needs no per-project tooling
installed is the current lean, over depending on a language-specific
static-analysis tool that may not exist in every target project); the
map's exact file format (structured data plus a short derived narrative
is the current lean, not a third possibility); whether `map-update` ever
hits a case ambiguous enough to need `AskUserQuestion` (current read: no,
it reports facts and mechanical flags, the same reasoning that makes
`accessibility-engineer` `background: true` — but worth confirming once
real cases exist, not assumed). Full three-source synthesis — this
plan's reasoning is not that synthesis — is still ahead, the same order
`tdd-coach`'s own shape-then-synthesis followed.

### `architecture-cartographer` built, the roster's tenth and last planned persona

The three-source synthesis ran against the shape already decided above.
**Flexion** contributed the corpus's only real, working implementations of
mechanical codebase-structure extraction — `duplication-candidates.py` and
`dependency-graph-gen.py`, read in full alongside their governing
`references/dependency-rule.md` and the `DUPLICATION` section of
`references/condition-types.md`, plus the orchestrating
`fleet-worker/agents/condition-checker.md` that consumes both tools'
output, and a contrasting standalone skill
(`oea-dependency-evaluator/SKILL.md`) with no upstream tier input of its
own. A promising-looking early grep hit
(`flexion-adapt/skills/discover/references/discovery-catalog.md`) turned
out to be a different domain entirely — an organizational digital-twin
catalog, not code — read, then discarded rather than stretched to sound
relevant. **Personal skills** contributed nothing on point, the same
finding shape as `ux-designer`'s, `accessibility-engineer`'s, and
`software-architect`'s own syntheses (`tdd-coach`'s synthesis remains the
one exception in this roster) — `code-review`'s and `deep-pr-review`'s
local, single-pass DRY checks were the only hits, and that territory
already belongs to `code-reviewer`, not this persona. **CAMS** contributed
`ui-component-catalog/SKILL.md` in full — the single strongest, most
directly-on-point precedent found anywhere in the corpus for this
persona's "does something like this already exist" half — plus
`cams-architecture/SKILL.md` (read for its grep-based extraction technique
underneath the procedure) and `cams-refactoring/SKILL.md`'s duplication
procedure; `cams-dataflow` and `cams-query-builder` were opened and
confirmed not relevant.

Four things resolved. First, whether this persona should ask the user
about relative importance or take tiers as given — two Flexion sources
disagreed sharply, but the disagreement dissolved once what each tool has
*available* was accounted for: the standalone skill with no upstream tier
source has to ask, while `dependency-graph-gen.py` runs inside a pipeline
where a human already adjudicated tiers once, elsewhere, and just applies
that decision. This roster's own pipeline already matches the second
shape — `architecture-design` assigns strategic-vs-tactical importance
per slice today — so tiers are persisted, never re-derived or re-asked;
an unclassified module renders explicitly **untiered**. This also settled
the `background: true` call PERSONAS.md's own planning section had left
as "current read: no, but worth confirming": nothing this persona does
ever turns on information only a human can supply in the moment, now
backed by an independent source's own explicit design choice rather than
derived in isolation a third time (see Durable findings below). Second and
third, the extraction method and map file format PERSONAS.md's planning
section had left genuinely open both turned out to be confirmations
rather than open contradictions — both usable sources independently land
on grep/import-statement regex by file suffix with no installed tooling,
and on a structured per-module table plus a short derived narrative.
Fourth, severity — sharper than this roster's usual "no quantitative
apparatus" stance, not just a repeat of it: neither usable source attaches
any severity, numeric or qualitative, to a structural fact itself, so this
persona carries none at all, not even this roster's own usual
Critical/High/Medium/Low scale — that scale describes a judgment about a
finding's consequence, and this persona never reaches that judgment for
anything. Full reasoning in `.synthesis/architecture-cartographer.md`. The map's
location, originally resolved per project by whichever consulting persona
could ask, is now fixed at `docs/architecture-map.md` at the app root (the
user's call, 2026-10-11).

**Built and wired.** `AGENT.md` plus both skills' `SKILL.md` written from
the synthesis. `architecture-design` and `tdd-implementation` each gained
a "Check what already exists first" section consulting `map-query` inline
— the same advisor-consult pattern `architecture-design` already uses for
its `devsecops-engineer` question, at the structural level for the former
and the implementation level for the latter. `architecture-review` gained
a section reading a precomputed `map-update` diff when one's handed to
it, without treating any flag in it as a substitute for its own judgment.
`orchestrator`'s quarantine flow gained `map-update` at both points
PERSONAS.md's plan named: a throwaway, worktree-scoped run per candidate
inside Grade, and a real run against the actual working tree after
Finalize that becomes the persistent map the next slice reads — plus the
`orchestrator-log.md` sub-entry format extended for both. None of this
added a new top-level spine row, exactly as planned.

**Eval cases run for both skills, written from `AGENT.md`/`SKILL.md` text
before any real dogfood output existed**, per this plugin's established
order. `map-query`: **6/6 PASS on the first run**, no skill-text fix
needed — its fixture's deliberate traps (matching an `OrderRepository`
query against a differently-named `CaseDirectory` purely by shape rather
than literal name; a teammate mentioning an unincorporated branch to test
whether a given map gets silently trusted as complete) both worked exactly
as intended. `map-update`: **6/6 PASS on the first run**, also no
skill-text fix — its fixture's three traps (tier carry-forward vs. fresh
assignment vs. an honest `untiered` for a module named in neither source;
a duplication candidate pair flagged without a merge/keep verdict; a
wrong-direction edge flagged by tier comparison alone, never turned into a
question or a severity label) all worked as intended too. Neither skill
needed a fix — the strongest first-pass result of any two-skill persona
built in this roster so far, plausibly because the mandate is mechanical
fact-reporting rather than a judgment call, leaving less room for the kind
of interpretive drift that produced real, multi-run fixes for
`tdd-implementation` and `test-quality-review`. Full sequence in each
case's own `eval-score/summary.md`.

### Evals moved to the real CLI; four skills migrated, next is `operational-readiness`

`claude plugin eval` is out of early access and works here. The first real
suite, `evals/library-app-*`, reviews a shared 60-file fixture app
(`evals/fixtures/library-app/`, with an answer key of 15 planted
violations and 9 traps) and replaced the emulated
`software-architect:architecture-review` case plus six inline-snippet
cases. Building it took three generations; the procedure that works is
now the playbook in `evals/README.md`, the fixture rules are in the
fixture's own README, and `evals/tools/new-case.sh` scaffolds a case.

`devsecops-engineer:security-review` was the second skill migrated
(`evals/security-review-*`, seven cases, 100% with the plugin on Sonnet
after three calibration passes and three skill-text fixes; details in
`evals/README.md`). The suites stay pinned to Sonnet: one Opus pass of
the architecture suite cost more and showed a smaller with/without delta.

`devsecops-engineer:reliability-review` was the third
(`evals/reliability-review-*`, eight cases including an agent-path case
and two negative triggers; every scoped case passes with the plugin except
the clean-module restraint case, which passes half the time in both arms
and is recorded as a known gap). Before it, a cleanliness pass moved the review standards,
stop rules and consult-mode rule out of `devsecops-engineer`'s `AGENT.md`
into its skills, keeping hand-off routing in the agent. Interactive skills
are no longer stuck on the `agent-eval` stand-in: `context.history_file`
chains one case per answer (`evals/README.md`, "Interactive skills").

`supply-chain-review` was the fourth (`evals/supply-chain-review-*`,
nine cases including the first phase-chained pair, built on
`context.history_file`); the base-image tag is its flaky spot.

Next, in order: `operational-readiness`
(phase-chained from its first turn), then `security-requirements` and
`reliability-requirements` (a slice-document fixture, fully phase-chained),
then the `devsecops-engineer` routing suite (named, unnamed, and
ambiguous-between-its-own-skills requests). A `runs: 3` pass of any real
suite is still unpaid; every number in `evals/README.md` is one run per
arm.

**Noted, not scheduled: `orchestrator` verifies a raised finding before
anything acts on it.** The reliability suite's clean-module case showed a
reviewer inventing problems about half the time, with or without the
plugin: on a module with no real defect it rated a speculative concern
(a missing bulkhead, a retry on a read) Medium or High. The skills already
tell reviewers to verify their own Critical/High findings, and on Sonnet
that self-check doesn't hold. The idea: between a reviewer's report and
anything acting on it (`tdd-implementation` applying fixes, the quarantine
flow's Grade/Combine steps in `skills/orchestrator/SKILL.md`), `orchestrator`
runs a separate verification pass over each Medium-or-above finding. That
pass gets the finding and the code, not the reviewer's reasoning. It checks
that the stated mechanism exists, checks any scale or capacity claim against
what the repo states, reproduces it with a test or a run where that's cheap,
and returns confirmed / downgraded / not substantiated. Only confirmed
findings get acted on; the rest are reported as hypotheses. Open questions:
who verifies (the same persona reloaded with a verify-only prompt, or a
neutral checker), what it costs per review, and whether findings below
Medium skip it. The three `*-catalog` restraint cases are its ready-made
eval: review plus verification should end with nothing above Low.

## Durable findings

- **An eval that exercises only `SKILL.md` finds what `AGENT.md`-only
  text never reaches.** `architecture-review` ran without the four-rule
  definitions and the state-the-ordering instruction under `claude plugin
  eval`, because those lived only in the agent prompt, and so it also ran
  without them on every direct `/skill` invocation and inline consult.
  Rule since: anything a skill needs to behave correctly lives in the
  skill; `AGENT.md` carries persona stance and routing, and points at the
  skills for the rules. The same suite showed the composition-root
  exemption was too lenient (both arms argued, correctly, that a use case
  importing `main/wiring` depends on everything wiring imports); fixed in
  both architecture skills.
- **Verified on Fable is not verified on Sonnet; pin the eval model and
  write skills a mid-tier model can apply.** With no `execution.model`,
  the architecture-review suite ran on the session default (Fable) and the
  skill fired 9/9 with the baseline matching it everywhere. Pinned to
  Sonnet, the skill fired 5/9 and missed half the smells it names. Fixes
  that worked: a description that says *invoke first, before reading
  code, for any request shaped like X*, and a concrete "how to check" next
  to every smell the skill lists (cycles: value-position vs type-position
  imports; mixing: label each line policy or mechanism; premature:
  count implementations and ask what the interface isolates). Every real
  case now pins `execution.model: sonnet`; a skill that only recognises a
  smell on a strong model hasn't encoded the principle yet.
- **Hand-written answer-key graders mostly measure the grader.** Two
  generations of snippet cases failed on vocabulary checks, one-framing
  assumptions, fixtures that leaked the answer in comments, and accidental
  bugs the no-plugin baseline got credit for finding. What gave signal:
  a realistic fixture with no hints, substance-only graders (found it /
  didn't flag it) derived from an answer key, traps for every principle
  with a wrong-looking side, and a blind pairwise judge whose reasoning is
  kept. Baseline Sonnet matches the skill on planted defects at one run;
  the uplift to look for is scoping, documented tradeoffs and stated
  ordering, and the pairwise judge's preference for breadth is a property
  of the judge, not a verdict on a deliberately narrow skill.

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

**No source has any precedent for racing parallel implementations —
every source converges on one implementation, many independent checks.**
The "Dev-agent quarantine/grade/combine cycle" imagined 2-3 isolated
implementer instances per slice, graded, then combined. A targeted survey
of all three sources specifically for this — CAMS's `*-impl`/`*-review`
agent pairs and its `cams-development-workflow` orchestration, Flexion's
`orchestrator`/`code-review-orchestrator` and `flexion-oea-coder`'s
`program`/`fleet-worker`, and personal skills' `deep-pr-review` — found
the pattern nowhere. CAMS's impl agents chain *sequentially*, each
building on the prior's output; parallelism there exists only among
*reviewers* running concurrently against one finished diff. Flexion's
`fleet-worker` runs a single implementer per unit, with independent
fresh-context sub-agents auditing that one output at fixed checkpoints
(sometimes by 3-agent vote, escalating to 5 on a true split), and states
the reasoning plainly: *"the agent that wrote the adapters cannot
objectively evaluate its own work."* Personal skills' `deep-pr-review` —
the closest thing to a real precedent for isolated parallel agents in
this whole corpus — parallelizes *review* subagents (some
`isolation:"worktree"`) against one PR, never competing implementations.
**First pass at resolving this folded the quarantine idea away entirely
— wrong call, corrected.** Absence of a source precedent isn't the same
as absence of value, and the user explicitly wants the racing-
implementations mechanic kept: this is the user's own judgment
overriding what the sources modeled, the same kind of move this roster
already made once before when no source addressed threat modeling or
rollback and both got supplied rather than left out. What the research
*does* change is the grading mechanism inside the flow: each candidate
gets graded by the already-validated single-implementation-many-
independent-reviewers pattern, run once per candidate, rather than a new
apparatus invented for racing implementations specifically. See
"Orchestrator v2 — quarantine, grade, combine" above for the corrected,
concrete flow — two candidates, graded independently, one accountable
combine decision, one fresh instance to finalize.

**A rare three-way convergence, strong enough to treat as settled rather
than synthesized.** CAMS's `cams-unit-test-reviewer`, Flexion's
`unit-test-reviewer`, and personal skills' `tests-audit` — three
completely independent sources — all separately name the identical
top-severity failure: mocking the code under test invalidates the test
and is rated Critical (or the equivalent highest tier) in all three. This
is the strongest cross-source agreement found for any persona in this
roster so far, and it's what settled `test-quality-review` as a real,
validated skill rather than a guess. CAMS's own false-positive guard for
this rule is worth keeping too: spying on a named test-double class
(`Mock*`/`Fake*`/`Stub*`) is not "mocking the subject" and must not be
flagged as though it were.

**Two more contradictions resolved toward this roster's own precedent,
not the sources — the pattern is becoming the default, not the
exception.** (1) Both CAMS's `pragmatic-reviewer` and Flexion's
conflict-resolution hierarchy hardcode a highest-precedence reviewer
whose preference wins by default. Directly opposite this roster's own
`devsecops-engineer` stance, already decided before `tdd-coach` existed:
"a persona that always outranks the others isn't reviewing, it's
vetoing." Kept the existing stance; no automatic winner, ever. (2)
Flexion's quantitative Likelihood×Impact×Effort→Score rubric and personal
skills' 5-level BLOCKER/HIGH/MEDIUM/LOW/INFO scale are both real,
working severity systems — and both rejected, for the same reason
`software-architect`'s numeric health score and a `security-reviewer`
source's self-quieting fast mode were already rejected: this roster
declines quantitative apparatus bolted onto what's actually a qualitative
judgment call, every time it comes up. `test-quality-review` and
`code-reviewer` both use the existing Critical/High/Medium/Low scale —
confirmed again, independently, when `code-reviewer`'s own synthesis hit
the identical rubric a second time and rejected it the same way (see
`.synthesis/code-reviewer.md` Contradiction 1).

**Reviewers still never edit code directly, even now that a real code-
writing persona exists to hand back to.** Personal skills' `code-review`
and `tests-audit` both apply their own fixes after user approval — a
materially different boundary than anything built in this roster so far.
Every existing review skill (`security-review`, `accessibility-review`,
`architecture-review`) only reports and recommends. Kept that boundary
for `test-quality-review` and `code-reviewer` rather than adopting the
personal-skill pattern: those skills were built for a context with no
separate implementer to hand back to (an ordinary Claude Code session
fixing whatever it finds); this roster now has one (`tdd-implementation`),
so hand-back stays the convention instead. `code-reviewer`'s own synthesis
hit this exact contradiction again independently — personal-skills'
`code-review` applies its own fixes — and resolved it the same direction
(`.synthesis/code-reviewer.md` Contradiction 2).

**Asking moves up a level, which is what makes an implementer safe to
background.** Flexion's `orchestrator` resolves any decision an impl
agent would otherwise need to ask about *before* dispatching that agent —
the impl agent receives a fully-specified task and never blocks on
`AskUserQuestion` itself. This generalizes cleanly to `tdd-implementation`
precisely because everything it needs (what to build, how it's
structured, what must hold true, what it looks like) should already be
decided by the time it runs — if something's genuinely missing, that's a
gap in an upstream artifact to hand back to that artifact's owner, not a
question for `tdd-implementation` to ask directly. Same shape as
`accessibility-engineer`'s own `background: true` reasoning, now
confirmed by an independent source rather than derived once in isolation.

**A third, independent confirmation of the same principle, for a persona
with no judgment call to escalate at all.** `architecture-cartographer`'s
synthesis found two Flexion sources giving opposite instructions about
asking the user for relative-importance tiers — one emphatic that asking
is mandatory, the other (`dependency-graph-gen.py`) treating tiers as a
GIVEN, parsed from an already-authored table, never asked about. The
difference traced to what each tool has *available*: a standalone skill
with no upstream tier source has to ask; a tool running inside a pipeline
where a human already decided tiers once, elsewhere, just applies that
decision. This is the same shape as `tdd-implementation`'s own
`background: true` reasoning above, confirmed a third separate time by a
third independent source's own explicit design choice — and sharper here
than either prior case, since this persona has no downstream judgment to
make at all, only facts to persist or report as honestly unresolved.
