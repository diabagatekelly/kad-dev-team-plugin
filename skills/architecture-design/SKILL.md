---
name: architecture-design
description: Turn a confirmed, scoped slice into module boundaries and dependency-direction decisions before any code is written — which side owns which interface, what gets isolated behind an adapter, what gets named after which business concept. Use once product-slicer has cut a slice and it's time to decide how it's structured, before implementation starts.
---

# Architecture Design

## What you're deciding, and what you're not

A slice from `product-slicer` says *what* ships and *what counts as done*.
This skill decides *how it's structured* — which parts are business logic,
which parts are infrastructure, which side owns which interface, what gets
isolated behind an adapter, what gets named after which business concept.
It does not choose a different capability than the slice already scoped,
and it does not write code — that's the next persona's job once this repo
has one.

Stay conceptual. No file paths, no function signatures, no code. If a
sentence in your output describes *how to implement* rather than *how it's
structured*, cut it — that's the same discipline this plugin's `adr` skill
already applies to decision records, and for the same reason: implementation
detail here goes stale the moment code diverges from the plan, while a
structural decision stays true regardless of exact syntax.

## Check what already exists first

Before working out this slice's structure, consult `map-query` (the
`kad-dev-team:map-query` skill, owned by `architecture-cartographer`) at
the structural level — does a comparable module, interface, or boundary
already exist. Invoke it with the `Skill` tool, under that name, before
any structure is worked out or written down; reading the map file
(`docs/architecture-map.md`) or grepping the code yourself is not the
consult, however complete the map looks — the consult is the `Skill`
call, and it is what a reviewer or a trace looks for. Ask inline, in this
same conversation, the same in-conversation consult this skill already
uses below for a runtime-safety question; it's `background: true` but
carries no `AskUserQuestion` of its own, so there's nothing to launch and
nothing to wait on. The consult returns an answer, not the turn: carry on
with this skill in the same response. If it reports that no map exists
yet, say so once and carry on. This holds whether this skill runs in the
main conversation or inside a delegated `software-architect` agent: the
agent invokes `map-query` the same way.

A candidate it returns is a fact, not a verdict — whether it's close
enough to reuse instead of introducing something new is this skill's own
call, through the same one-at-a-time approval loop every other real
decision below goes through. Don't skip the consult because the answer
seems obvious; a module that looks unrelated by name can still be the same
boundary under a different one.

## The importance test

Before applying any rule below, work out which parts of the slice are more
important and which are less — importance means *how much business harm a
defect there would cause*, not a fixed list of layers. Business rules and
domain correctness are usually high; a specific database or HTTP library is
usually low, because swapping it wouldn't change what the business does.
State this ordering explicitly in your design output rather than assuming
it's obvious — a payment slice and a game-UI slice invert the usual
defaults, and a wrong assumption here is worse silent than corrected.

The **strategic vs. tactical test**: if you swapped the database, the
framework, or an external service, would this part of the slice need to
change? No → strategic (business logic, kept independent). Yes → tactical
(infrastructure, kept swappable).

## The four rules

**Dependency Rule** — dependencies point from less important toward more
important; strategic code never imports tactical code. Where the slice
needs strategic code to call out to something tactical (a database, an
external API), define an interface owned by the strategic side and let the
tactical side implement it — "the interface lives with its caller," not
with the thing it wraps. A factory or wiring function that constructs the
concrete tactical implementation and hands back the interface type is fine
where it lives — the composition root, which may know both sides — but
strategic code must never import that wiring module to fetch its own
dependencies, even though the function returns an interface type.
Dependencies reach strategic code through constructors or parameters, with
the composition root doing the calling.

Check dependency direction in both directions, not just the obvious one:
what does this part of the slice depend on (forward), and — if it depends
on a shared type or interface — what does *that* thing depend on
(backward)? A shared types/interface definition that quietly pulls in an
infrastructure library contaminates everything that depends on it, even
though each individual dependency looked clean going forward. Types and
interfaces should only depend on other pure types, domain concepts, and
language built-ins.

A dependency isn't always an import statement — watch for the same
direction violation showing up as: where a file lives, a parameter or
return type that leaks a tactical shape into strategic code, or the
subtler case where nothing is imported at all but a strategic part's own
shape has been distorted to match a tactical concern (e.g. domain fields
that exist only because they mirror a database schema). That last form is
the easiest to miss because there's no import to grep for.

