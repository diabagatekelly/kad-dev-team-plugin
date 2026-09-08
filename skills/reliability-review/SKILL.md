---
name: reliability-review
description: Review existing or changed code for how it behaves when things go wrong — unhandled failure paths, resilience patterns applied to the wrong failure, resource lifecycle, undiagnosable failure modes, alert quality, and performance problems that are actually correctness problems. Produces a severity-ranked findings report. Use when reviewing a change for production-readiness, or when something works in development but is worrying under real conditions.
---

# Reliability Review

## Scope

Code and configuration that already exists — the counterpart to
`reliability-requirements`. You produce a findings report and edit nothing.
Review what changed; note pre-existing issues separately as lower priority.

The question: **what does this do when its dependencies misbehave, and
would anyone find out?**

## Failure paths

Walk each thing the change depends on and check the paths that aren't the
happy one:

- **Every call that can fail has a defined outcome.** An unhandled failure
  in a path that matters is the highest-value finding available here, and
  it's usually invisible on a read of the success path alone.
- **Slow is a failure mode, and it needs a timeout.** A call with no
  timeout doesn't fail — it waits, holding whatever it holds, until
  something upstream gives out. Missing timeouts are underreported because
  nothing looks wrong until the day it does.
- **Errors aren't swallowed.** A catch block that logs at debug and
  continues has converted a failure into wrong behavior, which is strictly
  worse — the system now proceeds on bad state and nobody knows.
- **Partial completion leaves defined state.** If the operation dies
  midway, what's left behind, and can it be resumed or retried safely?
- **Expected and unexpected failures are handled differently.** Routine
  validation failures shouldn't be alerting anyone; genuine faults
  shouldn't be hidden behind the same friendly message.

## Resilience patterns: check the pattern matches the failure

Each pattern addresses a different failure, and applying the wrong one is a
finding in itself — often a worse one than applying none, because it looks
handled.

- **Retry** — for transient failures only.
- **Timeout** — for never waiting indefinitely.
- **Circuit breaker** — for stopping a failing dependency from taking you
  down with it.
- **Bulkhead** — for containing a failure to one area.
- **Graceful degradation** — for partial service beating none.

**The finding to look for hardest: retrying something that isn't
transient.** Retrying a deterministic failure — bad input, a permission
denial, a malformed request — is not resilience. It's amplification: it
turns one failure into several, adds latency to a request already doomed,
and can generate a load spike against a dependency that is already
struggling. Check that retry logic distinguishes what's worth retrying,
and that retries back off rather than hammering.

**Resilience logic belongs in the adapter, not in business logic.** A use
case shouldn't know that its dependency retries. When you find retry or
circuit-breaker logic interleaved with domain decisions, that's a finding —
and it's the same boundary `software-architect` draws, so say so rather
than inventing a new justification.

## Resource lifecycle

Connections, handles, streams, subscriptions, timers, listeners — anything
acquired needs a release on every path, including the failure paths.
Unbounded growth belongs here too: a collection that only ever accumulates,
a cache with no eviction, a queue with no limit.

These deserve attention out of proportion to how they look, because they
fail slowly, only under sustained real use, and never in tests.

## Observability, framed as diagnosability

Don't review this as coverage. Review it as: **for each way this can fail,
could someone determine that it failed, and tell it apart from the other
ways?** Where the answer is no, that's the finding — stated as an
undiagnosable failure mode, not as a missing metric.

Related checks:

- **Structured context over concatenated message strings.** A log that
  interpolates values into prose isn't queryable later, which is the only
  reason it exists.
- **Something ties records together across boundaries.** Without a shared
  identifier threaded through, records from one operation are three
  unrelated stories.
- **Errors carry enough context to act on** — what was being attempted,
  against what, with what outcome.
- **Nothing sensitive is being logged.** This overlaps `security-review`
  deliberately; flag it here when you see it rather than assuming the other
  pass caught it.
- **Volume and cost are considered** on high-frequency paths. Excessive
  instrumentation is a real cost, and sampling is a legitimate answer.

## Alert quality

Where alerts exist, they're findings-worthy when they aren't actionable —
if there's no answer to "what would someone do about this," it isn't an
alert, it's a notification. Check that thresholds are anchored to a stated
target rather than picked arbitrarily, and that severity distinguishes
wake-someone-up from look-at-it-tomorrow.

**Alert fatigue is a finding in its own right.** An alert set that fires
routinely is worse than no alerts, because it trains people to ignore the
one that matters. A noisy alert is not a minor issue to tune later — it's
actively degrading the thing alerts exist for.

## Performance: separate correctness from speed

These are different findings with different bars, and conflating them is
how performance review turns into noise.

**Performance-as-correctness** — a finding regardless of current load,
because it fails by construction, eventually:

- Resource leaks and unbounded growth
- Result sets with no limit or pagination
- Work that grows without bound with input size on a path that takes
  arbitrary input
- A query per item in a loop, where one query would do

**Performance-as-speed** — algorithm choice, caching, sync versus async.
**Only a finding when it comes with a concrete scale story**: at what
volume, on which path, with what user-visible consequence. Without that,
it stays an observation. Flagging theoretical slowness manufactures exactly
the premature-optimization noise that makes reviews ignorable.

## Severity

- **Critical** — data loss or corruption possible; an unhandled failure on
  a path that matters; a leak that will exhaust something.
- **High** — a missing timeout on an external call; retrying
  non-transient failures; a failure mode nobody could diagnose; a query per
  item on a path taking arbitrary input.
- **Medium** — degradation that hides a real problem; observability gaps on
  secondary paths; alert quality problems; missing context in error
  handling.
- **Low** — instrumentation worth having; minor cleanups; speed
  improvements with a real but modest story.

Severity tracks production consequence. Dev-environment relaxations are
legitimate — what matters is whether they reach production.

## Finding report format

Use the same format as `security-review`, replacing **Reachability** with
**When this bites**: the conditions under which the problem actually
manifests — the load, the failure, the sequence. A reliability finding
without those conditions stated is speculation.

List findings most severe first. If nothing rises above Low, say so.
