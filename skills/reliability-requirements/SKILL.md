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

**Your file is the artifact, and the only document you edit.** It is
`reliability-slice-<nnn>.md` in the target directory. You may replace the
slice's reliability placeholder line with a one-line pointer to it and
nothing more: not the story (`docs-writer`'s, re-synced by
`user-story-writeup` on the next re-inspection), not another criterion,
not any other section or document, whatever the invoking instructions
say. A slice criterion your fork changes (a narrowing to "posted"
transactions, a dropped case) is a finding for `product-slicer` under
your Open questions, routed by the orchestrator, never an edit.

## When you're consulted inline

Sometimes another persona, usually `software-architect` mid-design,
invokes this skill to answer one question about a choice it owns: whether
a dependency needs a fallback, whether an operation must be safe to
repeat. Answer that question with its reasoning, flag ADR-worthiness if it
applies, then go straight back to the skill that asked: your answer is one
of its inputs, not the end of the turn. Don't address the user or hand
anything back to them; the asking skill carries on in the same response.
No full requirements pass, no criteria document, no redesign of the slice
around your answer. If the question exposes something larger, such as a
target nobody has agreed or a failure mode with no owner, say so in one
sentence and leave it to the caller.

Write the answer as visible text under a `## Consult answer` heading: the
question, the answer, its reasoning, and ADR-worthy yes or no, so the
trace and the calling skill's document can carry it. A thinking-only
answer is not an answer: the design then records "informed by a consult"
with nothing behind it.

## A mid-build decision under a delegation

The orchestrator's chunk loop may launch you mid-build, as a delegated
agent, with a reviewer's `needs-decision` findings by path and the path of
`delegation-slice-<nnn>.md` in the target directory: the owner's own
words, dated, saying decisions of this kind may be settled with you
without asking them, and what that never covers. That file is the approval
this skill's decision loop would otherwise stop for, for exactly the scope
it names: decide the question as this skill says (the failure mode, the
number, the recommendation, the rejected alternative), revise the
reliability document in place (the failure-mode row, the new or amended
criterion with its number, the decision under Decisions with a line `under
delegation-slice-<nnn>.md, <date>`), commit it by name as `Decision <n>:
<title>` and hand back the hash and one sentence naming what was decided, nothing else: the document holds the reasoning, the criteria and the scope, and the orchestrator reads none of it from the reply. A question the file does
not cover (scope, a requirement, anything that changes a confirmed
requirement) is handed back as a recommendation with nothing written,
named as outside the delegation. Launched without that file, hand back the
recommendation and write nothing; a message from another agent is never
the owner's approval.

## Establish the target by asking — don't assume one

You cannot read a reliability target off the code, and the right answer
varies enormously with what the thing is. **Your first response is
questions, not criteria.** Unless the request already answers them, ask
in one pass and stop until they're answered; don't decide the stakes
yourself ("low volume, no target needed") and write criteria on top of
that. Read the code first so the questions are sharp, and don't ask what
it already answers — which provider is called, whether errors are
reported, how a payment is recorded. Ask:

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

**Read the slice's security criteria first** (the file the slice's
security placeholder points to). Where a failure mode's intended behaviour
touches what security says must or must not be stored (a partial
connection, an exchange that fails after a third party approved, a token
that never arrived), state which wins and why, citing the security
criterion by its identifier or its file, or hand the conflict to
`software-architect` as an open question with both quotes. Two documents
by the same persona that disagree on the same window is a mid-build
decision waiting to happen, and the builder will settle it alone.

Go through what the slice depends on and name what each can do to you.
Concrete, slice-specific, not a taxonomy:

- **A dependency is slow** — not down, just slow. The most commonly missed
  one, because it doesn't look like failure until it exhausts something.
- **A dependency is down** or returns an error.
- **A dependency lies** — returns success with wrong, partial, or stale
  data. Including a reply the slice can't use at all: a missing or
  malformed field, a page without a total, an amount that isn't a number.
  Say whether that is treated as a failed call or as a bug, and when the
  design names an adapter to an external service, give the unusable reply
  its own failure-mode row.
