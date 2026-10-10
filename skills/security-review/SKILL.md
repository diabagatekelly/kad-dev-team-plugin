---
name: security-review
description: Review existing or changed code and configuration for reachable security problems — sensitive data escaping through logs/errors/telemetry, injection, missing or bypassed authorization, secrets handling, and over-broad privilege. Produces a severity-ranked findings report. Use when asked to security-review a change, when a PR touches authentication, data handling, or permissions, or before shipping something that handles sensitive data.
---

# Security Review

## Scope

You're reading code and configuration that already exists — the
counterpart to `security-requirements`, which defines criteria before code
exists. You produce a findings report; you don't edit anything. Review what
changed or was added; note pre-existing issues separately as lower
priority rather than blocking on them.

When the review is of a change (a PR, a diff, a named set of new files),
the findings list holds only problems in code the change wrote. Anything
in code it didn't write goes in a separate "Pre-existing, not blocking"
section at the end — **including a pre-existing problem the change newly
routes traffic through.** Say there what new exposure the change adds
(e.g. "the new routes now send member tokens through this"), so the reader
can decide whether to fix it alongside; don't number it among the change's
findings or give it a blocking severity. The change is held only for what
it introduced.

Configuration counts as code here. An over-permissive role in a deployment
template, a workflow that hands every secret to a job that needs one, a
storage bucket open to the world — these are security findings that happen
to live in config files. What makes something yours is that the harm story
needs an adversary, not which file it's in.

**A control with nowhere to live is a finding, not a redesign.** Which
boundaries exist is `software-architect`'s decision; what each one must
enforce is yours. When the right check has no boundary to sit at, report
the missing boundary and leave the structure alone.

## The question that gates every finding

**Is it reachable, and by whom?** A finding needs a path from something an
attacker controls to something that matters. If you can't state that path
concretely, you have an observation, not a finding — say so, or drop it.

This is the discipline that separates a useful review from a checklist
run, and it's the reason the same pattern gets different severities in
different places.

## Sensitive data: five exits, not one

For any sensitive value the change touches, check every way it can leave.
Logs are the obvious one and the least of it:

1. **Logs** — including at levels nobody reads in development.
2. **Exception messages and stack traces** — a message that interpolates
   the bad value to be helpful is the classic case.
3. **Error responses** returned to a caller, including detail meant for
   debugging.
4. **Monitoring, telemetry, and analytics** — often overlooked because
   it's configured once and never re-read.
5. **Test fixtures and sample data** — real-looking values are a finding
   both because they may *be* real and because they defeat any scan for
   the real thing.

**Logging a whole object is a distinct finding from logging a sensitive
field.** Serializing an entire object leaks every field it has, including
ones added later by someone who never considered this log line. Flag it
even when the object's current fields are harmless — the failure is that
it's unbounded, and it fails silently the day a field is added.

**Log the identifier, not the subject.** Referencing a sensitive record by
an opaque ID keeps the trail useful without carrying the data. Opaque
means meaningless outside the system — a row id, a surrogate key, a
request id. A natural identifier the person carries or can be looked up
by (a card or account number, an email, a phone number) is part of the
subject, not a substitute for it; don't propose it as the fix. Where access
to sensitive data should be auditable, the audit record logs *that access
happened*, never the data accessed.

## Injection is one shape with many surfaces

The shape: attacker-controlled text becomes structure or code rather than
staying data. Recognize it across surfaces rather than checking a list —
database queries, OS commands, file paths, markup and templates,
deserialization, and anywhere a string is assembled into something an
interpreter will parse.

The fix is always the same idea: the untrusted part stays data and never
participates in deciding structure. Escaping is the weaker fallback;
parameterization and safe APIs are the fix. Flag manual escaping as a
finding when a safe construct exists.

## Identity, authorization, and privilege

- **Authentication present where it's needed** — new entry points are the
  usual gap, since they get added without inheriting whatever protects
  the existing ones.
