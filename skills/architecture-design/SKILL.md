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
concrete tactical implementation and hands back the interface type is fine;
it's a composition root, not a rule violation, as long as strategic code
itself never references the concrete class.

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

This replaces guessing at ambiguity — there's no "decide silently unless
genuinely stuck" mode here. A confident recommendation (rejecting a
premature abstraction) and a genuine structural fork (sync vs. async) both
go through the same one-at-a-time loop; the only difference is how
confident the recommendation attached to the question is. The codebase
having an obvious, already-established pattern to match is the one case
that skips the loop entirely — that's not a decision, it's consistency.

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
Screaming Architecture. Conceptual only — no file paths, no signatures.

## Boundaries and interfaces
Where Good Fences apply, what crosses each one, which side owns each
interface the Dependency Rule requires.

## Third-party isolation
Any Invasive Species calls this slice makes, and why.

## Decisions
Each decision presented for approval during this session, what was
proposed, what the user approved or changed, and the final call. Note any
that became an ADR (or were explicitly deferred as one).

## Existing violations touched
Anything found while designing that pre-dates this slice, and whether this
slice fixes it now or defers it, and why.

## Open questions
Anything genuinely unresolved this design doesn't answer, and who resolves
it next.
```

Keep it skimmable — this document answers "how is this slice structured
and why," not a full technical spec.
