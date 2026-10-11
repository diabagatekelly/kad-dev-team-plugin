---
name: scope-map
description: Chunk a large problem into a light, named map of steps once a problem framing doc exists but before slicing begins. Use when a problem is big enough that "what's the smallest first slice" doesn't yet answer "what's the whole shape of this" — gives loose visibility into the full problem without designing or slicing any of it.
---

# Scope Map

**Trigger:** a problem framing doc exists, and the problem is large enough
that jumping straight to "what's the smallest slice" would lose the shape of
the whole thing. A scope map sits between the problem doc and slicing —
it names the rough steps a solution will eventually move through, without
designing or slicing any of them yet.

Skip this for small problems. If the problem framing doc already reads as
one thing a single slice could plausibly start on, there's no map to draw —
go straight to slicing.

**Not a backlog and not a design.** A step's own line is a name and a
one-line description of what it covers — no acceptance criteria, no thin
path, no *meta-commentary* about build order or timing tacked onto the
line (e.g. "(depends on step 2)," "(3 days)"). Those get added later, one
step at a time, by `vertical-slicing`/`acceptance-criteria` when that step
is actually being worked, and by `software-architect` when a step needs
real design. If you catch yourself slicing or designing a step here, stop
— that content belongs to those tools once the step comes up, not to this
map now. (Explaining the *overall* order across steps is different —
that's what the template's own "Sequencing notes" section is for; it just
doesn't belong inline on an individual step's line.)

A step's one-liner naturally describing what data or output it works from
— "categorize *retrieved* transactions," "surface a transfer amount
*based on the budget-vs-actual picture*" — is not a dependency
annotation, even though it implies an earlier step produced that input.
That's ordinary content describing what the step covers, the same as any
other part of its one-liner. The thing to avoid is explicit sequencing
meta-notes bolted onto a step, not a step's description naturally
referencing the data it operates on.

A one-liner may restate a constraint the problem doc already stated (e.g.
"a read-only connection," echoing a Constraint already on record) — that's
not a new design decision, just carrying forward context the reader already
has. Naming an actual technology, vendor, or implementation approach not
already in the problem doc is a design decision and doesn't belong here.

**A cross-cutting constraint isn't a step — and setting it aside is not the
same as deferring it.** Some constraints from the problem doc (protecting
sensitive data, staying free, not assuming one identity) apply to every
step rather than being one. Saying so here is right; they'd make a
misleading step. But say where they get applied, and the answer is **each
step's own `requirements-refinement` pass**, which reconciles them against
that step's confirmed scope before anything is sliced.

**Identify a cross-cutting constraint by its underlying concern, not by
which step its sentence happens to name.** A constraint can read as though
it only touches the step where it first bites — "AI-assisted categorization
must run at no ongoing cost" names categorization, but the concern
underneath it (this project must not accrue a recurring bill) isn't
actually about categorization; that's just the one place the problem doc
happened to spend words on it. Absorbing it into that one step's one-liner
and calling it handled is the same silent narrowing this section already
warns against for security — ask what the constraint is protecting against,
not which step's activity its sentence names.

Never route them to "made concrete per slice as each is designed." That
sounds responsible and defers a whole-problem constraint past the point
where scope is decided — so it resurfaces during design or review, when the
only remaining fixes are re-slicing or growing a slice. A constraint set
aside here is *every* step's requirements problem, not a later persona's.

**Template:**

```markdown
# Scope Map: <short name> (scope-map-001)

## Status
Active | Superseded by scope-map-NNN

## Steps
1. <step name> — <one line: what this step covers>
2. <step name> — <one line>
3. ...

## Sequencing notes
Why this order, only if it isn't self-evident from the steps themselves.
Omit this section entirely if the order is obvious.

## Out of scope
What this problem does not include at all, only if a step boundary needs
that stated for clarity — a reader who'd otherwise wrongly assume a missing
step is actually a gap. Most of the time this section isn't needed: what's
excluded is usually already implied by the steps that exist, the same
reason the problem doc itself doesn't carry a dedicated Non-goals section.
```

**Revise by superseding, never by editing.** Number scope maps sequentially,
same as ADRs. Once a map is Active, don't edit it — write a new numbered
version and mark the old one `Superseded by scope-map-NNN`. The diff between
versions is itself useful information: it's the record of how understanding
of the problem's shape changed as real work revealed things the first map
guessed wrong.

**Revise when slicing proves a step boundary wrong** — a step turns out to
be two separate problems, two steps turn out to be one, or work on one step
surfaces a step nobody had named. This is expected, not a failure: the first
scope map is a hypothesis about the problem's shape, not a commitment to it.
Don't revise pre-emptively on a hunch — wait until a slice actually forces
the question.

**Write for skimming.** Lead with the point; prefer bullets and headers to
prose; a paragraph is one or two sentences at most. If a sentence wouldn't
change what the reader does next, cut it.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.