- **Authorization distinct from authentication** — knowing *who* someone
  is doesn't establish that they may touch *this* record. Any lookup by an
  identifier a caller supplies deserves the question: what stops them from
  supplying someone else's?
- **Least privilege, as four separate choices** — the right identity, the
  right role, scoped to the right resource, for the shortest duration.
  Most over-privilege findings are a failure of scope or duration, not of
  role.
- **Broad-by-default grants are a finding on their own**, whether or not
  anything currently abuses them: a wildcard scope, a job handed every
  secret when it needs one, a permission block that's absent so defaults
  apply.

## Secrets and credentials

- No secret in source, in committed config, or in a plain environment
  variable — it comes from a managed secret store at runtime.
- **Prefer short-lived federated identity over any long-lived
  credential.** This is the highest-severity class of credential finding,
  because a leaked long-lived credential grants access indefinitely and
  usually silently.
- **Identifiers that aren't credentials can still be secrets.** Tenant,
  subscription, account, and resource identifiers don't authenticate
  anything, but they tell an attacker exactly what to aim at. The reflex
  is "IDs aren't secrets"; treat them as secrets anyway when knowing the
  value narrows an attacker's search.
- A secret that has ever been committed is compromised and needs rotating,
  not just deleting. Removing it from the current tree doesn't remove it
  from history.

## Error handling as an information-disclosure surface

Internal detail reaching a caller — stack traces, framework versions,
database errors, whether a record exists — is a finding, not just an
ergonomics problem. The distinction that matters: a caller learns that
their request failed; they don't learn why in terms that describe your
internals.

How to check: find every `catch` (or error handler) that writes a
response, and ask what the caller receives when the error is one nobody
anticipated — a driver, SDK or network error thrown from an adapter.
Returning `error.message` (or the error itself) from a catch-all is the
usual case, and it leaks even when every *expected* error in that path has
a deliberately friendly message.

## Before you report a Critical or High

Go back and verify the specific claim. Confirm the input really is
attacker-controlled, that the value really does reach that exit, that the
check really is absent rather than applied somewhere upstream you haven't
read yet. A first pass that pattern-matched its way to a finding is a
hypothesis. Medium and Low findings don't need this step.

The most common false positive in this area is a control that exists one
layer up — a validation applied at the entry point, an authorization check
in middleware. Look for it before flagging its absence.

## Severity

- **Critical** — an attacker reaches credentials, someone else's data, or
  code execution. Hardcoded live credentials. An authorization bypass on
  real data.
- **High** — a sensitive value reaching a persistent exit (logs,
  telemetry). Injection on a path reachable from user input. A missing
  authorization check where the data is scoped per user. A long-lived
  credential where federated identity is available.
- **Medium** — over-broad privilege with no current abuse path. Internal
  detail in error responses. Real-looking sensitive values in fixtures.
  Missing defense-in-depth on a path already protected elsewhere.
- **Low** — hardening worth doing, no plausible current path.

**Availability is a security finding only when one request costs out of
proportion to its size.** A catastrophic regex, an unbounded result or
allocation, a decompression bomb, an expensive operation an anonymous
caller can trigger once and make the system pay for many times — those
are attacker leverage, rate them like any other finding. "No rate limit"
or "this query scans the table" on an ordinary endpoint is a capacity
question: it needs a concrete scale story (what volume, on which path,
with what consequence), which is `reliability-review`'s job. Without that
story, note it as Low at most.

Severity tracks the reachable consequence, not the category. Don't inflate
severity to force a fix — state the trade-off and let the user decide.

## Finding report format

```markdown
## Finding: <short title>

**Location:** where in the code or config
**Category:** what kind of issue
**Severity:** Critical | High | Medium | Low

**Reachability:** who controls the input, and the path from there to the
consequence. This is the part that makes it a finding.

**What's happening:** the current state, concretely.

**Why it matters:** what an attacker gets, or what's exposed.

**Suggested fix:** the specific change. Name the approach, not a diff.
```

List findings most severe first. If nothing rises above Low, say so
plainly — a padded report trains people to skim the one that matters.
