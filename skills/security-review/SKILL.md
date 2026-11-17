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

## A serious problem that is another review's

While reading for this review you will sometimes see a problem that is
serious and is not this review's subject: a change to stored data that cannot be undone or rolled back, a retry that repeats a payment, a failure nobody would be told about, a test that cannot fail.
It is not yours to rank, and it is not yours to read past. Write it at
the top of the report, above `## Findings`, under `## Handed on`, one
line per problem:

```markdown
## Handed on

- <what is wrong, in a clause>; `<path>:<line>`; appears <Critical | High>; owner: `<the review that owns it>`
```

The severity is the one the problem appears to have on its owner's
scale, never one rated down to fit this review's categories (a migration with no way back is not a Low "hardening" note because an attacker is what this review rates; with no adversary in the story it is not yours at all).
The line is never one of your findings: no `###` heading, no
`**Severity:**` line, no place in the ranking and no suggested fix, so
no fixer is handed it on a judgement this review is not the one to
make. One line is all of it: the owning review verifies it, sizes it
and says what to do. Only what appears Critical or High goes there; a
smaller thing outside your subject is left unsaid. The owners:
`code-review` (readability, names, comments, code the change does not
need), `test-quality-review` (what the tests prove),
`architecture-review` (boundaries and the direction of dependencies),
`security-review` (anything whose harm needs an adversary),
`reliability-review` (what happens when something fails),
`accessibility-review` (a rendered screen), `supply-chain-review`
(dependencies and their pinning), `operational-readiness` (shipping and
rolling back). In a combined chunk report, a problem one of the
launch's own lenses owns is that lens's finding, not a line here. With
nothing of the kind seen, the section is left out.

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
   it is right. Reviewers each reading one side of a seam missed an
   orphaned provider record three runs running (incident 1).
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
fails. An accepted deferral of the slice
file (its `Still open` and `Explicitly deferred` items) is not restated
as a finding: `deferrals.py` lists each one once in the pull request's
body, and the same handful said by every criteria reviewer was a
quarter of one slice review's findings (incident 37). What the code
does because of a deferral is still yours: a state a person can reach
with no way out is a finding on the code, at its own severity, whether
or not a document accepted it (incident 14). The regressions-only re-review at
round 1 is different and stays as it is:
handed the fix's diff range and the files it touched, it reads those.

Why the order: a reviewer handed nothing traced the seam in one pass and
confirmed a second bug by running it, where six handed the documents
first had read past it; the same protocol on Opus found every
load-bearing bug on three runs' recorded lists
(`.synthesis/cold-read-check/`). The documents are the second pass
because they tell you what to look for, and the cold pass is for what
nobody wrote down.

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

## A value of the owner's in the repository

A row of a file the owner provided (a sheet or an export the planning
directory's `sources.md` lists by location) that turns up in a test, a
fixture, a planning document or a commit message is a finding, and it is
found with the scan, never by opening the source or grepping for a value
(either puts the value into your transcript and your command line):

```
python3 -I "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/source_scan.py" scan --planning '<the planning directory>' --history '<the range under review>'
```

and the same without `--history` for the tree. The finding names the
file, the line and the cell the scan printed and **never quotes the
value or describes it closely enough to identify it**: your report is
committed with the records, and a removal has had to be done twice
because its own record named what it had removed (incident 18). Severity is by what
the value is: High for a credential, an account or card number, Medium
for a name or an amount. The **Suggested fix** names the procedure, not
a `sed`: replace it in the tree with an invented value, and for the
commits that already hold it, `release-engineer:delivery`'s "Removing a
value from history" (the owner's words, a replacement map outside the
repository, every commit scanned before the push, a lease on any
force-push). With no `sources.md`, a real-looking value in a fixture is
the Medium the severity list already names.

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
The same rule the other way: nothing about how the code came to be
lowers a severity. A design that mandates the finding, a note that the
user has already been told, a decision already escalated — each changes
who owns the fix and says so in the finding's fix line, and none of them
changes what an attacker reaches. A card number reaching a persistent
log is High whether an approved design asked for it or not; "Medium
because the design mandates it" is a severity set by process, and the
report's reader, who may be a procedure that acts on Critical and High
alone, then never sees the High.

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
`**Reachability:** who controls the input, and the path from there to the
consequence`; that line is what makes it a finding. Its **Location** may be
a configuration file; its **Why it matters** says what an attacker gets or
what is exposed. If nothing rises above Low, say so plainly: a padded
report trains people to skim the one that matters.
