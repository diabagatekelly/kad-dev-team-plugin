# Synthesis: architecture-cartographer

Internal only — never referenced from `agents/architecture-cartographer/AGENT.md`
or its backing skills. Delete once the full roster is built.

Roster row 10, the last planned persona. Infrastructure for the rest of the
roster, not a reviewer in its own right: it maintains a mechanically-derived
map of the codebase's real structure and answers "does something like this
already exist," but never decides, judges, or grades. The shape (mandate,
scope boundaries, two skills, wiring) was already worked out in a prior
planning session and is recorded in `PERSONAS.md`'s "`architecture-cartographer`'s
shape, planned ahead of its own turn" section — this synthesis resolves the
things that section left genuinely open: the exact extraction method, the
map's file format, and the `AskUserQuestion`/`background` call.

## Sources consulted

1. **Flexion plugin** — `flexion-oea-coder/skills/program/tools/duplication-candidates.py`
   and `dependency-graph-gen.py` in full (real, working Python tools, not
   just prose guidance — the corpus's only source that actually implements
   mechanical codebase-structure extraction end to end), their governing
   reference docs `references/dependency-rule.md` (in full, including its
   "Facet-to-tier mapping" section) and the `DUPLICATION` section of
   `references/condition-types.md`, plus `skills/fleet-worker/agents/condition-checker.md`
   (the orchestrating agent prompt that consumes both tools' output) and,
   as a contrasting data point, `flexion-oea-engineer-scaffold/skills/oea-dependency-evaluator/SKILL.md`
   (a standalone dependency-rule checker with no upstream tier input of its
   own). `flexion-adapt/skills/discover/references/discovery-catalog.md`
   was also read in full on an early grep hit but turned out to be a
   different domain entirely (an organizational digital-twin discovery
   catalog, not code) — noted and discarded, not stretched to sound
   relevant.
2. **Personal skills** — searched global `~/.claude/skills` (`cams-commit`,
   `coach`, `code-review`, `deep-pr-review`, `diff-walk`, `handoff`,
   `pgp-log`, `tests-audit`) and every genuine project-level `.claude/skills`
   directory under `~/Documents/*` (`LLMCourse/arabic-teaching-multi-agent/.claude/skills`,
   `Fitalyst/fitalyst-poc/.agents/skills`) for dependency-graph, import-graph,
   duplication, codebase-map, catalog/inventory, and reuse material:
   **nothing on point**. The only hits were `code-review`'s and
   `deep-pr-review`'s local, single-pass DRY checks ("no duplicate code
   blocks >3 lines repeated," "database connection logic reused, not
   duplicated") — file-level duplication noticed during one review, not a
   persisted, regenerable, cross-codebase map. That's exactly the territory
   this roster already reserves for `code-reviewer` (local file-level
   DRY/naming), not this persona. Same finding shape as `ux-designer`'s,
   `accessibility-engineer`'s, and `software-architect`'s syntheses for
   their own topics — reported plainly, not fabricated.
3. **CAMS** — `skills/ui-component-catalog/SKILL.md` in full (the single
   strongest, most directly-on-point precedent found anywhere in the
   corpus for this persona's "does something like this already exist"
   half), `skills/cams-architecture/SKILL.md` in full (grep-based, ad hoc
   OeSA checks — read for the extraction technique underneath the
   procedure, not the procedure itself), and `skills/cams-refactoring/SKILL.md`
   PROCEDURE 7 ("Refactor Duplicated Code" — duplication found via ad hoc
   grep at refactor time). `cams-dataflow` and `cams-query-builder` were
   also opened (both named in the original research brief) and confirmed
   not relevant — dataflow scaffolding and a MongoDB query-builder library,
   neither about codebase structure — noted, not used.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Mechanical extraction is regex/import-statement-based over real source text, language-agnostic by file suffix, needing no installed static-analysis tool or language server | `duplication-candidates.py` / `dependency-graph-gen.py` (JS/TS import regex + Python `from`/`import` regex, extensible by suffix); `cams-architecture` (`grep -r "import.*Mongo" backend/src/**/use-cases/` as its own working method for the same class of question) | convergence across both usable sources — settled, not just "current lean" |
| Candidate *discovery* and *verdict* are structurally different steps, done by different authorities | `duplication-candidates.py` ("this tool discovers candidates; it never judges axes" — same-axis judgment is a separate 3-agent vote); `condition-types.md` DUPLICATION section ("the similarity is coincidental and the modules will diverge — leave them separate" is a judgment call, not the discovery step); CAMS `ui-component-catalog`'s "Recurring Patterns" section lists ad hoc duplication candidates without commanding extraction, deferring to a filed issue | convergence — confirms the mandate `PERSONAS.md` already committed to, not a new finding |
| Importance/tier is a GIVEN, supplied by an upstream authority, never derived from the import graph itself | `dependency-rule.md` ("importance is a GIVEN... deriving tiers from imports is circular: when modules violate the Dependency Rule, import-derived layering rearranges around the wrong edge, so the graph could never display an incorrect dependency") | gap → added, and resolves a real fork — see Contradiction 1 |
| A generated structure map is informational: nothing treats it as a pass/fail verdict, and the generator itself never adjudicates | `dependency-graph-gen.py` ("this graph is informational: no gate item consumes it as a pass/fail verdict and the generator exits 0 regardless of highlighted wrong-direction candidates... the generator projects, never adjudicates") | gap → added — the clearest single-source statement of this persona's whole mandate found anywhere in the corpus |
| A module/finding nothing has classified yet renders as an explicit "unclassified"/"untiered" state, never guessed | `dependency-graph-gen.py` ("modules with no mapped facet render in an explicit `unclassified` band, never guessed") | gap → added |
| A persisted catalog of what already exists, consulted *before* building something new and updated *in the same task* whenever something new is added, is a working, real-world pattern for exactly this "does X already exist" question | `ui-component-catalog` (component name + import path + 2-4 sentence description per entry; "if an existing component visually matches what is needed, use it — do not create a new one"; keep-current rule) | gap → added — the shape `map-query`/`map-update` both take is modeled directly on this |
| A candidate list can include not-yet-consolidated recurring patterns, named as candidates rather than commanded extractions | `ui-component-catalog`'s "Recurring Patterns" section (a pattern appearing in 2+ places gets named and filed as a beads issue "to consider extraction," not auto-extracted) | gap → added |
| No numeric or qualitative severity scale applies to a structural fact — a scale describes a downstream judgment about a finding's consequence, and mechanical discovery never reaches that judgment | derived from this roster's own repeated rejection of quantitative apparatus (`software-architect`, `devsecops-engineer`, `test-quality-review`) plus the corpus's own confirmation that neither `condition-checker.md`'s report format nor `dependency-graph-gen.py`'s output carries any score | baseline, sharpened — see Contradiction 4 |

## Contradictions — flagged and resolved

**1. Should the tool ask the user about relative importance, or take tiers as already given?**
Two Flexion sources take opposite stances on the identical underlying
question. `oea-dependency-evaluator/SKILL.md` is emphatic and repeated:
"YOU ABSOLUTELY MUST ASK THE USER ABOUT EVERY UNCACHED DEPENDENCY PAIR...
YOU CANNOT... assume importance based on module names... infer importance
from patterns... skip questions because they seem 'obvious'." Its own
`dependency-graph-gen.py`, by contrast, treats importance as a GIVEN
sourced from a separately-authored table, parsed at runtime, "never
derived from the import graph" and never asked about — a module with no
mapped tier simply renders `unclassified`.

These aren't actually in tension once the difference in what each tool has
*available* is accounted for: `oea-dependency-evaluator` is a standalone
skill with no upstream source of importance at all, so asking is the only
honest option. `dependency-graph-gen.py` runs inside a pipeline where a
human has already adjudicated the tier table once, in a separate document,
and the tool's job is to apply that decision, not rediscover it every run.

**Resolved toward the second stance, and it's not close** — this roster's
own pipeline already matches `dependency-graph-gen.py`'s precondition, not
`oea-dependency-evaluator`'s: `architecture-design` already assigns each
slice's strategic-vs-tactical importance ordering today, explicitly, in
its own "Importance ordering assumed" section, per slice. This persona's
job is to *persist* that already-made decision across slices, never to
re-derive or re-litigate it, and never to ask about it independently —
asking would re-open a decision that already has an owner and an approval
loop (`architecture-design`'s own `AskUserQuestion` sequence), which isn't
this persona's call to reopen. A module nothing has tiered yet renders
`untiered`, explicitly, the same as `dependency-graph-gen.py`'s
`unclassified` band — visible, never guessed, never silently defaulted.

This also directly settles the one thing `PERSONAS.md`'s planning section
left as "current read: no, but worth confirming" — whether `map-update`
ever needs `AskUserQuestion`. It doesn't, for a structural reason now
backed by a real precedent rather than just a guess: by the time this
skill ever runs, the one input it might otherwise have needed to ask about
(importance) is either already decided upstream or is honestly reported as
not yet decided. Nothing this persona does ever depends on information
only a human can supply in the moment. `architecture-cartographer` is
`background: true` on this basis, the same reasoning `accessibility-engineer`
and `tdd-coach` already established for this roster ("asking moves up a
level, which is what makes an implementer safe to background") — now
confirmed by an independent source's own explicit design choice
(`dependency-graph-gen.py`'s tier-parsing) rather than derived in isolation
a third time.

**2. Extraction method — genuinely open in `PERSONAS.md`'s planning note, now settled.**
Not a contradiction between sources so much as a confirmation: both usable
sources independently land on the same technique — parse real import
statements from real source text via language-specific regex/pattern
matching, filtered by file suffix, with no dependency on an installed
static-analysis tool, language server, or build step. `dependency-graph-gen.py`
and `duplication-candidates.py` do this for JS/TS and Python via dedicated
import-regex patterns (plus a documented supplemental pass for Python's
`from <package> import <member>` idiom, which a naive regex would miss).
`cams-architecture` does the same thing more crudely but for the same
purpose, via ad hoc `grep -r "import..."` invocations. **Resolved: the
portable, grep/import-statement-based approach `PERSONAS.md`'s plan
already leaned toward is the settled method**, not a remaining open
question — extended to whatever languages a given project uses by adding
an import-pattern per language, with a file whose language isn't
recognized yet rendering as present-in-the-module-list but edgeless
(visible, not silently dropped), the same "never guess, render explicitly
unknown" discipline the tier handling above uses.

**3. Map file format — also genuinely open in the planning note, now settled.**
`PERSONAS.md`'s "current lean" (structured data plus a short derived
narrative) is confirmed by both `dependency-graph-gen.py`'s output (a
generated Mermaid graph *plus* a prose paragraph explaining what it shows
and doesn't verdict on) and `ui-component-catalog`'s (a structured
per-entry record — name, path, description — *plus* prose sections like
"Recurring Patterns" that don't fit the structured shape). **Resolved:
the map is a structured per-module table (path, tier, internal edges,
external packages, public exports) as the backbone, plus a short prose
section per `map-update` run summarizing what changed and listing that
run's mechanical candidate flags in plain, verdict-free language.** No
particular diagram renderer is mandated — a project can add one, but
`map-update`'s own required output is the table plus narrative, kept
plain-markdown and portable rather than tied to a renderer every
downstream reader would need to support.

**4. Severity — sharper than this roster's usual "no quantitative apparatus" stance, not just a repeat of it.**
Neither usable source puts any score, numeric or qualitative, on a
structural fact itself. `condition-checker.md`'s report format is
`Module / Condition triggered / Details / Role axis / Recommended action`
— no severity field at all. `dependency-graph-gen.py`'s wrong-direction
highlighting is a visual flag (thick red edge), not a rated finding.
CAMS's CRITICAL/HIGH/MEDIUM/LOW scale (`cams-architecture`,
`cams-refactoring`) does exist, but it's applied by a human or reviewer
*deciding what to do about* a finding — a downstream judgment, not
something the mechanical scan itself computes. **Resolved: this persona
carries no severity apparatus of any kind, not even this roster's own
usual qualitative Critical/High/Medium/Low scale** — that scale describes
a reviewer's judgment about a finding's real consequence, and this persona
never reaches that judgment at all, for anything. A duplication candidate
or a wrong-direction edge is reported as a plain fact with its supporting
detail; whoever consumes it (`architecture-review`, `architecture-design`,
eventually `code-reviewer`) decides what it means and, if it matters,
what severity attaches.

## Scope decisions, not sourced from a contradiction

**Where the map file itself lives — the artifact-location convention applies, but at a different cadence.**
`PERSONAS.md`'s own convention is that artifact location is always a
parameter, asked for per-problem, never hardcoded and never searched for
instead of asked. The map doesn't fit that shape cleanly: it isn't owned
by any one problem or slice the way a design doc or a requirements doc
is — it's read and written across *every* slice's lifetime, closer in
kind to `technology-bootstrap`'s stack decision (also project-level, also
"runs once per project and then stays additive") than to a per-problem
deliverable. Both usable real-world precedents confirm this shape:
`ui-component-catalog`'s catalog lives at a fixed, project-tooling-owned
path relative to the component library, not inside whatever artifacts
folder a given feature's work happens to be using; `dependency-graph-gen.py`
writes to a fixed, tooling-declared convention (`docs/scenario-<id>/...`),
not a location resolved per invocation.

**Resolved: the map's location is still a parameter, never hardcoded — but
it's resolved once per project, the same cadence `technology-bootstrap`
already uses, not once per problem/slice the way every other artifact in
this roster is.** One thing this draft got wrong on a first pass, caught
during review rather than shipped: "ask once" cannot mean this persona's
own skills ask, since both are `background: true` with no
`AskUserQuestion` tool, precisely because nothing they do should ever
depend on a live human answer (see Contradiction 1) — and `map-update`
explicitly must be able to run unattended inside a worktree-isolated
candidate build, where no one is present to answer anything anyway.
**The asking, when it's genuinely needed, is done by whichever persona is
about to consult this one** — `architecture-design` or
`tdd-implementation`, both of which retain `AskUserQuestion` — the same
responsibility `orchestrator` already takes for a problem's artifacts
directory in its own step 1. That consulting persona resolves the map's
location (given, obviously implied, or asked for directly if this is the
first time this codebase has been mapped) *before* loading either of this
persona's skills inline, and passes it in as an input, the same as it
passes in everything else this persona needs. If `map-query` or
`map-update` is ever invoked with no location supplied and none
obviously implied, it says so plainly and stops — the same fallback
`accessibility-engineer` already established for a `background: true`,
no-`AskUserQuestion` persona — rather than asking itself or guessing.
Every other artifact this persona might ever produce (there currently are
none planned beyond the map itself) would still follow the normal
per-problem parameter rule; this exception is specific to the map because
it's project-local build infrastructure, not a per-problem deliverable,
and treating it as one would mean re-resolving the same answer on every
single slice for no reason, since it can't meaningfully change slice to
slice.

**Two skills, matching the two distinct triggers `PERSONAS.md` already
named — confirmed rather than re-derived.** `map-query` is read-only by
design: it answers from whatever the persisted map currently says, and
says so plainly (including "no map exists yet" or an honest note that the
map may be stale as of its last `map-update` run) rather than silently
regenerating live, which would blur the read-only/regenerate boundary the
two skills are built to keep separate. `map-update` is the only skill that
ever writes the map, extracting fresh from real source and diffing against
whatever was there before.

**Advisor-consult wiring, not a new spawn pattern.** `map-query` is loaded
inline by whichever persona is asking (`architecture-design` at the
structural level, `tdd-implementation` at the implementation level),
exactly the way `architecture-design` already consults `devsecops-engineer`
today — no async `Agent` call, control handed straight back. `map-update`'s
mechanical, non-judgment nature means it doesn't need the parallel-graded,
blind-to-each-other isolation the quarantine flow's actual reviewers get
(`test-quality-review`, `architecture-review`, `security-review`,
`reliability-review`, `accessibility-review`) — there's no competing
judgment to keep independent, just one deterministic regenerate-and-diff
step. It runs inline too: once per candidate inside Grade (feeding that
candidate's reviewers a precomputed diff instead of making each of them
re-derive the graph independently), and once for real after Finalize.
`architecture-cartographer` being `background: true` at the `AGENT.md`
level describes what's structurally possible (nothing in it ever blocks on
a human), not a commitment that every invocation actually spawns it async
— the exact same distinction `PERSONAS.md`'s own "Orchestrator" section
already draws for `accessibility-engineer` ("is `background: true` but
this skill still adopts its instructions inline like every other row,
since v1's routing is sequential by construction, not because every
persona it invokes requires it").

**Stays narrow — the boundary the planning section already drew, held
under contact with real source material.** Every source that gets close
to this persona's territory eventually reaches a place where the
underlying question stops being mechanical. `condition-types.md`'s own
DUPLICATION section states this almost verbatim: two modules that look
alike "may be duplicates produced by independent splits... if they serve
the same axis of change... merge them. [If not,] the similarity is
coincidental and the modules will diverge — leave them separate." Deciding
*which* of those two a given pair actually is stays outside this persona,
exactly as `PERSONAS.md` already specified — `architecture-cartographer`
surfaces the candidate pair and whatever mechanical facts support it
(shared exports, shared import targets, shared naming); it never renders
the coincidental-vs-real verdict itself.
