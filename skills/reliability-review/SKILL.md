---
name: reliability-review
description: Review existing or changed code and configuration for how it behaves when things go wrong — unhandled failure paths, resilience patterns applied to the wrong failure, resource lifecycle, undiagnosable failure modes, alert quality, and performance problems that are actually correctness problems. Produces a severity-ranked findings report. Invoke first, before reading any code, for any request to review a module, job, PR, route, adapter or alert configuration for production-readiness, reliability, resilience, failure handling, timeouts, retries, observability or alerting — including a plain "is this ready for production?" or "what happens when the database/provider is slow or down?" — and when something works in development but is worrying under real conditions. Never review reliability without it.
---

# Reliability Review

## Scope

Code and configuration that already exists — the counterpart to
`reliability-requirements`. You produce a findings report and edit nothing.
Review what changed; note pre-existing issues separately as lower priority.

When the review is of a change (a PR, a diff, a named set of new files),
the findings list holds only problems in code the change wrote. Anything
in code it didn't write goes in a separate "Pre-existing, not blocking"
section at the end — **including a pre-existing problem the change newly
depends on or makes matter more** (a store that was already process
memory, a call that already had no timeout). Say there what new exposure
the change adds (e.g. "staff now act on a queue a restart empties"), so
the reader can decide whether to fix it alongside; don't number it among
the change's findings or give it a severity at all. A pre-existing High
listed among the findings reads as a finding against the change to
whoever acts on the report — the orchestrator's re-grade hands every
Critical and High back as a fix — and "not recommending it block" in the
body does not undo the heading. The change is held only for what it
introduced.

The question: **what does this do when its dependencies misbehave, and
would anyone find out?**

## Cold pass first, under the chunk loop

When the orchestrator's chunk loop launches you at a round 0 (the
chunk's combined review at its C.3, the slice review at its D.3), the
task hands you five things and nothing else: the project root, the
documented test command, the commit range, the report path, and the
path of the gate's last output on this tree. No planning document, no
earlier report, no record, no git log: you learn the code from the
code, in this order.

1. **Read the code whole, not the diff.** `git diff --stat <range>` names
   the modules the range touches; read every file of each of those
   modules in full, and every test file that exercises them (at D, all of
   `src/` and `test/`). The diff says what moved; the module says whether
   it is right. Run 3's slice reviewers, each reading one side of the
   exchange-once seam, missed an orphaned Plaid Item three runs running.
2. **Run the checks** from the project root with the manifest's own
   scripts: the typecheck, the lint and the format check where each
   exists. The full suite you do not run: the gate ran it on this very
   tree minutes ago and the task hands you its output file; read the
   suite's result there (the smoke agent is starting the app on the same
   checkout as you work, and at D five other reviewers share it, so six
   suites at once would contend for ports and files). Never install: the
   tree was installed with the frozen lockfile before you were launched.
   Open the report with a `## Checks run` section, one line per command
   with its exit code, and one for the suite naming the gate output it
   came from.
3. **Probe every suspected bug by execution** where you can: a scratch
   script outside the tree (the session's scratchpad, importing the
   module by path) or a one-off test invocation; never a change to any
   file in the tree, never the app against a real external service. Each
   finding carries a `**Status:**` line under its Category: `confirmed by
   execution`, with the probe and its output in the body, or `verify`,
   with what would confirm it.
4. **Write the cold findings** under `## Findings`, in the shared format
   below, ranked. A cold finding never cites a planning document: it
   stands on the code and the run.

**Only then the second pass.** Open the slice's planning documents (they
live in the target directory above the report's records directory: the
slice file, the design, the criteria this skill owns) and check the code
against those criteria, under its own heading, `## Against the
criteria`, in the same format; a finding here may cite the criterion it
fails. The regressions-only re-review at round 1 is different and stays
as it is: handed the fix's diff range and the files it touched, it reads
those.

Why the order: a reviewer handed nothing traced the seam in one pass and
confirmed a second bug by running it, where six handed the documents
first had read past it; the same protocol on Opus found every
load-bearing bug on three runs' recorded lists
(`.synthesis/cold-read-check/`). The documents are the second pass
because they tell you what to look for, and the cold pass is for what
nobody wrote down.

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
- **State that has to outlive the process doesn't live only in it.** Check
  each store the code writes to: one backed by process memory loses
  everything on every deploy, restart and crash, and each instance has its
  own copy. That's data loss, not a cache miss, when users created it.
- **Expected and unexpected failures are handled differently.** Routine
  validation failures shouldn't be alerting anyone; genuine faults
  shouldn't be hidden behind the same friendly message.

## Resilience patterns: check the pattern matches the failure

Each pattern addresses a different failure, and applying the wrong one is a
finding in itself — often a worse one than applying none, because it looks
handled.

- **Retry** — for transient failures only. A missing one is a finding
  only when you can name what a transient failure on that path loses that
  a retry would have saved: a write that's dropped, a job nobody reruns, a
  partner call with no second chance. A read that fails cleanly to its
  caller (an error the user can simply repeat, reported to monitoring)
  loses nothing a retry would save; at most it's a Low note.
- **Timeout** — for never waiting indefinitely.
- **Circuit breaker** — for stopping a failing dependency from taking you
  down with it.
