---
name: reliability-requirements
description: Decide what a slice must do when things go wrong, and what must be observable to know whether it's working — before code exists. Establishes the slice's failure modes, which degrade gracefully versus fail loudly, what target it's held to, and emits testable Given/When/Then criteria. Use when a slice depends on something that can fail, or when "must be reliable" has never been made concrete.
---

# Reliability Requirements

## What you're producing

Acceptance criteria for the slice's behavior when things go wrong, and for
what has to be visible afterward. This is the counterpart to
`security-requirements` and sits alongside it — same moment, same slice,
same output form, different question.

The question here: **when this slice's dependencies misbehave, what should
the user see, and what should you be able to find out?**

**If the slice can't meet its target without a capability nobody scoped,
report that and stop.** Say what the gap is and what it forces, and
recommend if you have a view. Don't lay out the ways the slice could grow
for the user to pick from: choosing among them is a scope decision, and it
isn't this skill's.

## When you're consulted inline

Sometimes another persona, usually `software-architect` mid-design, loads
this skill to answer one question about a choice it owns: whether a
dependency needs a fallback, whether an operation must be safe to repeat.
Answer that question with its reasoning, flag ADR-worthiness if it
applies, and stop. No full requirements pass, no criteria document, no
redesign of the slice around your answer. If the question exposes
something larger, such as a target nobody has agreed or a failure mode
with no owner, say so in one sentence and leave it to the caller.

## Establish the target by asking — don't assume one

You cannot read a reliability target off the code, and the right answer
varies enormously with what the thing is. Ask:

- **What happens if this is unavailable for an hour?** The answer
  separates "personal tool, mildly annoying" from "someone loses money."
  Almost every other decision follows from it.
- **Is there a target worth stating?** For anything user-facing, a rough
  one is better than none: how often is it acceptable for this to fail,
  and how slow is too slow. A number someone agreed to converts "is this
  reliable enough?" from an argument into a check. The gap between that
  number and perfection is a budget you're allowed to spend.
- **Who notices when it breaks — and how?** On a personal project the
  honest answer is often "me, next time I use it," and that's a legitimate
  answer that should shape the criteria rather than being quietly upgraded
  into a monitoring requirement nobody asked for.

Scale everything to the real answer. Writing enterprise availability
criteria for a single-user tool produces criteria nobody implements, which
is worse than none.

## Enumerate this slice's failure modes

Go through what the slice depends on and name what each can do to you.
Concrete, slice-specific, not a taxonomy:

- **A dependency is slow** — not down, just slow. The most commonly missed
  one, because it doesn't look like failure until it exhausts something.
- **A dependency is down** or returns an error.
- **A dependency lies** — returns success with wrong, partial, or stale
  data.
- **The operation is interrupted partway** — what state is left behind?
- **The same thing happens twice** — a retry, a double submit, a redelivered
  message. Whether that's harmless is a design question this slice has to
  answer.

For each one that's plausible, decide the intended behavior. That decision
is what becomes a criterion.

## Degrade gracefully or fail loudly — decide, per failure mode

The two are opposites and both are correct in different places. Getting
this backwards is the most expensive mistake available here.

**Degrade gracefully** when partial service beats none and the user can
still get value: showing cached data with a staleness marker, hiding one
broken panel, queueing work for later.

**Fail loudly** when proceeding on bad data does damage, when silence
would hide a problem that compounds, or when the user would act
differently if they knew. A financial figure computed from partially-
retrieved data should fail loudly; showing it with a quiet asterisk is
worse than showing nothing.

The failure to avoid: degrading so gracefully that nobody — user or
developer — ever learns something is broken.

## Distinguish expected from unexpected failures

**Expected** failures are part of normal operation: invalid input, a
business rule refusing, a third party legitimately saying no. These aren't
exceptional, they have defined behavior, and the user gets a message that
says what happened and what to do next.

**Unexpected** failures are bugs and genuine system faults. These need to
be visible to whoever maintains the system, and must not be swallowed into
a generic message that makes them indistinguishable from the expected kind.

Conflating the two produces both halves of the classic bad outcome: alerts
full of routine validation failures, and real bugs hidden behind a friendly
error screen.

## Decide what must be observable — driven by a question, not coverage

Don't specify instrumentation as a coverage level ("all operations
logged"). Specify it as the questions you must be able to answer:

> **Is this slice working, and if not, where is it failing?**

Whatever it takes to answer that, and nothing more yet. This keeps
observability inside the same YAGNI discipline the rest of this plugin
applies, and it makes a gap concrete: a failure mode you couldn't
diagnose, rather than a function without a metric.

For each failure mode you named above, ask: if this happened, how would
anyone know, and how would they tell it apart from the others? Where the
answer is "they couldn't," that's a criterion.

Where the slice crosses process or service boundaries, something has to
tie the pieces together — a shared identifier threaded through, so the
records are one story rather than three unrelated ones. Instrumentation
costs money and performance; deliberate scope is part of doing it well,
not a compromise of it.

## Write criteria in the same form as the rest of the slice

Given/When/Then, matching `acceptance-criteria`, sitting alongside the
functional and security criteria. State observable outcomes, not
mechanisms:

> Given the bank aggregator is unreachable
> When the user opens the transaction list
> Then the previously retrieved transactions are shown, marked as
> potentially out of date, and no error page is displayed

Not:

> The system implements a circuit breaker with a 30-second reset

The second prescribes a mechanism, which is `software-architect`'s and the
implementer's territory, and it isn't checkable as a user-visible outcome.
Name the behavior; let the implementation follow.

## Decisions

Real forks here — accepting a single point of failure, choosing to degrade
rather than fail on a given path, committing to a target, deciding that
duplicate operations must be prevented rather than tolerated — get
presented one at a time with a recommendation and rejected alternatives,
and approved before they're written in. Flag any that clear the ADR bar
and hand off to `docs-writer` once the criteria are done.

## Output format

```markdown
# Reliability requirements: <slice name>

## What's at stake
The consequence of this slice being unavailable or wrong, and any target
agreed with the user. Stated, not assumed.

## Failure modes
What this slice depends on, what each can do, and the intended behavior —
degrade or fail loudly, and why.

## What must be observable
The questions someone must be able to answer, and what that requires.

## Acceptance criteria
Given/When/Then, alongside the slice's other criteria.

## Decisions
Presented, chosen, rejected. Note any flagged as ADR-worthy.

## Out of scope for this slice
Real concerns belonging elsewhere, and where.

## Open questions
Unresolved, and who resolves them.
```

If the slice has few real failure modes, say so and write few criteria.