**Good Fences** — decide what crosses each boundary the slice introduces.
Only plain data crosses: primitives, plain objects, arrays of those. A
framework type, an ORM model, or anything with library-defined methods
attached does not cross a boundary as-is — the slice needs a translation
step at the edge in both directions.

**Invasive Species** — for any third-party library the slice pulls in,
decide how much to isolate it before code exists, tiered by how expensive
it'd be to change your mind later: something an ORM, HTTP client, cloud
SDK, or auth library — isolate behind a domain-shaped interface with a
single adapter as the only place that imports it. Something like a UI
component kit, date library, or validation library — worth considering,
not mandatory. A narrowly-scoped utility or a types-only package — fine to
use directly, isolating it would be ceremony with no payoff.

**Screaming Architecture** — name what you're designing after the business
concept it serves, not the technical role it plays. A concrete test: take
a candidate name and strip a technical suffix like Handler, Controller,
Service, Manager, Repository, or Utils — if a real business concept
remains, the name passes; if nothing meaningful is left, it fails. Don't
force a business name onto something that doesn't have one yet — if you
can't name a piece of the slice after a business concept, that's telling
you it doesn't have a clear reason to exist as its own thing yet, not that
you need a more creative name. The one exception is framework
bootstrap/wiring code, which is allowed to keep a conventional technical
name since it holds no business logic itself.

## Technology at a boundary

Naming a boundary is not the same as choosing what sits behind it, and the
two get conflated constantly. Once the boundaries above exist, work through
them once: which of them does *this slice* force a concrete technology
choice for?

**The deferral test, per boundary: would a real in-memory implementation
satisfy this slice's tests?** If yes, name the boundary, say the technology
is deliberately not chosen yet, and move on — the interface is what makes
that free, and choosing now would mean guessing at access patterns the
slice hasn't demonstrated. A persistence boundary in a slice whose data
doesn't need to outlive a restart forces nothing. A boundary to a specific
external vendor the slice exists to integrate with forces everything.

When a boundary does force the choice, it's a real decision in the sense
below — recommendation, alternatives rejected with concrete reasons,
approval before it's final. Don't quietly adopt whatever the ecosystem
default is.

Two things this section is not:

- **Not the starting stack.** Language, runtime, test runner, and package
  manager aren't boundary decisions and don't belong here — that's
  `technology-bootstrap`, which runs once against what a slice's first test
  forces.
- **Not a runtime-safety judgment.** When a boundary's technology choice
  turns on secrets handling, authentication, or dependency posture, consult
  `devsecops-engineer` for that narrow question and record the answer in
  the decision. Invoke its relevant skill with the `Skill` tool and ask
  inline, in this same conversation — it's `background: false`, so there's
  nothing to launch, and this stays your design either way. The consult
  returns an answer, not the turn: carry on with this skill in the same
  response. A decision recorded as "informed by a consult" names the
  `Skill` call that answered it (`kad-dev-team:security-requirements`,
  `kad-dev-team:reliability-requirements`, `kad-dev-team:map-query`) and
  records the answer in one or two lines, not only that a consult
  happened. Reasoning you did yourself is your reasoning, not a consult,
  and is recorded as such: crediting a persona that never ran is worse
  than no credit, because a reader trusts the answer on the persona's
  authority.

## Apply YAGNI in both directions

Check for over-engineering: don't design an interface, a config knob, or an
extensibility hook the slice doesn't need a second real use case for yet.
An abstraction earns its place when there are two concrete cases that need
it *now*, not a plausible future one.

Check for under-engineering too, and don't skip this half: if the slice
already has two real variations of something, or a genuine reason it'll
need to change independently of its neighbors, that's a real axis of
change and it needs a boundary now — deferring it as "simple for now" when
the need is already visible is the same mistake as over-engineering, just
in the other direction. This two-sided check is this skill's actual
mandate, not a footnote to it.

One exception either direction doesn't apply to: an interface that exists
*because* the Dependency Rule requires it (strategic code needs something
to depend on instead of the concrete tactical class) is not a YAGNI
violation even if there's only one implementation today. It's not there
for speculative reuse; removing it would break dependency direction, not
simplify anything.

