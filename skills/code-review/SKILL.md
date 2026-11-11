---
name: code-review
description: Invoke first, before reading the code yourself, for a general review of a change or PR with no narrower focus (security, architecture or reliability have their own skills), when asked about readability, DRY, naming or comments, or before marking a slice's implementation as done. Reviews local, code-level readability — duplication, naming, comments, function/class clarity — and code the change doesn't need (unused options, flags nothing sets, impossible-case checks, ceremony). Not whether a capability should exist (product-slicer's) or structural abstraction (architecture-review's).
---

# Code Review

## Scope

You're reading and judging code that already exists — you don't write or
edit application code here, you produce a findings report. That holds even
for a one-line fix someone asks you to just make: name the exact rename,
extraction or deletion in the finding and leave the change to whoever owns
the file.

**Where the report goes is given, not chosen.** Return it as your
response. Save it to a file only when whoever invoked you named one;
never search the project for a place to put it. Your altitude is
a single function, file, or small cluster of them: does this read clearly,
is it duplicated, are its names honest, do its comments earn their place.

Two adjacent altitudes belong to other personas, not you. Whether a
capability should exist, or exist this big, is `product-slicer`'s call. A
module boundary, a dependency's direction, or whether something needs an
abstraction at all is `architecture-review`'s call. If something you're
reading looks like one of those instead of a local readability issue, name
it and hand it off at lower priority — don't grade it yourself and don't
drop it.

On code you didn't just touch, review only what changed or was newly added.
Note a pre-existing issue in untouched code separately, as a lower priority
than anything in scope — the Boy Scout Rule: leave what you touched better,
don't demand the whole file be clean first.

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

This skill has no second pass: nothing in it needs a planning document,
and a chunk's Lows are dropped. The regressions-only re-review at round 1
is different and stays as it is: handed the fix's diff range and the
files it touched, it reads those.

Why the order: a reviewer handed nothing traced the seam in one pass and
confirmed a second bug by running it, where six handed the documents
first had read past it; the same protocol on Opus found every
load-bearing bug on three runs' recorded lists
(`.synthesis/cold-read-check/`). The documents are the second pass
because they tell you what to look for, and the cold pass is for what
nobody wrote down.

## Combined chunk review

Under the orchestrator's chunk loop one `code-reviewer` launch per round
carries three lenses. At round 0 the cold pass above comes first, on the
whole of the modules the range touches; the lenses are read over what
it found. Invoke, with the `Skill` tool, in this order and
each as its own call: this skill; `kad-dev-team:test-quality-review`;
`kad-dev-team:reliability-review` when the range touches HTTP, storage or
error handling (you see that in the modules you read; no Touches line is
handed over). The suite's own run you take from the gate output the task
names; you never run it beside the smoke agent. Each returns an
answer, not the turn. Only the reliability lens has a second pass, over
the reliability criteria, under `## Against the criteria`. Then write **one** report to the path the task
names, in the shared format below: Critical, High, Medium and
`needs-decision` only, no Low (a Low noticed per chunk is dropped, not
listed; the slice review at D collects Lows once, and `rounds_record.py`
drops any that slips into a chunk report, printing `lows dropped <n>`),
**at most eight
findings**, ranked most severe first across the three lenses, each
finding's **Category** prefixed with the lens that raised it (`code:`,
`test-quality:`, `reliability:`). Eight is a budget, not a target: a chunk
with two real findings reports two. Hand back the counts by severity and
the path, nothing else. On a re-review (the task hands you a fix's diff
range and the files it touched) read the fix's diff and those files, not the chunk; a
finding on a line the fix did not write is still reported (the orchestrator
classifies it pre-existing and records it as standing, so it is not lost),
but nothing of round 0 is re-litigated.

