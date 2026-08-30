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
path, no per-step dependency or estimate annotation. Those get added later,
one step at a time, by `vertical-slicing`/`acceptance-criteria` when that
step is actually being worked, and by `software-architect` when a step
needs real design. If you catch yourself slicing or designing a step here,
stop — that content belongs to those tools once the step comes up, not to
this map now. (Explaining the *overall* order across steps is different —
that's what the template's own "Sequencing notes" section is for; it just
doesn't belong inline on an individual step's line.)

A one-liner may restate a constraint the problem doc already stated (e.g.
"a read-only connection," echoing a Constraint already on record) — that's
not a new design decision, just carrying forward context the reader already
has. Naming an actual technology, vendor, or implementation approach not
already in the problem doc is a design decision and doesn't belong here.

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
What this problem does not include at all, if a step boundary needs that
repeated from the problem doc's Non-goals for clarity. Don't duplicate the
whole Non-goals section — only what a reader would otherwise wrongly assume
is a missing step.
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
