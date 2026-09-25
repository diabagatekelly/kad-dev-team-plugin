---
name: orchestrator
description: Route a problem to whichever kad-dev-team persona/skill applies next, by inspecting what already exists (problem doc, scope map, requirements, slices) rather than the user having to name the right persona each time. Use when the user wants to move a problem forward and hasn't said which persona/skill to use, or says "what's next" / "keep going" on a problem already in progress.
---

# Orchestrator

**This is a skill the main agent loads, not a persona to spawn.** Every
persona in this roster that plans work (`docs-writer`, `product-manager`,
`product-slicer`, `software-architect`, `devsecops-engineer`) blocks on
`AskUserQuestion` and must run inline — never as an async `Agent` spawn. Orchestrating them means *you* adopt each one's
instructions in turn, in this same conversation, the same way you would if
the user had asked for that persona directly. `accessibility-engineer` is
`background: true` and *could* be launched async outside this skill, but
this skill still adopts its instructions inline like every other row,
since routing here is sequential by design, not because every persona it
invokes requires it. **The one exception is the `tdd-coach:tdd-implementation`
row** — see "Quarantine, grade, combine" below — which genuinely launches
real async `Agent` calls, the only place in this skill that does.

**Skip this skill** when the user already named what they want directly
("write an ADR for X," "audit the docs for staleness") — routing only
earns its keep when the user hasn't said which persona/skill applies and
you'd otherwise have to guess or ask them to pick.

**Stay inside your lane while inspecting.** Every read you do — in step 2,
and when adopting a persona in step 4 — is confined to (a) the `AGENT.md`
and `SKILL.md` files the routing actually needs, and (b) the resolved
target directory. Never read anywhere else in the project "for context" —
not this plugin's own `evals/`, not other skills' fixtures, not unrelated
directories. If this is being dogfooded inside the plugin's own repo,
those directories look like real project content but aren't; outside that
repo, they won't even exist. Either way, wandering into them isn't this
skill's job.

## Procedure

**1. Identify the target.** You're invoked with the artifacts directory as
a parameter, or not:
- **Given one** — that's the target. Skip straight to step 2. Don't
  second-guess it, don't search for a different one.
- **Not given one** — ask once, before doing anything else: "Where do this
  problem's artifacts already exist, or where should they be created if
  we're starting from scratch?" Whatever the user answers becomes the
  target for every persona this skill invokes on this problem, this
  session and any future one — record it nowhere except by virtue of the
  first artifact actually landing there. Never guess a location yourself
  and never search the project for one instead of asking — if it wasn't
  handed to you, ask.

**2. Inspect what already exists in the target directory** — cheap,
mechanical checks only, never a semantic read of full artifact prose:
- A problem framing doc (a file whose top heading is `# Problem: ...`)?
- Any `scope-map-*.md` files? If more than one, the current one is the
  highest-numbered file whose `## Status` says `Active` (not `Superseded
  by ...`).
