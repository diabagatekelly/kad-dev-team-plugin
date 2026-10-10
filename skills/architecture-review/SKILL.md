---
name: architecture-review
description: Review existing or changed code against the Dependency Rule, Good Fences, Invasive Species, and Screaming Architecture — catching both premature and missing abstraction, not just import-direction violations. Invoke first, before reading any code, for any request to review a module, directory, PR or codebase for architecture, structure, boundaries, dependencies, layering or design — including a plain "review X for architecture issues" — when a PR touches module boundaries, or before marking architecture-sensitive work as done. Never review architecture without it.
---

# Architecture Review

## Scope

You're reading and judging code that already exists — this is the
counterpart to `architecture-design`, which decides structure before code
exists. You don't write or edit application code here; you produce a
findings report. On legacy code you didn't just touch, review only what
changed or was added — and keep a separate "Pre-existing, not blocking"
section at the end of the report for the violations you noticed outside
the change. Skim the rest of the module the change lives in before you
finish, so that section reflects what is actually there rather than being
empty by omission. Don't drop them and don't block on them: the reader
needs to know they exist and that this change isn't being held for them. That's
the Boy Scout Rule: leave the area you touched better, don't demand the
whole forest be clean first.

The same holds when the request scopes the review to a module rather
than a change: the findings list is for that module. Something you notice
in a neighbouring module while tracing goes in the "Pre-existing, not
blocking" section, whatever severity it would earn on its own. And two
adapters reaching their stores through different libraries or idioms
(raw SQL in one, an ORM in another) is not a finding when each stays
behind its port — hiding exactly that choice is what the port is for.

## The importance test

Before applying any rule, decide which parts of the code in front of you
are more important and which are less — importance means *how much
business harm a defect there would cause*, not a fixed list of layers.
Business rules and domain correctness are usually high; a specific
database, HTTP library or SDK is usually low, because swapping it wouldn't
change what the business does. State the ordering you're assuming at the
top of the report rather than leaving it implicit — a payment module and a
UI module can invert the usual defaults, and a wrong assumption is worse
silent than corrected.

The **strategic vs. tactical test**: if you swapped the database, the
framework, or an external service, would this code need to change? No →
strategic (business logic, kept independent). Yes → tactical
(infrastructure, kept swappable).

## The four rules, briefly

- **Dependency Rule** — dependencies point from less important toward more
  important; strategic code never imports tactical code, and an interface
  lives with the side that calls it, not the side that implements it.
- **Good Fences** — only plain data crosses a module boundary; framework
  types and ORM models get translated at the edge.
- **Invasive Species** — a high-lock-in library (ORM, HTTP client, cloud
  SDK, auth) is isolated behind a domain-shaped interface with one adapter
  as its sole importer.
- **Screaming Architecture** — modules are named after the business concept
  they serve; a purely technical role name with no business concept left
  after stripping the suffix is a violation.

The per-rule checks further down are what you actually apply; this list is
so the vocabulary is defined even when this skill is loaded on its own.

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

## Before flagging a factory call as a violation, check where the caller sits

A composition root — the place that constructs concrete tactical objects
and hands them back as their interface type (a `main/`, wiring or
bootstrap module) — is allowed to know both sides. Don't flag it for
importing domain and infrastructure together; that's its job.

The exemption covers the composition root itself, not code that reaches
into it. Strategic code that imports the wiring module to fetch its own
dependency is a Dependency Rule violation even when the function it calls
returns the interface type and the caller never names a concrete class:
the module-level dependency now points at everything the wiring imports
(every adapter, the ORM, environment config), the dependency is hidden
from the constructor instead of declared there, and the caller can't be
handed a fake. The test is the import, not the return type. When you find
it, recommend injection through the constructor or parameters, with the
composition root doing the calling.

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
with nothing else identifying what business concept they serve. Walk the
top-level directories and strip the technical suffix from each; if nothing
is left (`services/`, `utils/`, `helpers/`, `common/`), that is a finding
with a severity and a "where this belongs" fix, not a line in a
description of the layout. Names like factory, helper, base, orchestrator,
processor, or worker aren't automatic violations — they're a near-miss,
worth a second look at whether a business name would fit better, but not
always wrong. Framework bootstrap/entry files are exempt if they contain
no business logic themselves — that's the test, not the filename.

**Circular dependencies** — two modules importing each other is Critical
only when the cycle exists at runtime. Check whether either file uses the
other's export as a *value* at module-evaluation time: a static field
initializer, a top-level call, a default argument, a module-level
constant. That throws on load in CommonJS and ESM alike (`X is not a
constructor`, or a temporal-dead-zone error) — name the crash, rate it
Critical, and propose breaking the cycle. A cycle that exists only in
type positions (`import type`, annotations) is erased by the compiler and
is not a finding.

## Design smells beyond the four rules

Some violations don't show up as an import-direction problem at all:

- **Missing abstraction** — a real axis of change with no boundary around
  it yet. The tell: an `if`/`else` chain or `switch` choosing between two
  or more concrete things that do the same job under different method
  names. Two or more implementations already in the code is a visible
  axis, not a speculative one — flag it, don't call it YAGNI.
- **Premature abstraction** — an interface or extension point with no
  second real use case. For every interface, count its concrete
  implementations and ask what it isolates: one implementation and no I/O
  or external system behind it is premature; one implementation over real
  I/O earns its place from the Dependency Rule, not from a second
  implementation.
- **Wrong abstraction level** — a boundary drawn around the wrong thing,
  so callers still reach past it for what they actually need.
- **Leaky abstraction** — callers have to know the implementation detail
  the abstraction was supposed to hide.
- **Inconsistent abstraction level** — siblings in the same module mix
  high-level orchestration with low-level detail, making the module hard
  to read at any one level. Check each method that calls collaborators
  (fetch a report, send a message, write a file): if the same body also
  works at the level of characters, delimiters, encodings, byte offsets
  or wire formats, it is operating at two levels at once. Flag it, and
  propose extracting the low-level part into its own named piece so the
  orchestration reads at one level.
- **Mixing what and how** — a business decision and a technical detail
  interleaved in the same method body, where a reader can't tell which
  parts express intent and which parts are mechanism. This one is
  invisible to import-scanning entirely — it only shows up on a read. Do
  the read: label each line of a business method as policy (a rate, a
  cap, a grace period, a rule) or mechanism (date arithmetic, id
  generation, serialization, retries, formatting). If the two interleave
  in one body, flag it; the fix is named policy values or a policy
  function with the mechanism moved out.

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

Open with the importance ordering you assumed, then the findings:

```markdown
## Importance ordering assumed
Which parts you treated as strategic and which as tactical, in a sentence
or two — stated, not implied.

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