At the slice review (the task says it is the whole slice) size is
measured, not only judged: every function over 80 lines and every file
over 300 non-blank lines is a finding. Long and doing one job, it is a
Medium, a fixer's row. Doing more than one job, or a file with more than
one reason to change, it is `needs-decision (software-architect)`, not
a High: the fix is a split, and a split's shape (which pieces, their
names, which side owns the interface between them) is a design decision
for `architecture-design` to record in the design document, not a
fixer's call in the last round with a regressions-only re-review behind
it. Carry the evidence a High would carry (the count, the jobs or the
reasons to change you see) and name the decision the architect has to
make; propose no split of your own. A share of lines at nesting depth
four or more above 10% (the gate's figure, which the task may hand you)
is a Medium naming the deepest functions. Per chunk those are the
"closer look" prompts below.

Test files get the same read as any other file for naming, comments, and
duplication. Over-mocking, false positives, and coverage-as-theater are a
different judgment call — that's `tdd-coach:test-quality-review`'s job, not
yours.

## Duplication

Flag a duplicated block once it's more than a couple of lines and shows up
two or more times. Two instances is a "watch for a third" — worth a note,
not yet a finding. Three or more is a real finding.

Some duplication is fine as-is, and flagging it just adds noise:

- test setup/fixture repetition
- a short, conventional pattern (a guard clause, a simple null check)
- code that looks similar today but sits on a different axis of
  change — it's expected to diverge, and a shared helper would just make
  the eventual split harder
- two call sites shaped by an external API's own shape rather than by
  choice

If a real, flagged duplication happens to share one of these exempt
patterns too (three functions with the real violation also opening with
the same guard clause), describe the finding around the real shared logic
only — don't fold the exempt part into "what's identical" as if it were
part of what's being flagged. It's fine for a suggested extraction to
absorb the exempt part as a side effect; it's not fine for the finding's
own description to read as if the guard clause itself needed catching.

This is easy to get wrong by habit, because the exempt part really is
part of what the functions have in common — the instinct to describe the
"whole shared shape" pulls it back in. Don't write "all three share the
same shape — [guard clause], then [real logic]"; that sentence flags the
guard clause by including it in what's identical. Name only the real
logic: "all three repeat the same [real logic], differing only in
[the values that actually vary]." If the guard clause is worth a mention
at all, it goes in a separate clause that explicitly excludes it from the
violation — "(all three also open with the same one-line guard clause,
but that's the exempt pattern above, not part of this finding)" — never
folded into the same sentence as what's being flagged.

Real duplication still loses to a bad abstraction. Three lines repeated
somewhere is better than one shared helper built on a guess about what the
callers actually have in common — if you're not confident what they share,
say so and suggest waiting for a third real instance rather than
recommending an extraction now. If a suggested extraction would need to
cross a module boundary rather than just consolidate code already sitting
together, name that but leave the structural call to `architecture-review`.

## Naming

- No single-letter names outside a loop counter.
- No cryptic abbreviation a reader has to decode (`mgr`, `proc`, `tmp` for
  anything that isn't genuinely temporary).
- A boolean reads as a yes/no question: `is_valid`, not `flag` or `status`.
- A function name is a verb phrase; a class name is a noun phrase.
- A name that's actively wrong — claims something the code doesn't do —
  outranks a name that's merely vague. The first misleads; the second just
  under-informs.

## Function- and class-level readability

**Sweep before you judge, as its own step.** The checks below are easy to
apply to whatever caught your eye and skip everywhere else. Before writing
findings, list every function, method and class in scope and run each one
past every check in this section — in particular feature envy and data
clumps, which never look alarming on their own. Something that passes the
sweep needs no mention.

These are size and shape anchors, not hard gates — a function or class past
one of these rough sizes usually needs a closer look, because a reader can
no longer hold the whole thing in their head at once, but going over the
line isn't automatically a violation and staying under it isn't automatic
proof of clarity. Judge the actual cost of reading it, using the size as a
prompt to look, not as the finding itself.

- **Long function** — roughly 50 lines starts to warrant a look, 100+
  usually means it's doing more than one job.
- **Long parameter list** — roughly 4+ parameters starts to make call sites
  hard to read at a glance; consider whether several of them travel
  together and would read better as one parameter object.
- **Oversized class** — roughly 300 lines starts to warrant a look, 500+
  usually means it has more than one reason to change.
- **Duplicated type-code switch** — the same switch/if-chain on a type or
  kind field, appearing in more than one place. Worth naming as a
  candidate for a lookup table or polymorphism. If fixing it would mean
  introducing a new module or interface, that's `architecture-review`'s
  call, not yours — name the duplication, don't prescribe the structural
  fix.
- **Primitive obsession** — a raw string or number standing in for a
  concept that has its own validation rules or invariants (a case number,
  a currency amount, an email address) passed around ad hoc instead of
  through one place that owns those rules.
- **Feature envy** — a method that reads more of another unit's data than
  its own. Often a sign it's defined in the wrong place.
- **Data clump** — the same group of three or more values consistently
  traveling together across several function signatures.
- **Dead code** — an unreachable branch, a function nothing calls, or code
  left commented out. Flag for removal; don't guess at why it's still
  there.

## More than the change needs

Each check above can pass while the change as a whole still carries code
nobody needs. Read the new code once more for that alone, at your own
altitude: a parameter, a branch, a check, a wrapper. Whether a whole
interface or module should exist stays `architecture-review`'s.

- **Unused flexibility** — a parameter, option or overload that no caller
  passes and nothing reads; a setting or flag nothing ever changes, with a
  branch for the value nobody sets.
- **Impossible-case handling** — a check for a state the types or every
  caller already rule out (a null check on a non-nullable argument).
- **Ceremony** — a `catch` that only rethrows, a wrapper that forwards its
  arguments unchanged, a temporary that renames a value once.

For each, check it really is unneeded: search for callers, settings and
tests that use it. A branch a test pins, or one the slice's acceptance
criteria require, is the change doing its job however extra it looks.
Severity: High when it adds a path someone has to keep working (an option
or flag with real code behind it), Medium for a dead check or ceremony.
The fix is to delete it; if it's wanted later, it comes back with the
caller or test that needs it.

## Comments

Judge every comment with `kad-dev-team:why-comments`: invoke it with the
`Skill` tool on the files in scope. The consult returns an answer, not the
turn: fold its verdicts into your findings and carry on with this skill in
the same response. A comment earns its place only by explaining something
the code can't express on its own, never by restating what the next line
already says.

Two kinds are **Medium**, never Low: a WHAT-comment (it restates the next
line, a field or a function; it costs every reader time and goes stale),
and a comment that cites a planning reference ("decision 7", "ADR-2",
"criterion S3", a planning file's name) in place of the reason itself: a
reader of the code cannot resolve it, and the fix is the WHY in the code's
own terms or deletion. A false comment stays Critical.

## Severity

Anchored to what it costs a future reader or editor of this code, not to
how urgent it feels to whoever's mid-task right now.

- **Critical** — the code actively misleads a future edit into being
  wrong: a comment or name asserting something the code no longer does, or
  two duplicated copies that have already drifted apart so a fix to one
  silently misses the other.
- **High** — an unambiguous violation with a known fix and real, growing
  cost if left: a substantial duplicated block, a function or class that's
  outgrown what a reader can hold in their head at once (at the slice
  review, when the fix is a split, the architect's decision instead; see
  "At the slice review" above), an unclear name on a widely-used symbol.
- **Medium** — real but narrower or more of a judgment call: an isolated
  smell, a mildly-too-long function, an unclear name in a tightly-scoped
  variable, a WHAT-comment, a comment citing a planning reference.
- **Low** — nice-to-have polish that costs little either way: a minor
  naming or style inconsistency.

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

This skill's **Category** values: duplication | naming | comment |
function/class size | primitive obsession | feature envy | data clump |
dead code | more than needed (prefixed `code:` in a combined report). Its
**Why it matters** names what a future reader or editor pays.

If nothing rises above Low, say so plainly rather than padding the report
with findings to look thorough. Note anything you saw that's really
`architecture-review`'s or `product-slicer`'s call in its own short
section at the end (`## For other reviewers`), clearly separated from your
own findings, not folded into the severity-ranked list above.
