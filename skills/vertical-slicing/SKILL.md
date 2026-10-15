---
name: vertical-slicing
description: Cut the smallest end-to-end shippable slice from a problem — picking what to build first, applying slicing techniques when the thinnest path isn't obvious, catching too-big/too-thin scope, and handling scope-creep pushback. Use once a problem framing doc exists and it's time to decide what to build first, when a proposed slice looks too big, too thin to demo, or scoped by layer instead of by user value, or when a later stage (security, reliability, architecture) hands back a scope change: a capability nobody scoped that a slice turns out to need.
---

# Vertical Slicing

**First, find the Active requirements doc for this unit. If there isn't
one, stop here:** write nothing, cut no slice, and don't sketch one in
your reply. Say that what to build hasn't been decided with the user yet
and hand back to `requirements-refinement`. This holds when the user says
to skip it ("just decide", "we don't need to talk it through"): what gets
built is theirs to confirm, not yours to infer, and a slice cut anyway
with a note that it's your own judgment is still a slice cut on a guess.

## What a vertical slice is

A slice cuts **through** all layers a feature touches (UI, logic, storage,
any external integration) rather than delivering one layer at a time. A
slice is done when a user (even an audience of one) can exercise real,
observable behavior end to end — not when a layer is "ready for the next
layer."

A slice is not a task list. "Build the database schema" is a horizontal
layer, not a slice — it has no observable behavior on its own. "Upload a CSV
and see it categorized" is a slice — thin, but complete top to bottom.

## Picking the first slice from a confirmed requirement

Start from `product-manager`'s requirements doc for the unit being worked
— its "confirmed in scope," not the problem doc's eventual full feature
set and not a capability choice you're inferring yourself. Its "confirmed
in scope" is the whole of what you're slicing: never reach past it into a
scope map's later steps or the requirements doc's own "confirmed out, for
now" list. Without an Active requirements doc, stop (see the top of
this skill). Don't infer the WHAT from the problem doc or scope map
yourself, and don't re-ask the user what the requirements doc already
settled.

Slicing decides what gets built first, not how it's built: technology,
architecture and module structure are `architecture-design`'s, code is
`tdd-implementation`'s.

The first slice should:

- **Resolve, ask, or explicitly defer** each remaining *technical* open
  question — which capability or approach the user wants is already
  decided by the time you're slicing; what's left is slicing shape (an
  input variation, an edge case, an implementation detail the requirements
  doc didn't anticipate). Ask directly when the answer would change the
  slice's shape; defer everything else rather than requiring every
  question answered up front. Deferring is a decision — write it down as a
  non-goal, don't just drop it silently.
- **Defer risky capabilities, never defer the *need* for security/
  accessibility review on what you do ship.** Prefer a slice that doesn't
  yet need the highest-risk integration (bank credentials, an AI vendor,
  infrastructure nobody's stood up) — there's nothing to secure in a
  capability that isn't built yet. But whatever the slice *does* touch gets
  **two separate placeholder acceptance criteria — one for security, one
  for accessibility, always both.** Never combine them into one line, and
  never ship one without the other, even when only one seems obviously
  relevant (a CSV upload control and a transaction list are both real UI
  *and* both touch real data — that's two placeholders, not one). You
  don't have either expertise — don't author either criterion yourself.
  Delegate the security one to
  `devsecops-engineer:security-requirements`, and the accessibility one to
  `accessibility-engineer` once that persona exists; until then, the
  placeholders keep both gaps visible instead of either going missing
  silently. Shipping without both placeholders is a gap, not a deferral.
- **Still be genuinely end-to-end**, even if narrow. A slice that skips the
  "view the result" step to save time isn't a slice — it's half of one.
- **Has a real user as its actor.** If the actor is "the system" or "a
  developer," that's horizontal slicing wearing a user-story costume — find
  the actual person who benefits.

"Smallest" is relative to your team and tooling, not an absolute floor —
don't split a slice into uselessly small pieces just to say it's small if a
slightly larger cohesive capability is still comfortably deliverable and
still end-to-end.

## Name the whole set, specify only the first

For the unit you're slicing, **list every slice you currently think it
needs** — one line each, a verb phrase and nothing more — then write up
only the first one properly.

The set is what makes the first slice checkable. "Is this the thinnest
first step" has no answer in isolation; it only means something against
what the second and third steps would be. A slice cut with nothing after it
in view is the one that quietly becomes the whole unit, because there's
nowhere else for anything to go.

Keep the split sharp:

- **The set** is cheap, provisional, and one line per entry. No thin paths,
  no acceptance criteria, no ordering rationale beyond what's obvious.
- **The first slice** gets the full write-up below — thin path, acceptance
  criteria, both placeholders, deferrals.
- **Everything after it stays a line** until it's actually next. Writing
  acceptance criteria for slice 3 today prices in assumptions that building
  slice 1 is about to invalidate.

**Expect the set to change, and say so where you write it.** Building the
first slice is the single best source of information about whether the rest
of the list is right. A set that survives untouched to the end was probably
not being checked against reality. Revising it is the process working —
it's the same relationship `scope-map` has with its own steps.

Never advance to fully specifying the second slice before the first is
built and learned from. The set exists to give the first slice context, not
to authorize working ahead.

## Slicing techniques

When "find the thinnest end-to-end path" doesn't obviously produce a slice,
try one of these:

- **Happy path first** — build the single simplest successful path before
  any variation of it. Everything else is a later slice.
- **Input variations** — one slice per distinct kind of input, instead of
  handling every kind at once (e.g. CSV import first, bank-API import
  later, rather than building a universal importer up front).
- **Workflow steps** — if the eventual feature is a sequence, ship step one
  usable on its own before chaining in step two.
- **Reduce scope** — same capability, smaller surface (fewer categories,
  fewer account types, fewer report views) rather than a different
  capability entirely.
- **Defer non-functional requirements** — performance targets, exhaustive
  audit logging, and the like can usually wait for a later slice; don't let
  them block shipping the functional core (security and accessibility are
  the exception — see above, those aren't "non-functional" in this sense).

Infrastructure and setup work (a database connection, an auth mechanism)
isn't its own slice — it rides along with the first slice that actually
needs it, sized to just what that slice requires.

## Handling pushback

- **"We need error handling first."** Tier it instead of blocking on it:
  essential errors (bad input, not-found) ship in slice one, common errors
  (duplicate, timeout) in slice two, rare edge cases (concurrent
  modification) later. "No error handling" and "complete error handling"
  aren't the only two options.
- **"Our architecture requires building layers in order."** Ask whether
  that's a real constraint or a habit. Good architecture lets each slice
  build the minimal part of every layer it needs, and layers get richer as
  more slices land — that's what makes vertical slicing possible at all. If
  it's a genuine legacy constraint, slice as thin as the constraint allows
  rather than abandoning slicing.
- **"The first slice takes longer."** True, and fine — it carries foundational
  work. The failure mode isn't a slower first slice, it's over-building that
  foundation for slices that don't exist yet. Build just enough for slice
  one; let slice two justify any expansion.

## Feature-shape YAGNI

Two failure shapes to catch, in both directions:

- **Too big**: a "slice" that quietly bundles the eventual full feature
  (every account type, every category rule, every edge case) because it
  seemed easier to design once. Cut it down to the smallest version that's
  still end-to-end and still demoable.
- **Too thin to demo**: a "slice" that's technically end-to-end but shows
  nothing a person would recognize as progress (e.g., a hidden internal
  data transform with no visible output). If you can't show it to someone
  and have them understand what changed, it's not a slice yet, it's a task.

Speculative generality is a smell at slice-scoping time too: don't design a
slice to anticipate an account type, category, or integration nobody has
asked for yet. Add it when a second real instance shows up.

## When a later stage forces a scope change

A downstream persona — security, reliability, architecture — will sometimes
find that a slice needs a capability nobody scoped. **That finding is
theirs; the resolution is yours.** They report what they found and what it
forces. Deciding what happens to the slice is this skill's job, and it
doesn't get made by whoever happened to notice.

Work the options in this order, and say which you picked and why:

1. **Cut a new slice ahead of this one** delivering the missing capability
   on its own. Usually right, and usually available — it keeps both slices
   thin and puts the new capability where it can be demonstrated
   independently.
2. **Narrow the current slice so the constraint stops applying.** Legitimate
   when the requirement comes from context this slice doesn't need yet —
   running locally rather than exposed, for instance. Genuinely thinner, not
   a dodge.
3. **Grow the current slice.** Last resort, and only when the missing piece
   can neither stand alone nor be avoided.

**Growth is ranked last because it has no natural stopping point.** Every
addition arrives with a good reason attached, and a slice that has grown
once is easier to grow again. If you land on option 3, say plainly that the
slice is now larger than what was cut and what that bought.

**Whatever you pick, repair what it invalidated.** A capability added
mid-flight has no confirmed WHAT behind it, whether it arrives as a new
slice or by growing this one. What it should be (say, what a guardian's
consent to a junior member's payment looks like) is the user's to decide
in its own `requirements-refinement` pass, not an assumption that the finding
constitutes one, and not something you write into the requirements doc
yourself. A changed step boundary supersedes the scope map rather than
editing it. Leaving a stage skipped because the slice arrived from an
unusual direction is exactly the gap this ordering exists to close.

**Your output is the scope decision, not the repairs.** Record the choice,
the options rejected and why, and for each document it invalidates
(requirements, design, security or reliability criteria) which skill
redoes it. Don't edit those documents: an Active one is superseded by the
skill that owns it, never edited in place, and criteria for the new
capability are that persona's to write. The hand-back section stays as it
is until its owner revises the document.

## Matching and detection criteria need a named key

Any criterion built on comparing two things — matching a transaction to
sample data, detecting a duplicate, matching a merchant to a category —
needs the concrete key it matches on, not just the asserted outcome.
"Transactions don't appear twice" without saying what makes two
transactions "the same" is exactly as untestable as "categorizes
correctly" without saying what "correctly" means — the same vagueness
pitfall from the `acceptance-criteria` skill, just one level removed: the
ambiguity is in the *comparison*, not the *outcome* word.

If the problem doc doesn't specify the key: either name a reasonable one
and flag it as a decision — the same treatment as "CSV vs. bank-API," a
named choice with a stated reason, not a coin flip — or defer the whole
criterion to "Still open"/"Explicitly deferred" like any other undecided
behavior. Never assert the outcome and skip the key; that's deciding by
omission. And apply this consistently within one write-up — deferring the
matching logic for categorization while silently asserting duplicate
detection works (or vice versa) is the same decision made two different
ways in the same document.

## Slice write-up format

Before writing the acceptance criteria, invoke `acceptance-criteria` with
the `Skill` tool for its quality checks. The consult returns guidance, not
the turn: carry on writing the slice in the same response.

If the slice was cut from a scope-map step rather than straight from the
problem doc, name that step in the title, e.g. "Slice 1 (scope-map-001
step 2): ..." — it's how later stages tell which steps are already sliced.

```markdown
# Slice N: <name — a verb phrase describing user-observable behavior>

## Slice set for this unit
Every slice this unit currently looks like it needs, one line each, this
one marked. Provisional — expected to change once this slice is built.
Include this section in the unit's first slice write-up; later slices in
the same unit reference it rather than restating it.

## Thin path
The single end-to-end path this slice delivers, one or two sentences.

## Acceptance criteria
Given/When/Then scenarios, as many as needed, no filler ones added to look
thorough. See the `acceptance-criteria` skill for quality checks.

## Explicitly deferred
Open questions from the problem doc (or earlier slices) that this slice
does NOT resolve, and why deferring is fine for now.

## Still open
Anything genuinely unresolved that the next slice (or another persona —
name which one) needs to answer before it can be scoped.
```

Keep the whole write-up skimmable — this document answers "what are we
building first and why," not "here is everything about the feature."

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.
