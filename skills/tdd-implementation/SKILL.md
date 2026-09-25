---
name: tdd-implementation
description: Write a designed slice into working code via genuine Red-Green-Refactor, one test at a time from a Test List, or apply a specifically-named fix handed back from any reviewer through that same loop. Use once a slice has an approved design doc and it's time to actually build it, or when a review finding needs a code change.
---

# TDD Implementation

## What you're doing, and what you're not

You turn an already-decided design into code, one small verified step at a
time. Most of the time you're handed a slice with an approved design doc —
`architecture-design`'s boundaries are the structure you build inside, not
something you redecide. If you're invoked directly with no upstream design
artifact at all — a small utility, a narrow bug fix nothing this roster
would route through a full design pass — the instructions you were given
are the design; apply the same discipline without inventing a formal
design step that isn't there. Either way, you don't decide what capability
gets built, how the slice is structured, or what a screen looks like — you
implement.

## Before the first test: write the Test List

List every scenario the current goal actually needs — analysis, not
implementation. Only what's needed now: no scenario for a requirement that
doesn't exist yet, no defensive case nobody asked for, no "while I'm at it"
addition. As you work, you'll discover real cases you didn't see up front
— add them to the list when they're genuinely needed, not speculatively.

Work the list one entry at a time. Converting the whole list into concrete
tests before making any of them pass defeats the reason the list exists —
each test's outcome informs the next one's shape. Mark an entry done only
after its full cycle (through REVIEW, below) is complete.

## Check what already exists first

Before writing a Test List entry's implementation, consult
`architecture-cartographer:map-query` at the implementation level — does a
comparable function, class, or helper already exist. Load its `SKILL.md`
and ask inline, in this same conversation; it's `background: true` but
carries no `AskUserQuestion` of its own, so there's nothing to launch and
nothing to wait on.

A candidate it returns is a fact, not a verdict. Whether reusing it is the
right call for this entry, or a genuine structural fork exists (reuse this
vs. build new, one interface vs. two), is the same kind of question a
missing collaborator's own fork already gets escalated for — decide it
yourself if there's no real alternative to weigh, escalate to
`architecture-design` if there is. Don't skip the consult because the need
seems novel — a differently-named helper doing the same job is exactly
what this catches.

## RED — one failing test

Write one test for the entry you picked. It should be concrete, runnable,
and fail because the behavior doesn't exist yet. Run it — actually invoke
the test runner — and confirm two things: it fails, and it fails for the
right reason (a real assertion failure or missing implementation, not a
typo, a bad import, or a setup error). A test that "fails" for the wrong
reason isn't proof of anything yet.

Test the public behavior, not internal state or a private method — if you
can't describe what you're testing without mentioning how it's
implemented, you're testing the wrong thing.

If this test needs a test double for an external dependency, wire the
double so it actually intercepts how the code under test obtains that
dependency — a constructor/parameter-injected dependency substitutes
cleanly; a dependency reached through a tightly-coupled import needs a
mechanism that actually replaces that reference, not one that quietly
leaves the real dependency running underneath a mock that's never
consulted. Get this wrong and `test-quality-review` will catch it, but
catching it yourself here is cheaper.

## GREEN — the minimum that passes

Write the smallest possible implementation that makes the one active test
pass. Hardcoding is fine if that's genuinely all the test requires. Don't
add validation the test doesn't ask for, error handling for a case nothing
exercises, or an abstraction that has exactly one caller "so it's ready
for later." Run the test and confirm it passes; run the rest of the suite
and confirm nothing else broke.

If you notice something the implementation should eventually handle that
this test doesn't cover, that's a new Test List entry — write it down, do
not fold it into this implementation silently.

## REFACTOR — structure only, tests green throughout

With the test passing, improve the code's structure without changing what
it does: rename for clarity, extract a piece with a name, remove
duplication, simplify a conditional. Make one small change, run the full
test suite, confirm it's still green, then make the next one. A refactor
that changes behavior isn't a refactor — if you find yourself wanting to
add something new here, stop, finish the refactor as-is, and put the new
behavior on the Test List as its own entry.

If a test fails during this step, revert the last small change immediately
and try a smaller one rather than debugging forward through a red state.

Touching existing code that isn't part of what this test needs: a small,
bounded improvement if you're already there (a clearer name, one
duplication removed) is worth doing; a larger restructuring is only worth
it if the existing state genuinely blocks this task, and even then it's
its own step, done and verified green before the feature work continues.

## REVIEW — check what you just wrote

Run `test-quality-review` against the test (and its implementation) you
just finished. This is inline, in the same pass, not a separate stage to
remember later — the whole point is catching a bad pattern while it's the
newest thing on the stack, before three more cycles get built on top of
it. Address anything Critical or High before picking the next Test List
entry; a Medium or Low finding can be noted and deferred if it's not
blocking, but say so explicitly rather than letting it silently disappear.

This inline pass doesn't need its own persisted report — a pass/fail plus
whatever needs fixing now is enough. Save a written findings report only
when `test-quality-review` is invoked standalone (see that skill).

**Name it every time, not just once.** Across many cycles it's tempting to
shorten this to a generic "reviewed" or "inline check" after the first
mention — don't. Each cycle's review line names `test-quality-review`
explicitly, the same way every other invocation of it does. A shorthand
label is indistinguishable, to anyone reading the work back later, from
the step having been skipped and only summarized at the end.

## REPEAT

Pick the next Test List entry and start the cycle again. Continue until
the list is exhausted for the current goal.

**Before declaring a goal complete**, spot-check the one or two
highest-risk assertions you wrote: temporarily break the implementation on
purpose (a wrong comparison, an off-by-one, a flipped condition), confirm
the test actually fails, then restore the correct code. A test suite can
report full coverage while still never proving it would catch a real bug
— this is the cheap, no-tooling way to catch that before calling the work
done. Coverage itself should land at or near 100% line and branch as a
result of testing every real behavior on the list — treat any gap as a
missing Test List entry, not a number to pad after the fact with a
low-value test.

If the project already commits as part of how this work happens, keep the
failing test and its implementation as separate, ordered commits (test,
then implementation, then any refactor) — that's what makes this cycle's
TDD adherence independently checkable from git history later. Don't invent
a commit discipline the project hasn't asked for.

## Applying a fix handed back from review

A named fix — from `test-quality-review`, `architecture-review`, or
anything else — goes through the same loop, not a special-cased patch:
re-run the affected tests first to see current state, make the change,
re-run them to confirm green (and, if the fix was itself a missing test,
that's a RED step like any other). Report back what changed and that
verification passed.

## Reporting

State, in this shape, so progress stays legible without re-deriving it:

- **Starting point** — tests and coverage before this session's work, if
  any existed.
- **Test List** — as created, with each entry's status as you go.
- **Per cycle** — which entry, and a one-line result (e.g., "2 of 5 done,
  suite green, review clean").
- **On completion** — Test List exhausted, full suite green, coverage
  landed where testing every behavior put it, `test-quality-review` run
  with nothing Critical/High outstanding, false-positive spot-check done.
  This is what "done" means before handing back to whoever asked for this
  work.
