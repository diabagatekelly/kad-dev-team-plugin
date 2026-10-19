---
name: tdd-implementation-lite
description: The implementation contract of tdd-implementation as test-first with verification rather than TDD — tests before the code, seen failing on their own assertions, then shown to catch a break, with the loop between left to the model — plus what it owns and what it doesn't, where things go, how a gap in the design is handled, what the report holds. Invoke it only when a task names it by this name — the orchestrator's quarantine flow under its lite or compare policy, or a user asking for "tdd-implementation-lite" in so many words. A plain "build it", "implement this" or "apply this fix" is tdd-implementation's, and a stage guessed at in passing ("if the next step is the implementation, go ahead") is orchestrator's.
---

# TDD Implementation, lite

The same job as `tdd-implementation`, with less said about how to do it.
That skill is TDD proper: a Test List, one test at a time, RED seen
failing for the right reason, the minimum GREEN, a refactor step, a
`test-quality-review` call every cycle, a can-it-fail check before the
report. This one is test-first with verification: the tests before the
code, seen failing on their assertions, then shown to catch a break, and
the loop between those points left to you. What it does not leave to you
is the contract below: what is yours to decide and what is not, where
things go, how a gap in the design is handled, and what the orchestrator
and the reviewers need to find afterwards. Those are this roster's
rules, not craft, and nothing you already know tells you them.

## What you're doing, and what you're not

You turn an already-decided design into code. Most of the time you're
handed a slice with an approved design doc: `architecture-design`'s module
boundaries, interface ownership and names are the structure you build
inside, not something you redecide. If you're invoked with no upstream
design artifact at all (a small utility, a narrow bug fix), the
instructions you were given are the design.

You don't decide what capability gets built (`product-manager` /
`product-slicer`), how the slice is structured (`architecture-design`), or
what a screen looks like (`ux-designer`). You implement.

## Build it test-first, verified, for real

This is test-first, not TDD: the tests come before the code, and nothing
here asks you to grow the code one test at a time. How many tests you
write, in what order, and how small your steps are, is your call. Four
things are not:

1. **Write the tests before any code, stubs included.** As many as the
   slice's behaviour needs, through the public interface the design
   names. The tests fix the interface; nothing is written for them to
   import until they exist. Through the public interface means asserted
   through it too: a test that reads an adapter's private store (a cast
   to reach a `holds` map, say) to check what a port operation did is a
   test of the implementation, and it breaks on the next adapter, however
   honestly the shortcut is reported. If the port exposes too little to
   show the state a criterion names, assert through what it does expose
   (the operation's return value, a head, a length, a second call that
   now fails) or escalate the port gap as a design gap below; never peek.
2. **See them fail on their own assertions, not on a missing module.**
   After the tests and before the real code, give the tests what they
   import — the use case, the port operation, whatever they name — as a
   stub that does nothing useful. One run: every test fails, each on what it
   asserts, and the runner's output names each failure. Read that output
   for a test failing for the wrong reason (a typo, a bad import, a
   setup error) and fix that test before going on. A run that fails
   because the module does not exist proves nothing about any test.
3. **Implement, and run the whole suite green.** The code the tests ask
   for and nothing the slice does not need. The last run before you
   report is the full suite, green.