- **Bulkhead** — for containing a failure to one area. A missing one is a
  finding only when you can name the shared resource, the load at which
  one consumer exhausts it, and why that load is plausible here (from what
  the repo states about traffic and scale). Without those three, it's a
  Low note.
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

How to check: follow every constructor and factory call on the path you're
reviewing (`new X(...)`, a wiring or `create*` function) into what it
builds, and ask whether it acquires something — a connection or pool, a
socket, a file handle, a timer, a listener. Then ask how often that call
runs (once at startup, per run, per request) and what releases it. A
resource acquired per run or per request and never released is a leak even
when each instance looks fine; a sibling that reuses a shared instance is
the usual tell.

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
- Work that grows without bound with what a caller sends, on a path that
  takes arbitrary input
- A query per item in a loop, where one query would do

How to check for unbounded results: for each query a route or job
reaches, find its limit. A query with none, over rows that only
accumulate (history, events, logs, anything never deleted), is a finding
even when today's numbers are small, and it's easy to miss when the same
query has a louder problem: report both.

**Performance-as-speed** — algorithm choice, caching, sync versus async,
and cost that grows with how much data is stored or how much traffic
arrives (a scan over a table, a pool shared with no bulkhead).
**Only a finding when it comes with a concrete scale story**: at what
volume, on which path, with what user-visible consequence. Use whatever
the repo states about its scale (a runbook, a README, a capacity note)
and check the story against it. Growth with stored data is never "fails by
construction": work out from the stated numbers when it would matter. If
they put it years away, it's a Low note. Without that,
it stays an observation. Flagging theoretical slowness manufactures exactly
the premature-optimization noise that makes reviews ignorable.

## Before you report a Critical or High

Go back and verify the specific claim: that the call really has no timeout
anywhere on its path (a client default, a wrapper, the adapter), that the
failure really is unhandled rather than caught a layer up, that the retry
really does fire on the failure you named. A first pass that
pattern-matched its way to a finding is a hypothesis. Medium and Low
findings don't need this step.

For a capacity finding (a missing bulkhead or circuit breaker, a shared
pool, a slow path), verifying means doing the arithmetic with the numbers
the repo gives: what the shared resource holds (pool size, workers), how
long each use holds it (query time, timeout), so what load exhausts it,
and whether anything stated about traffic makes that load plausible. On an
async server, a request that waits out a bounded timeout holds no thread;
say what it does hold. If the arithmetic doesn't support the severity,
lower it.

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

An observability or error-context gap is Medium only when a failure on
that path could not be told apart from the others with what is already
reported; when the cause is already distinguishable (a failure reason, a
path, an error class) and what's missing would make diagnosis quicker or
tidier (a component tag, a request id, a richer context, a runbook whose
wording doesn't match the field names), it's Low. Likewise a behaviour
you could not verify (a library's pool-wait semantics, say) is a
question to raise, not a Medium finding: say what you couldn't check and
what would settle it. Severity tracks production consequence. Dev-environment relaxations are
legitimate — what matters is whether they reach production. Don't inflate
severity to force a fix: when a recommendation collides with simplicity,
cost or scope, state the trade-off and let the user decide. And nothing
about how the code came to be lowers a severity: a design that mandates
the behaviour, a decision already escalated, a user already told — each
changes who owns the fix and belongs in the finding's fix line, not in
its severity.

## Finding report format

Every review skill in this roster reports a finding in this shape, so one
parser (`rounds_record.py`) and one fixer read them all:

```markdown
### <short title>

**Severity:** Critical | High | Medium | Low | needs-decision (<persona>)
**Location:** <path>:<line>
**Category:** <category>

**What's happening:** the current state, concretely.

**Why it matters:** what it costs if left.

**Suggested fix:** the specific change, named, not a diff.
```

One `###` heading per finding with the `**Severity:**` line directly under
it; the path project-relative, the line the one the fix would change (a
range as `12-20`); findings ranked most severe first under a `## Findings`
heading, which says `No findings.` when there are none. `needs-decision
(<persona>)` is the severity for a finding you cannot rate because no
planning document states the rule it would need: name the owning persona
(`software-architect`, `devsecops-engineer:reliability-requirements`,
`devsecops-engineer:security-requirements`, `ux-designer:screen-design`,
`accessibility-engineer`) and, under **Suggested fix**, the question that
persona has to answer; the orchestrator routes it before any fixer runs. A
pre-existing problem in code the change did not write goes under a `##
Pre-existing, not blocking` heading, with no `**Severity:**` line, so
nothing hands it to a fixer. Report-level sections (`## Summary`, `##
Findings`, `## Pre-existing, not blocking`, `## What's working`) are `##`;
nothing else is `###`.

This skill adds one line between **Category** and **What's happening**:
`**When this bites:** the conditions under which the problem actually
manifests, the load, the failure, the sequence`; a reliability finding
without those conditions stated is speculation. Its **Location** is the
file the fix would change, not every file that touches the symptom; its
**Why it matters** says what breaks, for whom, and whether anyone would
know; its **Category** is prefixed `reliability:` in a combined report.
Every finding carries all of these, Suggested fix included. If nothing
rises above Low, say so.