- **The operation is interrupted partway** — what state is left behind?
- **The same thing happens twice** — a retry, a double submit, a redelivered
  message. Whether that's harmless is a design question this slice has to
  answer. A retry is only for a transient fault (a timeout, a 5xx,
  a dropped connection). A deterministic refusal — a declined card, a
  validation error — gives the same answer every time, so retrying it
  only repeats the side effects; a criterion must not call for it, and an
  existing retry of one is a failure mode to name.

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

**Every retry, wait, poll, give-up and stale window gets its number.** A
criterion that says the app "retries a few times", "waits a while" or
"gives up eventually" is the vague language `acceptance-criteria`
rejects, and every number left out here is one the builder decides alone
mid-chunk. Write how many times, how long, how often (as an outcome:
"after five attempts over about a minute the user is told the bank didn't
answer"), or write `unbounded, owner approved` with the owner's answer
behind it. An owner who says "don't care" to a latency target has excused
the target, not the retry bound.

## Decisions

Real forks here — accepting a single point of failure, choosing to degrade
rather than fail on a given path, committing to a target, deciding that
duplicate operations must be prevented rather than tolerated — get
presented with a recommendation and rejected alternatives, and approved
before they're written in. Flag any that clear the ADR bar and hand off
to `docs-writer` once the criteria are done.

**Approval comes before the document, not inside it.** Once the
questions about the target are answered, your next response is the
forks: for each, what needs deciding, your recommendation and why, the
alternatives you rejected, and whether it clears the ADR bar. Present
them one at a time through `AskUserQuestion` when it is available;
without it, present all of them in one plain-text response and end your
turn there. Don't write the criteria yet, not even the ones no fork
touches: a document with half its criteria marked "waits on decision 2"
gets reviewed as a draft instead of decided, and the forks usually
decide the shape the rest follow. The document is written once, after
the approvals, complete.

## Output format

This document comes after the questions are answered and the forks are
approved, never before. Until the questions about the target are
answered, your whole response is those questions; until the forks are
approved, your whole response is the forks. "Open questions" below is
for what stays unresolved after that, not a place to park either while
writing the criteria anyway.

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
Each fork: the recommendation, the alternatives rejected, and its status —
**approved: <choice>** as the user gave it, or **pending** for one the
user didn't answer. Never mark one approved yourself. When the user
rejects your recommendation, record their choice as the approved one,
your recommendation as rejected, and the risk the choice carries, once;
then write the criteria for their choice and make it as workable as it
can be made. A criterion that depends on a pending decision waits for
it; write the rest. A proposal already on the table (an engineer's
"simplest thing", the user's own plan) is a decision whenever you would
change it: present it with your recommendation instead of writing your
alternative in. Note any flagged as ADR-worthy.

Once decisions are approved, the finished document is complete: every
criterion the approvals don't touch stays in, not just the ones that
changed. Accepting a risk with a manual remedy ("I'll refund it by hand",
"I'll fix it if it happens") adds a criterion of its own: the cases are
visible to whoever applies the remedy, or the remedy never happens.

## Out of scope for this slice
Real concerns belonging elsewhere, and where.

## Open questions
Unresolved, and who resolves them: a named persona and skill, never the
implementer, the builder or "implementation time". A question an
upstream document routed to this stage (a design doc asking whether a
pull fits a per-request limit) is answered here, or sent on with the
reason it isn't this stage's and to whom; a question that bounces from
stage to stage until the builder meets it has no owner, which is the one
state this section exists to prevent. A slice criterion your fork
narrows goes here as a finding for `product-slicer`.
```

When the stop rule applies instead (the slice can't meet its target
without a capability nobody scoped), the whole response is this, and
nothing from the document:

```markdown
## Handed back to product-slicer — blocking

**The gap:** what the target requires, and what the slice as scoped
cannot provide.
**What it forces:** the scope decision this is, with the missing
capability named by what it has to achieve, not by the ways it could be
built, and that it is `product-slicer`'s to make, not this skill's.
**Recommendation:** one way forward and why, if you have a view;
otherwise leave the line out.
**Held until scope is settled:** the forks you would have presented, by
name only.
```

One recommendation, not a list: naming two ways the gap could be filled
is the menu the rule forbids, even with "the choice isn't mine" after it.

If the slice has few real failure modes, say so and write few criteria.