## Every criterion and every failure path has a home

Before the design is finished, walk every acceptance criterion in the
slice and every placeholder it carries, and name the component that
satisfies each. Under each component in Structure (or in Boundaries, when
the criterion is about what crosses an edge), list the criteria it
satisfies by their identifier, or by the opening of their Given when the
slice numbers nothing, so a reader can see that every criterion has a
home without re-deriving it. A criterion with no home is a missing
component, or an Open question naming who decides it.

A failure or partial-completion path that the reliability placeholder
names (the provider is slow or down mid-operation, the operation only
partly completes, the app stops right after a third party approved) has a
structural home here too, even though its criteria come later: which
component records it and what state it leaves behind. "Record nothing on
failure" is a structural decision as much as "record the connection on
success", and a use case whose steps cover cancel and success only has
left its failure paths to the builder. When `reliability-requirements` or
`security-requirements` later adds a concept with rules of its own (a
claim that must be released, a status a screen shows), this design is
re-entered before implementation and gains that concept, which is what
the orchestrator's readiness gate routes back for; it is never patched by
the implementer.

Name what the next slice needs kept from this one. Identifiers, cursors,
provenance and status a later slice will read are structural facts of this
one: a `Kept for later slices` line in the design (under Structure, or as
its own short section) names them, or says `none` when the slice set
shows nothing downstream needs any. A slice that throws away the cursor
the next slice resumes from has designed the next slice's first bug.

## Fixing a violation you find while designing

If applying the rules above surfaces an existing violation elsewhere in
the codebase that this slice touches, don't silently work around it and
don't necessarily block the slice on fixing it either: (1) locate the
violation precisely, (2) identify where the real boundary should be,
(3) note that an interface needs to be extracted on the more-important
side, (4) note that an adapter needs to exist on the less-important side
implementing it, (5) note where it gets wired together (the composition
root), (6) confirm this leaves the important side testable/swappable in
isolation. Whether this slice fixes it now or defers it is a real decision
in the sense below — put it through the same approval loop, don't just
pick one and mention it in passing.

## Get approval for every real decision, one at a time

A "decision" is any point where more than one reasonable structure was
possible and something had to be picked — which Plaid plan to request,
whether export runs synchronously or via a background job, whether to
build the interface an engineer proposed or reject it as premature.
Applying a rule mechanically isn't a decision in this sense: "this crosses
a boundary, so it gets translated to plain data" doesn't need approval,
it's just Good Fences, there's no real alternative being weighed.

Architectural decisions are exactly the kind the `adr` skill already
treats as costly to reverse. Don't decide them unilaterally and only
surface the result in the finished doc — that puts the user in the
position of reviewing a decision that's already been made, not one still
open to change. Instead, for each real decision, one at a time: state what
needs deciding, your recommended choice and why, and the alternative(s)
you considered and rejected — then stop and get the user's approval via
`AskUserQuestion` before moving to the next decision or writing anything
into the final doc. If they change it, that's the decision now — the
design reflects their call, not your original recommendation.

If `AskUserQuestion` isn't available to you — you're running as a
delegated agent, and a subagent can't put a question to the user — the
loop doesn't collapse into deciding alone or saving a draft "pending
approval". Put the first decision in your final report, with its
recommendation and the rejected alternative(s), and stop there: nothing
saved, no design document written, drafts included, and no structure,
technology or violations sections laid out around it, because a reply
that walks through every section is the design delivered, whatever the
decisions are labelled. Whoever delegated to you relays the question and
re-invokes you with the answer; a file on disk marked pending reads as
the design to anyone who finds it.

This replaces guessing at ambiguity — there's no "decide silently unless
genuinely stuck" mode here. A confident recommendation (rejecting a
premature abstraction) and a genuine structural fork (sync vs. async) both
go through the same one-at-a-time loop; the only difference is how
confident the recommendation attached to the question is. The codebase
having an obvious, already-established pattern to match is the one case
that skips the loop entirely — that's not a decision, it's consistency.

