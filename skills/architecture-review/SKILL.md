---
name: architecture-review
description: Review existing or changed code against the Dependency Rule, Good Fences, Invasive Species, and Screaming Architecture — catching both premature and missing abstraction, not just import-direction violations. Use when asked to review code for architecture/dependency issues, when a PR touches module boundaries, or before marking architecture-sensitive work as done.
---

# Architecture Review

## Scope

You're reading and judging code that already exists — this is the
counterpart to `architecture-design`, which decides structure before code
exists. You don't write or edit application code here; you produce a
findings report. On legacy code you didn't just touch, review only what
changed or was added — note pre-existing violations separately as a lower
priority rather than blocking on full-codebase compliance. That's the Boy
Scout Rule: leave the area you touched better, don't demand the whole
forest be clean first.

## Start from a precomputed diff, when one exists

If whoever invoked you (the quarantine flow's Grade step, or a direct
request) hands you an `architecture-cartographer:map-update` diff for the
code in front of you, read it before your own pass — it's a cheap,
mechanically-derived starting point (new/removed dependency edges,
wrong-direction candidates, duplication candidates), not a substitute for
your own judgment. Everything in it is a candidate or a fact, never a
verdict: a flagged wrong-direction edge still needs your own two-direction
check below to confirm it's real and to size its severity; a flagged
duplication candidate still needs your own read to tell a real duplicate
from two things that only look alike today. No diff provided is the
normal case for most reviews — derive what you need yourself, the way
this skill already does below.

## The two-direction dependency check

For every place code depends on something else — an import, a shared type,
a parameter — check direction twice. **Forward**: is the thing being
depended on more important, or at least equally important? **Backward**:
if that thing is itself a type or interface, what does *it* depend on?

The backward check catches what the forward check misses: a types or
interfaces file can look completely clean from the caller's side — nothing
wrong with importing it — while itself quietly importing something
tactical (a database client's option type, an HTTP library's request
shape). Every strategic file that imports that types file inherits the
violation without ever importing the tactical thing directly. When you find
this, the violation is located in the types file, not in each of its
callers — fix it once at the source rather than flagging every caller.

## Before flagging a factory call as a violation, check this first

Code that calls something like a factory or a wiring function to get a
concrete implementation is not automatically a Dependency Rule violation.
A composition root — the place that knows how to construct concrete
tactical objects and hand them back as their interface type — sits outside
the strategic/tactical comparison entirely; it's allowed to know both
sides. Before flagging: confirm the call site never references the
concrete class directly (only the interface type), and confirm what's
returned is typed as the interface. If both hold, this is composition-root
wiring, not a violation, even though a factory call can look identical to
a strategic-depends-on-tactical import at a glance.

## What to check per rule

**Dependency Rule** — direction as above, plus watch for dependency
showing up without an import: a file placed in the wrong location for what
it actually depends on, a parameter or return type that leaks a tactical
shape into strategic code, or a strategic module whose own shape has been
quietly distorted to mirror a tactical concern (fields that exist only
because they match a database schema, not because the domain needs them).
That last form has no import to grep for — it shows up as an unexplained
resemblance between a domain concept and an infrastructure detail.

Severity for a Dependency Rule finding tracks how entangled the violation
is, not just its category: an isolated import or a single misplaced call
is low severity; a tactical type threaded through several method bodies or
stored as a field is medium; a whole module's public signature and
internal logic built around a tactical concern is high — removing it there
means rewriting the module, not swapping one line.

**Good Fences** — flag any framework type, ORM model, or object with
library-attached methods crossing a boundary as-is instead of being
translated to plain data first.

**Invasive Species** — flag a high-lock-in-cost library (ORM, HTTP client,
cloud SDK, auth library) imported anywhere outside a single adapter file.
A lower-risk library (UI kit, date library, validation library) used
directly in multiple places is worth a note, not necessarily a blocking
finding.

**Screaming Architecture** — flag directory/module names built from a
technical role (handler, controller, service, repository, utils, manager)
with nothing else identifying what business concept they serve. Names like
factory, helper, base, orchestrator, processor, or worker aren't automatic
violations — they're a near-miss, worth a second look at whether a business
name would fit better, but not always wrong. Framework bootstrap/entry
files are exempt if they contain no business logic themselves — that's
the test, not the filename.

## Design smells beyond the four rules

Some violations don't show up as an import-direction problem at all:

- **Missing abstraction** — a real axis of change with no boundary around
  it yet.
- **Premature abstraction** — an interface or extension point with no
  second real use case.
- **Wrong abstraction level** — a boundary drawn around the wrong thing,
  so callers still reach past it for what they actually need.
- **Leaky abstraction** — callers have to know the implementation detail
  the abstraction was supposed to hide.
- **Inconsistent abstraction level** — siblings in the same module mix
  high-level orchestration with low-level detail, making the module hard
  to read at any one level.
- **Mixing what and how** — a business decision and a technical detail
  interleaved in the same method body, where a reader can't tell which
  parts express intent and which parts are mechanism. This one is
  invisible to import-scanning entirely — it only shows up on a read.

Treat "premature" and "missing" as equally worth flagging — this review is
explicitly two-sided. A codebase that's all missing-abstraction findings
and no premature-abstraction findings (or vice versa) is a sign you're only
checking one direction; go back and look for the other.

Broader smells worth a mention when you see them, even though they're not
architecture-specific to this skill: god objects, circular dependencies,
shotgun surgery, feature envy, primitive obsession, inappropriate
intimacy.

## Severity taxonomy

- **Critical** — business logic tightly coupled to infrastructure in a way
  that blocks changing either; a circular dependency breaking the build.
- **High** — a Dependency Rule violation inside business/use-case code; a
  framework type leaking across a boundary; a high-lock-in library used
  directly in business logic; a missing abstraction blocking a real,
  already-visible axis of change.
- **Medium** — an interface parked on the wrong side; inconsistent pattern
  use across similar modules; a moderate over- or under-engineering call.
- **Low** — naming, a minor abstraction cleanup, style.

## Stance

Review to distinguish "must fix" from "could improve" — not everything
that deviates from the rules is a violation to eliminate. A deviation can
be a legitimate, documented tradeoff; when you see one that looks
deliberate, ask whether it's already reasoned through before flagging it
as a defect. Perfect compliance on code nobody's touching in months isn't
the goal; catching what actually costs someone later is.

## Finding report format

```markdown
## Finding: <short title>

**Location:** where in the code
**Category:** which rule or smell
**Severity:** Critical | High | Medium | Low

**What's happening:** the current state, concretely.

**Why it matters:** what this costs if left — not "it violates rule X,"
but what becomes harder because of it.

**Suggested fix:** the structural change, in the same conceptual terms
`architecture-design` uses — not a code diff.
```

List findings most severe first. If nothing rises above Low, say so
plainly rather than padding the report with findings to look thorough.
