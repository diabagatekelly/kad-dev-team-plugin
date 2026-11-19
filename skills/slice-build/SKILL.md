---
name: slice-build
description: Build a whole planned slice as one builder, inside the orchestrator's `solo` cadence — every criterion held by one test at the level that reaches it, written first and seen failing, a second test only for a branch the first cannot reach, exact wording in one table per message module, commits in steps of the builder's own choosing — and apply the one batch of confirmed fixes handed back afterwards. Invoke it only when a task names it by this name, which the orchestrator's S step does (`kad-dev-team:tdd-coach:AGENT` with `kad-dev-team:slice-build` to invoke first). A plain "build it" or "implement this" is the orchestrator's; a chunk of a chunk plan is `tdd-implementation-lite`'s.
---

# Slice build

One builder builds the whole slice. There is no chunk plan and nobody
reviews you commit by commit: the gate, a mutation pass, a cold reader
and a walk of the criteria in a real browser come after you, on the
whole thing, and only what they confirm by running it comes back.

This is a measured arm (the owner, 2026-11-18): the same slice is built
a second way, and the two are compared on what a stranger finds by
running the code, on what the tests catch, and on cost. The one rule
that differs most from the other arm is the test rule below. Slice 4 of
the first project had 2,450 lines of test for 573 of source, 35
criteria each tested at two levels and its wording asserted sentence by
sentence, and its quality scores did not move.

## What is yours and what is not

You turn a decided design into code. The module boundaries, interface
ownership and names of the design document are the structure you build
inside. You do not decide what is built (`product-manager`,
`product-slicer`), how it is structured (`software-architect`) or what a
screen looks like (`ux-designer`), and you never edit one of their
documents. You run in the background and ask the owner nothing.

The task hands you, by absolute path: the slice file, the design
document, the domain model when the project has one, the security and
reliability criteria, the screen design and accessibility criteria for a
slice with a screen, the project root, the documented test command, the
report path, the design's module directories and the orchestrator's
scripts directory. Read them all before writing anything, then the code
the slice runs beside.

## One test per criterion

1. **List the criteria.** Every Given/When/Then of the slice file and of
   the security, reliability and accessibility documents, by its
   identifier (its text quoted when the document numbers nothing). A
   bullet under `## Design notes` is not a criterion: build what it
   says, and write no test for it.