- Any `requirements-*.md` files? Same Active/Superseded rule. Which unit
  (scope-map step, or "the problem" if there's no scope map) does the
  current one belong to?
- Any slice files? For each, does its title name a source scope-map step
  (e.g. "scope-map-001 step 2")? A slice with no such reference was cut
  directly from the problem doc. Has it been written up as a user story
  yet (a matching user-story artifact, if this project tracks those
  locally — otherwise take the user's word for whether filing happened)?
  Has it been designed yet (a matching design-doc artifact from
  `architecture-design`, if this project tracks those locally — otherwise
  take the user's word)? Does it still carry unfilled placeholder
  acceptance criteria naming `devsecops-engineer` (or, in artifacts written
  before this persona existed, `security-engineer` / `reliability-engineer`)?
  Is it UI-touching — does its thin path describe a screen or view a
  person looks at and acts on? Take this as stated by the slice's own
  text; a genuinely ambiguous case is worth asking about, not guessing.
  If UI-touching, does it have a screen-design artifact yet (a matching
  artifact from `screen-design`, if this project tracks those locally —
  otherwise take the user's word)? Check both the target directory itself
  and a `visual-ux/` subfolder inside it — `ux-designer` saves its written
  artifacts in either place depending on the run, and both are valid; don't
  conclude one doesn't exist just because the root came up empty. If it has
  one, does it still carry an unfilled accessibility-criteria placeholder
  (naming `accessibility-engineer`, or, in artifacts written before this
  persona existed, an explicit not-authored-here placeholder)?
- **Project-level, not per-unit:** is there a technology-bootstrap artifact
  in the target directory? If not, take the user's word for whether this
  project already has a working stack — a repo someone has been building in
  for months has obviously settled this without an artifact, and asking it
  to produce one retroactively is busywork. Only a repo with no stack yet
  routes to this row.
- **Project-level, not per-unit:** is there a design-system artifact in the
  target directory, or inside a `visual-ux/` subfolder of it — check both,
  same as the screen-design check above? Only relevant once some unit is
  actually UI-touching — a problem where nothing has needed a screen yet
  never routes to this row, the same way a problem with no stack decision
  forced yet never routes to the technology-bootstrap row below.
- Has the current unit's slice actually been implemented — real,
  working code, not just design/criteria artifacts? There's no fixed
  convention for detecting this mechanically (it's application source, not
  a markdown artifact this plugin names) — take the user's word for it,
  the same way you already do for an established project's stack.

**3. Route by what's missing**, in this order. Each row assumes everything
above it in the table is already satisfied for the current unit of work
(a scope-map step, or the whole problem if no scope map applies).

**Backward routing takes precedence over the whole table.** Before matching
any row, check whether a later artifact has invalidated an earlier one.
Signals, all cheap to spot: a section headed "handed back," "blocking," or
similar naming another persona; an artifact stating it contradicts or
supersedes something upstream; an artifact whose own text says a stage was
skipped for it.

When you find one, **route to the persona that owns the invalidated
artifact — not the one that found the problem.** A security pass that
discovers a slice needs a capability nobody scoped has found a
`product-slicer` problem; a slice created without a requirements pass is a
`product-manager` problem. The finder reports; the owner decides. Letting
the finder resolve it in place is how a scope decision gets made by a
persona that doesn't own scope, and how a stage gets skipped without anyone
choosing to skip it.

Two rules for the backward step: upstream artifacts are revised by
superseding, never by editing in place (`scope-map`, `requirements-refinement`,
and `adr` all number sequentially for this reason), and once it completes,
return to step 2 and re-inspect from scratch — a superseded scope map can
move the forward position by more than one row.

That "return to step 2" instruction governs your own next invocation once
the backward step actually completes — it is not something to narrate now.
When reporting a backward route (step 5), state only the single routed
destination and why; don't add what re-inspection will find or where the
forward position might land once it resolves. Describing that round trip is
the same chaining step 5 already forbids, just spelled backward instead of
forward.

| Detected state | Route to |
|---|---|
| No problem framing doc | `docs-writer:problem-framing-doc` |
| Problem doc exists; no scope map, no requirements doc, no slice anywhere yet | `docs-writer`, to decide — per `scope-map`'s own trigger criteria, by reading the problem doc — whether this needs a scope map or is small enough to treat as one unit. This is the persona's judgment call from the problem doc's own content, not an orchestrator-level question; it may still ask the user if genuinely torn, just not by default. |
| A unit is identified (the lowest-numbered Active scope-map step with no requirements doc yet, or — if no scope map exists — the problem itself) and has no requirements-refinement doc | `product-manager:requirements-refinement` for that unit |
| The current unit has a requirements-refinement doc but no slice yet | `product-slicer` (`vertical-slicing` + `acceptance-criteria`), using the requirements doc as the primary input for WHAT to slice — not re-deciding it |
| A slice exists for the current unit but hasn't been written up as a user story yet | `docs-writer:user-story-writeup` |
| The current unit's slice has been written up as a user story but has no design doc yet | `software-architect:architecture-design` for that slice |
| The slice has a design doc but its security criteria are still an unfilled placeholder | `devsecops-engineer:security-requirements` for that slice |
| The slice's security criteria are filled but its reliability behavior has never been made concrete | `devsecops-engineer:reliability-requirements` for that slice |
| The slice is UI-touching, its runtime-safety criteria are filled, and the project has no design-system artifact yet | `ux-designer:design-system` |
| The slice is UI-touching, its runtime-safety criteria are filled, a design-system exists, but this slice has no screen-design artifact yet | `ux-designer:screen-design` for that slice |
| The slice is UI-touching, has a screen-design artifact, but its accessibility criteria are still an unfilled placeholder | `accessibility-engineer:accessibility-review` for that slice |
| The slice is designed with its runtime-safety criteria filled (and, if UI-touching, its screen designed and its accessibility criteria filled), and the project has no stack yet | `software-architect:technology-bootstrap` for that slice |
| The slice has a design doc, its runtime-safety criteria are filled (and, if UI-touching, its screen designed and its accessibility criteria filled), the project has a stack, but the slice hasn't been implemented yet | `tdd-coach:tdd-implementation` for that slice |
| The slice has been implemented — `tdd-coach:tdd-implementation` has produced working, tested code for it | **Stop — see step 5.** Don't advance to the next scope-map step. |

**Why the requirements rows come *after* design, not before.** These are
the only non-functional criteria in the spine that depend on structural
decisions: what data a slice actually handles is determined by how it's
built. A design that puts a third-party vendor between the system and a
credential means the credential never enters at all — which is a completely
different set of security criteria than the same slice built to hold that
credential itself. Running these before the design decision would produce
criteria for a system nobody is building.

**Why screen design comes after security and reliability, not before.**
Those two rows are exactly the ones most likely to surface a backward
route — a slice discovers it needs a capability nobody scoped, and the fix
can change the slice's shape entirely. Designing a screen for a slice whose
scope might still move is wasted work at best and a screen built for the
wrong slice at worst. Placing screen design after both runtime-safety rows
means it only ever runs against a slice that's already survived its most
likely sources of change.

**Why accessibility review comes right after screen design, not before.**
There's nothing to check before a screen has actually been rendered —
`accessibility-review` verifies an artifact `screen-design` produced, the
same dependency `screen-design` itself has on `design-system`. Running it
before the stack is chosen also keeps its findings technology-agnostic: a
missing label or a failing contrast pair is a property of the rendered
markup and tokens the mockup already committed to, not of whatever
framework eventually renders it for real — the same reason runtime-safety
criteria get written before a stack exists rather than after.

**Why the bootstrap row comes last, not first.** An empty repo makes
"choose the stack" feel like step one, but a structural design needs no
technology to exist — it names boundaries and what crosses them — and
runtime-safety criteria are deliberately technology-agnostic ("bank
credentials never enter the system" holds regardless of what's storing
anything). The one thing that genuinely can't proceed without a stack is
writing the first failing test, which is `tdd-coach:tdd-implementation`'s
job, the next stage after this row. Putting it here means the choices get
made against a slice that's fully
specified, and only the ones that slice actually forces get made at all.
This is also why screen design, when it applies, runs before bootstrap
rather than after: `technology-bootstrap`'s own "sometimes forced"
UI-framework decision depends on whether the first failing test actually
drives a screen, which is only knowable once that screen has been
designed.

Never invent a stage this table doesn't cover. ADRs, `staleness-audit`,
`tdd-coach:test-quality-review`, `code-reviewer`, and all four of
`devsecops-engineer`'s review/posture skills (`security-review`,
`reliability-review`, `supply-chain-review`, `operational-readiness`) are
event-triggered, not part of this forward spine — they run against code, a
test file, or a repo that already exists, which most of this spine hasn't
reached. Hand off to them only if the user asks. `test-quality-review` and
`code-reviewer` also run inline, as part of the quarantine flow's Grade
step, inside `tdd-implementation`'s own row — that's not a spine stage
either, it's part of how that one row does its job.

**`architecture-cartographer:map-query` is another inline advisor consult,
not a spine stage — it doesn't get its own row here either.**
`software-architect:architecture-design` consults it before writing a
design doc, at the structural level ("does a comparable module or
interface already exist"), the same inline, hand-control-straight-back
pattern that row already uses for its `devsecops-engineer` consult.
`tdd-coach:tdd-implementation` consults it again before writing each Test
List entry's code, at the implementation level ("does a comparable
function or helper already exist") — below `architecture-design`'s own
conceptual altitude, squarely inside what that row actually writes. Both
consults are instructed in the asking skill's own `SKILL.md`, not
something this file dispatches; nothing about routing changes because of
them. `architecture-cartographer:map-update` has its own wiring inside the
quarantine flow below — see "Quarantine, grade, combine."

**4. Execute exactly one routed step.** For every row except
`tdd-coach:tdd-implementation`, execute inline: read the target persona's
`AGENT.md` and the specific `SKILL.md` the trigger matched — nothing
else. Adopt those instructions directly — this is live use, not a dry
run: if that persona would ask the user something, actually ask via
`AskUserQuestion`. Tell it explicitly where to save its output — the
location resolved in step 1. It should not ask where to save or invent a
different location; you already resolved that. Produce the real artifact
and save it there, using that persona's own filename/heading convention.

**The `tdd-coach:tdd-implementation` row doesn't execute inline — it runs
the quarantine/grade/combine/finalize procedure below, every time, by
default.** There is no separate "is this slice worth it" judgment call
here: no signal anywhere in this roster's pipeline reliably predicts
implementation risk, and inventing one would be worse than having none.
The cost this multiplies is bounded by `product-slicer` already keeping
each unit at the smallest shippable slice — this is real cost applied to
something small, not a large unit of work. If the user explicitly wants a
specific slice built without it, that's their call to make by saying so
directly; this skill doesn't offer a way to opt out on its own judgment.

**Append one entry to `orchestrator-log.md`, in the target directory,
every time this step runs — before moving to step 5.** This is the only
retrospective record that every stage actually ran rather than getting
silently skipped; a graded final artifact says nothing about the path
that produced it. Create the file if it doesn't exist yet. One entry per
invocation, appended, never edited or reordered — a prior entry being
wrong gets a new entry noting the correction, the same append-only
discipline `scope-map`/`requirements-refinement`/`adr` already use for
their own artifacts, applied here to a process record instead of a
decision record. Each entry:

```markdown
## <sequence number>. <date> — <the detected-state row that matched>

**Routed to:** `<persona:skill, or "quarantine flow" for that row>`
**Artifact:** <path to what was produced, or "see sub-entries below">
```

For a backward route (the step 3 rule that supersedes the table), log it
the same way, naming which artifact got superseded and why, not just the
forward destination.

### Quarantine, grade, combine — the `tdd-coach:tdd-implementation` row's own procedure

Five steps, replacing the normal single inline execution for this one
row only. Every other row in the table is unaffected.

**A. Quarantine.** Launch two `tdd-coach:tdd-implementation` instances
against the same slice — real async `Agent` calls, each with
`isolation: "worktree"` so each works in its own isolated copy of the
repo. Give both the identical task: the slice's design doc, its
runtime-safety criteria, its screen-design/accessibility criteria if
UI-touching, and where to save output — the same inputs a single
non-quarantined execution would get, nothing added about quarantine,
grading, or a second candidate existing. Blindness here is structural,
not something to enforce by instruction: two fresh spawns with no shared
context already can't see each other. Wait for both to finish before
continuing. Each worktree-isolated run returns its own path and branch —
note both; you'll need them in the next two steps.

**B. Grade.** For each candidate, before launching its reviewers, run
`architecture-cartographer:map-update` inline (not an async `Agent` call —
it's mechanical, not a graded judgment, so it needs none of the isolation
the reviewers need from each other) against that candidate's own
worktree, diffed against the real project's last persisted map. This run
is throwaway: it never overwrites the persisted map, and it exists only to
hand that candidate's reviewers a precomputed diff — new/removed edges,
duplication candidates, wrong-direction candidates — instead of each of
them re-deriving the graph independently. Then, for each candidate
independently, run every applicable reviewer in parallel against that
candidate's own worktree, as real async `Agent` calls:
`tdd-coach:test-quality-review`, `architecture-review`, `code-reviewer`,
`devsecops-engineer:security-review`, and
`devsecops-engineer:reliability-review` always apply;
`accessibility-engineer:accessibility-review` applies only if the slice
is UI-touching. No persona is weighted above another
within a candidate's grading pass; read every finding on its own merits.
That's up to 12 parallel review agents (6 reviewers × 2 candidates, fewer
if the slice isn't UI-touching) — `map-update`'s two inline runs aren't
part of that count. Wait for all of them before continuing.

**C. Combine — inline, yours alone, not spawned.** Read both candidates'
actual code from their worktree paths (not just their own self-reports)
and both full sets of graded findings from Grade. This read is explicitly
in-scope even though it reaches outside the target directory — the "stay
inside your lane" constraint from earlier is about inspection in step 2,
not about executing the routed step itself. Decide, and state your
reasoning: which candidate to build from, or which pieces of each, and
exactly what needs fixing or reconsidering. Not joint authorship of the
two, not an average of them — one accountable call. Write the decision as
a concrete brief describing the target implementation — informed by both
candidates' approaches and every finding raised against either one — not
a shorthand like "use candidate A's version."

**D. Finalize — a fresh instance, regenerated independently, not layered
on either candidate.** Launch a third `tdd-coach:tdd-implementation`
instance — not either original candidate — with no worktree isolation
this time, targeting the project's real working tree. Its task is your
combine brief from step C, plus the same original slice inputs from step
A. It builds a genuinely new implementation informed by both candidates
and every finding against either, not a patch on top of whichever
candidate combine preferred. This is the real, final artifact — the one
that answers "has this slice been implemented" for step 2's future
inspection.

Once the fresh instance finishes, run `architecture-cartographer:map-update`
for real — inline, not an async `Agent` call, for the same reason as
Grade's throwaway runs — against the actual working tree this time. This
run's output replaces the project's persisted map: it becomes what the
next slice's `architecture-design` and `tdd-implementation` read via
`map-query`, and what the next slice's own `map-update` runs diff against.

**E. Re-grade — targeted, not a full re-open.** Once the fresh instance
finishes, re-run only the reviewers whose findings the combine brief
asked it to address, checking only those specific findings against the
finalized implementation. Pass/fail per finding, not a fresh grading pass
across every category from step B.

**Reporting this procedure.** Step 5's report names what happened at each
of the five steps above, not just the final outcome. The two candidate
worktrees and branches from Quarantine still exist once this completes —
name both so the user can inspect either directly if they want to, but
don't merge or delete them yourself; discarding a candidate's branch is
exactly the kind of action this roster's own safety rules reserve for the
user to decide, not something to clean up silently on your own judgment.

**This row's `orchestrator-log.md` entry needs sub-entries for all five
steps, not the one-line form every other row gets** — this is the one
place a single "Routed to" line would hide exactly the thing the log
exists to catch:

```markdown
## <n>. <date> — slice ready for implementation

**Routed to:** quarantine flow
- **A. Quarantine:** candidate 1 — `<worktree path>` / `<branch>`; candidate 2 — `<worktree path>` / `<branch>`
- **B. Grade:** map diffs per candidate — `<duplication/wrong-direction candidate counts>`; reviewers run per candidate — `<list>`; findings summary — `<Critical/High counts per candidate>`
- **C. Combine:** chosen basis — `<candidate 1 | candidate 2 | pieces of both>`; brief — `<one line>`
- **D. Finalize:** `<path to final artifact>`; persistent map updated — `<path>`
- **E. Re-grade:** findings addressed — `<count>` pass, `<count>` fail
```

**5. Report, then ask whether to continue — never chain silently.** State
what was detected, why it routed where it did, and what got produced.
Then:
- **If step 3 found a next row** (there's more to do for the current
  unit): name what that next step would be and ask whether to continue to
  it now, in this same conversation. If yes, loop back to step 2 for the
  now-current state — don't re-run step 1. If no, stop and wait.
- **If the current unit just reached the terminal row** (its slice is
  designed, its runtime-safety criteria are filled, its screen is designed
  and its accessibility criteria filled if it's UI-touching, the project
  has a stack to build on, and `tdd-coach:tdd-implementation` has produced
  working, tested code for it, already graded by `code-reviewer` and every
  other applicable reviewer inside the quarantine flow's Grade step): don't
  propose anything further. Moving on to the next scope-map step's
  requirements or slicing before this one is implemented and reviewed would
  repeat the mistake this rule exists to prevent: deciding too much before
  anything's been built. If the user explicitly wants to start a different
  unit anyway, that's their call to make by asking directly — not something
  this skill offers.
