---
name: operational-readiness
description: Check whether something can be shipped safely and recovered when it goes wrong — how you'd know it broke, how you'd put it back, and what someone needs to know when they're debugging it later with no context. Covers rollout strategy, rollback as a tested capability, irreversible changes, and the minimum an on-call or future-you needs. Invoke first, before reading any files, for any request about whether a release, deploy, migration or service is ready to ship, safe to roll out or roll back, or operable in production — including a plain "can we ship this?" — when setting up a delivery path, or when a change is hard to undo. Never judge shipping readiness without it.
---

# Operational Readiness

## The three questions

Asked before something ships, about the delivery path rather than about a
diff:

1. **How would we know it broke?**
2. **How do we put it back?**
3. **What does someone need to know at 2am?** — where 2am often means
   *you, in six months, with no memory of this.*

Every check below serves one of the three. If a proposed practice doesn't,
it doesn't belong in this pass.

You read and ask; you don't edit or run anything. "Has someone run the
rollback" is a question for the user, not something to try. When a check
needs a command run, name the command and what its output would settle,
and let the user run it.

**If shipping safely needs a capability nobody scoped, report that and
stop.** Say what the gap is and what it forces, and recommend if you have
a view. Don't lay out the ways the slice could grow for the user to pick
from: choosing among them is a scope decision, and it isn't this skill's.

## Scale to the real situation

This is where operational advice goes wrong most often. A single-user
personal project and a service with users have almost nothing in common
here, and applying the second's practices to the first produces ceremony
nobody performs — which is worse than nothing, because it looks like the
question was handled.

**Your first response is questions, not a review.** Unless the request
already says who uses this, what breaks for them if it's down, and who
would find out, ask those three — plus whether anyone has ever actually
run a rollback — and stop until they're answered. Don't infer them from
the repository: code says what a service does, not who depends on it or
who would notice, and a confident guess here sets the scale of every
finding that follows. Reading files to ask sharper questions is fine;
writing findings first is not. On a personal
project, "I'd notice next time I opened it, and I'd redeploy the previous
version" is a legitimate and complete answer to questions 1 and 2. Write
that down and move on rather than upgrading it into a monitoring stack.

What follows scales up from there; take only what the answers justify.

## 1. How would we know it broke?

How to check: list everything that runs, not just request paths —
scheduled and background jobs, queues, the deploy itself — and for each
say what tells someone it failed, stalled or never ran at all. A job with
no answer is found by users first. Error reporting covers "failed" only;
a run that never started reports nothing, so scheduled work also needs a
completion signal that alerts when it goes missing.

- **Something confirms the deploy actually worked** beyond the deployment
  tool reporting success. The gap between "deployed" and "working" is where
  the worst incidents live, because everything upstream says green.
- **The first signal doesn't depend on a user reporting it** — for
  anything with users other than you.
- **The signals distinguish "broken" from "slow" from "partly broken."**
  A single up/down check misses the most common real failure, which is
  partial.
- **Someone actually receives the signal.** An alert routed nowhere, or to
  a channel nobody reads, is not a signal. Check the delivery path, not
  just the rule.

## 2. How do we put it back?

**Rollback is a tested capability of the delivery path, not a procedure
improvised during an incident.** This is the central principle here: the
first time a rollback is exercised should never be the time it's needed.
A documented rollback that has never been run is a hypothesis.

Check:

- **There's a way back, and someone has run it.** If nobody has, that's the
  finding — regardless of how good the documentation is. Its fix is to
  exercise it, sized to the situation (one rehearsal against staging or in a
  quiet window, timed); avoiding the change that would need it doesn't
  close the gap, because the next change will. Report it as its own
  finding even when another finding also breaks the rollback (an
  irreversible migration, say): fixing that one leaves this one open.
- **How long it takes**, roughly. A rollback measured in hours isn't a
  rollback, it's a second outage.