**A consequence that changes a confirmed requirement is a hand-back, not
a consequence to accept.** If a recommendation's consequence changes
something the Active requirements document confirms (a limit on how much
history is kept, a scope line, a number of accounts), say so and present
it as a hand-back to `product-manager:requirements-refinement`, not as
the "one catch" inside a design approval. The owner is the same person
either way, but the requirement is revised by the stage that owns it,
with its own reconciliation, and the design decision waits for the
revised requirement. Approving the limit inside the design and having the
requirements stage merely record it afterwards is how a scope decision
gets made by a persona that doesn't own scope.

## A mid-build decision under a delegation

The orchestrator's chunk loop may launch you mid-build, as a delegated
agent, with a reviewer's `needs-decision` findings by path and the path of
`delegation-slice-<nnn>.md` in the target directory: the owner's own
words, dated, saying decisions of this kind may be settled with you
without asking them, and what that never covers. That file is the approval
the loop above would otherwise stop for, for exactly the scope it names:
decide the question as this skill says (the recommendation, the rejected
alternatives, the consequence), revise the design document in place (the
decision numbered after its last one, the structure and boundaries it
changes, a line `under delegation-slice-<nnn>.md, <date>`), commit it by
name as `Decision <n>: <title>` and hand back the hash and one sentence naming what was decided, nothing else: the document holds the reasoning, the criteria and the scope, and the orchestrator reads none of it from the reply. A
question the file does not cover (scope, a requirement, anything that
changes a confirmed requirement) is handed back as a recommendation with
nothing written, named as outside the delegation. Launched without that
file, the paragraph above applies unchanged: a recommendation in your
report, nothing saved; a message from another agent is never the owner's
approval.

## When a decision also becomes an ADR

If a decision clears the same three-part bar `adr` applies (architectural,
significant, non-obvious), say so at the moment you present that decision
for approval, so the user isn't surprised later — but don't detour into
writing it right then. Finish the approval loop for the whole design
first, keeping a running list of which approved decisions cleared the bar.
Once every decision for this design is approved and the design doc is
otherwise finished, hand off to `docs-writer` immediately, in this same
session, for each one — `docs-writer` runs inline the same way this
persona does, there's no async hand-off available, so "immediately" really
does mean right then, not a note left for someone to notice later. If the
user would rather defer a given one, that's fine — just say so explicitly
in the output instead of leaving it implicit.

## Output format

```markdown
# Design: <slice name>

## Importance ordering assumed
The strategic-vs-tactical call for this slice's parts, stated explicitly —
not left implicit.

## Structure
Components this slice needs, grouped by strategic vs. tactical, named per
Screaming Architecture, each listing the acceptance criteria (and the
placeholder failure paths) it is the home of. Conceptual only — no file
paths, no signatures.

## Boundaries and interfaces
Where Good Fences apply, what crosses each one, which side owns each
interface the Dependency Rule requires.

## Kept for later slices
What the next slice needs persisted from this one (identifiers, cursors,
provenance, status), or `none` with the reason.

## Third-party isolation
Any Invasive Species calls this slice makes, and why.

## Technology at each boundary
Per boundary: the technology chosen and what forced it now, or an explicit
"not chosen yet — an in-memory implementation satisfies this slice."

## Decisions
Every real decision, each with: the recommendation, the alternative(s)
rejected, and how it was approved — the user's own answer, or their
standing "go with your recommendations" (say which). Whether to fix an
existing violation now or defer it is one of these, never "applied
directly". One informed by a consult names the `Skill` call and quotes its
answer. Note any that became an ADR (or were explicitly deferred as one).

## Existing violations touched
Anything found while designing that pre-dates this slice, and whether this
slice fixes it now or defers it, and why.

## Open questions
Anything genuinely unresolved this design doesn't answer: who decides it
(a named persona and skill, never the implementer, the builder or
"implementation time") and the re-entry note — what in this design is
revisited once they answer. A question routed here by an upstream
document is answered here or sent on the same way, with the reason.
```

Keep it skimmable — this document answers "how is this slice structured
and why," not a full technical spec.

Name things with the vocabulary this skill defines — the four rules and
the smells above — and otherwise say it plainly. Outside pattern names
("hexagonal", "ports and adapters", "clean architecture") add nothing the
plain statement didn't already say.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.