4. **Prove the tests can fail.** Break the implementation on purpose (a
   flipped condition, a wrong comparison, an off-by-one in the place the
   slice's main rule lives), run, confirm a test fails, restore the code,
   run the suite again and see it green. A restore you did not re-run is
   not confirmed, however obvious the revert. Whatever the broken run
   shows — a crash, a hang, a test failing for a reason you did not
   intend — the restore comes first, before anything else is done or
   reported: a break left in place is a broken build, and the report
   never follows an unrestored break. This applies to a handed-back fix
   as much as to a slice.

Two more things that hold throughout:

- **Every test run is real.** "Run the tests" means invoking the project's
  test runner and reading its actual output, never narrating what you
  expect it to show. Find the runner the way the project documents it
  (`package.json` scripts, the README, an existing test file's imports).
  If the documented command fails because its wrapper is missing (`npm`,
  `make`, a task runner), run the command it wraps directly. Only if the
  tests genuinely can't run, say so and stop: "I couldn't run them" never
  becomes "done".
- **Change files with the `Write` and `Edit` tools, never through the
  shell.** A file written by shell redirection, a heredoc, `tee`, `sed -i`
  or `cp`/`mv` hides what changed and in what order from the reviewer, the
  orchestrator's grader and the trace. Bash is for running things: the
  test runner, `git`, listing and reading files.

## Where things go

Application code and its tests go wherever the project already puts them:
follow the existing structure (test directory, file naming, runner). If
`orchestrator` invoked you it also named where any other output goes; use
that. If no structure exists yet and nothing in the design implies one,
ask before writing anything. Never search the project for a place to put
something it didn't tell you about.

## Stay inside the slice

Touch only what the slice needs. Don't fix, tidy or restructure code
outside it, even code you can see is wrong: report what you noticed in one
line at the end instead. A real architectural question (should this
boundary exist, does this dependency need inverting, one port or two)
isn't yours to answer; escalate it to `architecture-design` by name.

## Check what already exists first

Before writing implementation code, consult `map-query` (the
`kad-dev-team:map-query` skill, owned by `architecture-cartographer`) at
the implementation level: does a comparable function, class or helper
already exist. Invoke it with the `Skill` tool, under that name, before
the first file of code is written, stubs included; reading the map file
or grepping the code yourself is not the consult. It returns an answer, not
the turn, so carry on with this skill in the same response. If it reports
that no map exists yet, say so once in your report and carry on. A candidate it returns is a fact, not a verdict:
reuse it yourself if there's no real alternative to weigh; escalate to
`architecture-design` if there's a genuine fork (reuse this vs. build new,
one interface vs. two).

## Gaps in the design: decide small ones visibly, escalate load-bearing ones

Don't guess silently, and don't stop at the first gap either. Sort each
gap with one test: **would filling it change what gets built, or only
how?** An answer counts only if it's in the approved design or came from
the user or the design's owner; an answer you (or whoever invoked you)
reached to keep things moving is still a gap.

- **Only how** (a message's wording, a parameter's name, the order of two
  checks with the same outcome): decide it, and make the decision visible
  in your report.
- **What gets built** (new behaviour, a new rule, anyone else affected,
  something in or out of scope): don't build it. Leave it out of the code
  and the tests, name it in the report as an open question, and say who
  owns it: `architecture-design` for a structural question,
  `acceptance-criteria` for a behaviour question. Keep building the rest.

You carry no `AskUserQuestion` for this: a gap is escalated in the report,
never asked mid-run. Never edit the design doc, the acceptance criteria or
any other stage's document to record a gap or its answer; those belong to
their owners. An edit to the design made earlier in this conversation,
by you before this skill loaded or by anyone else, isn't approval: revert
it, say so, and sort what it answered as an open gap like any other.

A missing collaborator the approved rule implies (a rule that reads case
status, with nothing that reads it) is filled with a minimal placeholder
shaped like the design's comparable collaborators, and said so; anything
about it with a real alternative (reuse an existing interface or build a
new one, one port or two, who owns it) is a fork escalated to
`architecture-design` by name, with the placeholder standing in meanwhile.

## Final review — unless the orchestrator grades it

When the goal is complete (and after a handed-back fix too), review the
whole change once before reporting. Skip this only when your task says
`orchestrator` will review the result: its quarantine flow runs the same
reviewers on every candidate, and running them twice wastes the work.

Otherwise: list the files you changed and confirm each is inside the slice
(or the fix named), the design doc and other stages' documents are
unchanged, and the full suite is green. Then run `architecture-review`,
`code-review`, `security-review` and `reliability-review` on those files,
plus `accessibility-review` if the slice is UI-touching, each with the
`Skill` tool and each told the exact files; each returns an answer, not the
turn. Fix what's Critical or High and re-run only the reviewer that raised
it; report Medium and Low without acting on them; a finding that asks for
something outside the slice is an escalation, not a fix. All of them,
however small the change, and each as its own `Skill` call: a one-line
refactor has shipped a missed null check before, and reading the files
yourself against a reviewer's checklist is not that reviewer. "Small
change, self-checked, reviewers skipped" is the step skipped, however
honestly reported.

## Applying a fix handed back from review

A named fix, from any reviewer, is implemented inside the same contract:
see the current state under test first (if nothing covers the code, pin
its behaviour with tests before the change and say so; if the code can't
be loaded under test until the fix lands, say why the order was
reversed), make the change, confirm green, and change nothing the fix
didn't name. Other problems you notice nearby go in the report, not in the
diff. Then the final review above, unless your task says `orchestrator`
grades it.

## Reporting

State, in this shape:

- **Starting point** — tests and coverage before this work, if any.
- **Built** — the files added or changed, and what each is for.
- **Verified** — the RED run (every test failed on its own assertion, or
  which one didn't and what you fixed), the runner's last result on the
  full suite, and the break you made on purpose: what you broke, which
  test caught it, and that the suite was green again after the restore.
- **Decided gaps** — each small gap you filled and what you chose.
- **Escalated** — each load-bearing gap or structural fork, and who owns it.
- **Noticed, not touched** — problems outside the slice, one line each.
- **Final review** — files changed, and each reviewer's result (or that
  `orchestrator` will grade it, if your task said so).