- **What can't be rolled back.** Schema and data changes, messages already
  sent, external side effects. These are the real constraint, and they're
  what makes a change genuinely one-way. Identify them explicitly — a
  change containing one needs a different plan, not the same plan with more
  care.
- **Whether the change can ship in a way that limits exposure** — behind a
  flag, to a subset first, decoupled from the data change that has to
  precede it. The point isn't a specific technique; it's whether "undo"
  exists as something other than "deploy the old version and hope."
- **Whether the data change is separable from the code change.** A
  deployment that ships both at once, where one can be reversed and the
  other can't, is the standard way a rollback becomes impossible.

## 3. What does someone need to know at 2am?

The bar is low and specific: enough that a person with no context can
orient. Not a runbook library — the few things that aren't recoverable
from reading the code.

- **How to tell what version is running**, and how to get to its logs.
- **What this depends on**, and what happens when each is down. Often the
  single most useful thing to have written down, because it's the first
  question asked and the slowest to answer from source.
- **The one or two known failure modes and what to do about them** — where
  they exist. Don't invent them to fill the section.
- **What's genuinely irreversible**, flagged where someone will see it
  before acting rather than after.

Written where it'll be found — near the thing, in the repo. A document
somewhere else goes stale unnoticed, which is `docs-writer`'s
`staleness-audit` concern and a real cost.

When these aren't written down, the fix is one short operations note next
to the code covering the four items above, written now. Runbooks per path
are a later, separate choice, and a sound runbook for one path doesn't
cover the others.

## Configuration and environment

How to check: find where configuration is read and, for each variable,
say what happens when it's absent — the service exits, a default applies,
or an empty value flows on. An empty-string fallback is the usual silent
one; check what the code receiving it does with an empty value.

- **Environment differences that could surprise someone** — anything true
  in production and not locally, or the reverse. This is where "works on my
  machine" becomes an outage.
- **Nothing required is undocumented.** A deployment that fails because an
  environment variable nobody wrote down is missing is a readiness finding.
- **Startup fails loudly on missing configuration** rather than starting
  degraded and failing later on a code path nobody exercises immediately.

## What this doesn't cover

Formal incident management — severity matrices, on-call rotations,
post-mortem process — presumes a team and a pager. If those exist, they're
an organizational practice, not something this skill should generate.
Say so and move on rather than producing a template nobody will use.

Writing an operational problem up as an issue is `docs-writer`'s job. When
a finding warrants that, quantify the pain concretely — what it costs, how
often, to whom — and hand it off rather than writing the issue here.

## Output format

```markdown
# Operational readiness: <what's shipping>

## Situation
Who uses this, what breaks for them, who finds out — as established, not
assumed. Everything below is scaled to this.

## How we'd know it broke
Current state, and gaps.

## How we'd put it back
The rollback path, whether it's been exercised, roughly how long, and
what can't be reversed.

## What someone needs to know
The short list, and where it lives.

## Findings
Every gap the sections above name, each as its own finding with a fix — an
observation that never reaches this list hasn't been reported. Before
writing it, walk the bold checks in sections 1–3 and Configuration: each
one either has a finding here or is fine for a reason you can state in a
line. Two gaps that share a cause are still two findings when they need
different fixes.
Severity-ranked (Critical / High / Medium / Low by what it costs if left).
Each finding gives its location, category, severity, **When this bites**
(the conditions under which it manifests), what's happening, and a
suggested fix. Verify a Critical or High before reporting it: that there
really is no rollback path, rather than one written down somewhere you
haven't read. When a way back exists but this change breaks it, say that
— name the path and what breaks it — rather than "no rollback path." Don't inflate severity to force a fix; state the trade-off
and let the user decide.

## Decisions
Anything presented for approval — a rollout strategy, accepting a one-way
change. Note any flagged as ADR-worthy.
```

If the honest answer is that this is small, reversible, and only affects
one person, say that and keep the output to a few lines. Recommending
infrastructure this situation doesn't warrant is the main failure mode of
this skill.