2. **Each criterion is held by one test, at the level that reaches it.**
   That is the outermost level the project's suite can drive: the
   running app through its real interface (a request to the route, the
   page in the project's own browser or DOM harness, the command line)
   wherever the criterion is something a person or an operator would
   see. Go one level in only when the outer one cannot produce the
   situation (a provider that fails, a clock, two requests that
   interleave): then the fault is injected at the port the design names
   and everything inside it is real. Say which level, and why when it
   is not the app.
3. **A second test for a criterion only for a branch its test cannot
   reach.** A module-level test is written for a branch (an error path,
   a boundary of a calculation) that no criterion's test can take, is
   named for that branch, and asserts nothing a criterion's test
   already asserts. The same behaviour is never asserted at two levels.
   No test for a getter, a type, a constant, or wiring a criterion's
   test already passes through.
4. **Exact wording is held once.** Every message, label and heading the
   slice shows is an exported constant of one module of strings (per
   screen or per app, as the design names it). One table test per such
   module holds the exact words: a list of constant and sentence, one
   assertion over the list. Every other test asserts on the constant,
   never on a sentence typed again, and no criterion's test fails
   because a sentence changed.
5. **Written first, seen failing.** The tests before any code, stubs
   included, through the public interface the design names. Then a stub
   that does nothing useful, and one run: every test fails on its own
   assertion, not on a missing module, a typo or a setup error; fix the
   test that fails for the wrong reason before going on. Then the code
   the tests ask for and nothing the slice does not need, and the whole
   suite green.
6. **One break, caught.** Break the line where the slice's main rule
   lives, run, see a test fail, restore, run green again. The restore
   comes before anything else, whatever the broken run showed.

A test asserts through the interface, never by reaching into an
adapter's private state. When a port exposes too little to show what a
criterion names, assert through what it does expose or escalate the gap
(below); never peek.

## While you build

- **Every test run is real**: the project's runner, its output read
  whole. If the tests cannot run, say so and stop; "could not run" is
  never "done".
- **Files change through `Write` and `Edit`, never the shell** (no
  redirection, heredoc, `sed -i`, script or `cp`). The gate replays what
  you ran and counts every shell edit on the record.
- **Check what exists first.** Grep the suite's support folder and
  consult `map-query` before writing a helper or a module; one that
  exists is imported. A helper a second test file needs goes in the
  support folder.
- **No comment unless `why-comments` would keep it**, and never a
  planning document, a decision number or a criterion cited in code.
- **Stay inside the slice.** A problem in older code is a line of your
  report, not a change, unless the slice cannot work without it.

## Commits

You commit in steps of your own choosing: a behaviour with its tests is
a good step, and one commit for the whole slice is allowed when it is
small. Every commit, the same way:

1. The full suite as its own command, its result read, green. Never the
   test run and the commit on one line.
2. The gate's checks, and the commit only on `checks: PASS`:

   ```
   python3 -I '<scripts directory>/validation_gate.py' --project '<project root>' --test-cmd '<test command>' --checks-only
   ```

   A `FAIL` your change caused is yours to clear in your code, never by
   raising a baseline or editing `gate-checks.json`, a tool's
   configuration or an ignore file. A check that cannot run here, or
   that fails the same way without your change, does not hold the
   commit: say so in the report (`checks: FAIL <check>, not this
   change's: <why>`). Run the format check too when the manifest has
   one, on the files you changed.
3. `git add` each file by name, never `-A`, `.` or a directory.
4. `git commit` with what the step delivers as the subject and a
   `Delivers:` line naming the criteria made green. No trailers.
5. Never push, amend, rebase or switch branches.

## Gaps in the design

Sort each gap with one question: would filling it change what gets
built, or only how?

- **Only how** (a parameter's name, the order of two checks with one
  outcome): decide it and say so in the report.
- **What gets built** (a new rule, a state the domain model does not
  have, anyone else affected): do not build it. Leave it out of code
  and tests, name it in the report with its owner
  (`architecture-design` for structure, `acceptance-criteria` for
  behaviour, `domain-model` for a missing state), and build the rest.

## The report and the hand-back

Write the report at the path the task gave, before the last commit, and
commit it with that commit. Nothing else goes in it:

```markdown
# Implementation report: slice <nnn>

## Criteria
| Criterion | Test | Level | Why this level |
|---|---|---|---|
| <identifier> | "<test name>" | app / port / module | <only when not app> |

## Branch tests
| Test | Branch | Why no criterion's test reaches it |
|---|---|---|

## Wording
<strings module>: "<table test name>" (<n> strings)

## Decided
- <gap>: <choice>

## Escalated
- <gap>, <owner> (or "none")

## Deviation
- <file outside the design's modules>: <why> (or "none")

## Verified
First run: <n> tests, all failing on their assertions. Suite: <n> green.
Break: <what>, caught by "<test>", restored, green.
```

Every criterion has exactly one row of the first table. Your last
message is one line and nothing else: `built <first sha>..<last sha>;
<c> criteria, <t> tests; deviations <n>; <report path>`, the hashes as
`git rev-parse --short` printed them.

## Asked about survivors

After the build you may be sent the mutation report's path. Answer with
one line per survivor it lists, and change nothing: `real: <the
assertion or test that is missing>` when the break changes something a
criterion or a branch test should have noticed, `equivalent: <why>`
when no behaviour a person could observe differs. Read the line it
broke before answering; a survivor in a line you cannot explain is
`real`.

## A fix handed back

One batch at most comes back, and everything in it was confirmed by
running the code: a failing check, a survivor you called real, a bug a
reader reproduced, a criterion the walk failed. The agent applying it is
often not the one that built the slice; read the report and the code
first.

- **Reproduce before you change.** For each finding, a test that fails
  on it now, at the level that reaches it (a failing check is its own
  reproduction). If a criterion's test should have caught it, that test
  is corrected, not joined by a second.
- **Fix what the finding describes, not what it suggests.** Its
  suggested mechanism was written without running anything. A fix that
  adds something nothing uses, or goes round a routine that already
  does the job, is the wrong fix.
- **Change nothing the findings did not name.** What you notice nearby
  goes on your hand-back line.
- A test you rewrite keeps every assertion it had, and a test whose
  behaviour changed is renamed where it is registered.
- One commit, made as "Commits" says, its subject `Fix: <finding
  titles>`. Add to the report, under a `## Fixes` heading, one line per
  finding: `<title>: "<test>" shown failing on <what>, then green`.

Your last message is one line: `fixed <sha>; <n> findings; <t> tests
added or changed; <anything not fixed and why>`.
