---
name: tdd-implementation
description: Use before writing or changing application code — building an approved design or slice ("the design's approved, build it", "implement this") or applying a fix a reviewer handed back ("apply this finding", "architecture-review flagged X, fix it"). Invoke it first, before reading around, deciding anything or editing the design yourself: a design's open questions are this skill's to sort, so leave them unanswered. Writes the code test-first via genuine Red-Green-Refactor, one test at a time from a Test List. Not the skill to invoke when the user is moving a planned project forward and names implementation only as the stage they expect next ("if the next step is the implementation, go ahead"): that is orchestrator's call, and its chunk loop invokes this skill behind a sandbox check, once to write a slice's chunk plan and then once per chunk to build and commit it.
---

# TDD Implementation

## What you're doing, and what you're not

You turn an already-decided design into code, one small verified step at a
time. Most of the time you're handed a slice with an approved design doc —
`architecture-design`'s boundaries are the structure you build inside, not
something you redecide. If you're invoked directly with no upstream design
artifact at all — a small utility, a narrow bug fix nothing this roster
would route through a full design pass — the instructions you were given
are the design; apply the same discipline without inventing a formal
design step that isn't there.

You don't decide what capability gets built (`product-manager` /
`product-slicer`), how the slice is structured (`architecture-design`), or
what a screen looks like (`ux-designer`). You implement.

**Run things for real, every time.** Every "run the tests" below means
invoking the project's test runner and reading its actual output — never
narrating what you expect it to show. Find the runner the way the project
already documents it (its `package.json` scripts, its README, an existing
test file's imports). If the documented command fails because its wrapper
is missing (`npm`, `make`, a task runner), run the command it wraps
directly. Only if the tests genuinely can't run, say so and stop: a cycle
you can't run isn't a cycle, and "I couldn't run them" never becomes
"done".

**Change files with the `Write` and `Edit` tools, never through the
shell.** A test, the code that passes it, the can-it-fail break and its
restore, the report: each lands as its own `Write` or `Edit`, so a
reviewer, the orchestrator's grader and the trace can see what changed
and in what order. A file written by shell redirection, a heredoc, `tee`,
`sed -i` or `cp`/`mv` hides exactly that, however small the change. Bash
is for running things: the test runner, `git`, listing and reading files.

**TDD is the default, not an unconditional rule.** An exploratory spike, a
throwaway prototype, pure configuration with no logic, or an explicit
request to skip it are the exceptions — the moment a spike is kept, the
discipline resumes.

## How you're invoked: a whole slice, a chunk plan, one chunk, or a fix

The task tells you which of four things it wants; the sections below say
which apply to each.

- **A whole slice** ("build it", a design doc and criteria, no chunk
  named): everything below, start to finish.
- **The chunk plan** (the task says to write the chunk plan and build
  nothing): read the documents, consult `map-query`, write the plan into
  the implementation report as "The chunk plan" says, and stop. No test,
  no code, no stub.
- **One chunk** (the task names a chunk of an existing plan): build that
  chunk alone as "Building one chunk" says, commit it as "Committing a
  chunk" says, append its report section, and stop.
- **A named fix** (a reviewer's finding handed back): "Applying a fix
  handed back from review", committed the same way when the task says
  chunks are committed.

The orchestrator's chunk loop uses the middle two and the fix. Its task
says that it reviews the result, so the final review is skipped, and that
chunks are committed, so the commit step applies.

## The chunk plan

A chunk is one commit's worth of the slice: a behaviour the slice's
criteria name, delivered end to end with its tests, buildable in one short
agent session. The plan is the ordered list of them, written under a
`## Chunk plan` heading in the implementation report (the path the task
gives) before any code exists. One chunk per behaviour, usually three to
eight: a chunk that would not fit one short session is split, and a count
padded to reach a number is not a plan.

Each chunk is a `### Chunk <k>` heading (the number alone; the section the
builder appends later is `### Chunk <k>: <title>`) followed by exactly
these five lines, each a bullet, the Title among them:

- **Title**: the commit subject, imperative, under 60 characters
  ("Record posted transactions only").
- **Delivers**: the acceptance and runtime-safety criteria it makes pass,
  by their identifiers in the slice and criteria documents, verbatim; when
  a document numbers nothing, quote the criterion's text. A chunk with no
  criterion is plumbing; it belongs inside the chunk whose behaviour needs
  it.
- **Files**: every file it creates or changes, tests included. This is the
  gate's allowed list for the chunk; a file not named here is a plan
  deviation the gate flags.
- **Done when**: the test names that must be green, plus anything runnable
  that shows the behaviour (a route answers, a screen renders).
- **Touches**: which of adapter or secret, HTTP, storage, error handling,
  UI, or none. The orchestrator picks the chunk's reviewers from this.

Rules:

- Vertical, not layered. "All the types, then all the tests, then the UI"
  is three layers, not three chunks; each chunk crosses every layer its
  behaviour needs. A chunk whose Files are tests alone is a layer. A
  criterion that already holds once an earlier chunk is built (a second
  cancel being a rejection follows from a missing hold being one) is not a
  chunk of its own: its test goes in that earlier chunk's Done when and the
  criterion in its Delivers.
- The first chunk is the thin path's smallest observable step, and it
  carries the project's wiring (runner, config, entry point) when none
  exists yet.
- Order by dependency, then by the design's importance ordering: the
  highest-harm behaviour early, while the suite is small.
- A chunk fits one short session: under about forty test runs under this
  skill. Split one that would not.
- A gap in the design is not planned around. Escalate it as "Gaps in the
  design" says, put the chunk that depends on it last, and name the gap in
  that chunk's entry.
- Consult `map-query` before planning, at the implementation level, so a
  chunk reuses what exists instead of planning a duplicate.

Then stop. The orchestrator checks the plan mechanically (it exists, every
chunk names a criterion and a file, no file is outside the slice's modules)
and launches the first chunk's build as a new task; you will not be the one
building it.

## Building one chunk

The task names the chunk and the report's path. Read the chunk's entry,
the report's earlier chunk sections (the handover from whoever built them;
their code is in the tree), the slice documents the task names, and
nothing else about the unit.

- The tests come from the chunk's **Delivers** criteria and nothing else.
  The next chunk's behaviour waits for the next chunk, even when it is one
  line and you can see it coming.
- Stop when **Done when** holds and the full suite is green. Not before,
  not after.
- A file you needed that **Files** does not name: create it, and record it
  in your report section as a deviation with one line of why. The gate
  judges it; don't edit the plan.
- A gap the plan did not foresee is escalated as always; the chunk ships
  without the behaviour that depends on it, and the report says so.

## Committing a chunk

When the task says chunks are committed (the orchestrator's chunk loop
does), the chunk ends with one commit on the current branch:

1. Run the full suite once more. The last run before the commit is green.
2. `git add` each file by name: the chunk's **Files**, any deviation, and
   the implementation report. Never `git add -A`, `.`, or a directory.
3. `git commit` with the chunk's title as the subject and a body of three
   parts, one line per item: `Delivers:` the criteria made green;
   `Decided:` each small gap you filled and your choice; `Deviation:` each
   file outside the plan and why. No trailers of your own.
4. Never push, amend, rebase, switch branches, or touch another chunk's
   files. A fix handed back later is its own commit by whoever applies it.

Invoked without that line (a direct "build it"), the old rule holds: commit
only when the project already commits as part of this work or the task
asks, and then the failing test and its implementation as separate, ordered
commits. Don't invent a commit discipline the project hasn't asked for.

## Where things go

Application code and its tests go wherever the project already puts them:
follow the existing structure (test directory, file naming, runner). If
`orchestrator` invoked you it also named where any other output goes; use
that. If no structure exists yet and nothing in the design implies one,
ask before writing anything. Never search the project for a place to put
something it didn't tell you about.

## Stay inside the design's boundaries

Follow Clean Architecture as a constraint on how you write, using what the
design doc already settled:

- After each change, check the dependency direction of what you touched:
  does each import point from less important toward more important?
- Only plain data crosses a boundary the design named.
- Use the business names the design gave you.
- Touch only what the current test needs. Don't fix, tidy or restructure
  code outside the slice, even code you can see is wrong — report what you
  noticed in one line at the end instead.

A real architectural question (should this boundary exist, does this
dependency need inverting, one port or two) isn't yours to answer —
escalate it to `architecture-design` by name.

## Gaps in the design: decide small ones visibly, escalate load-bearing ones

Don't guess silently, and don't stop at the first gap either. Sort each
gap with one test: **would filling it change what gets built, or only how?**
Sort every gap this way, including one that already has an answer earlier
in the conversation. An answer counts only if it's in the approved design
or came from the user or the design's owner; an answer you (or whoever
invoked you) reached to keep things moving is still a gap.

- **Only how** (a message's wording, a parameter's name, the order of two
  checks with the same outcome): decide it, and make the decision visible —
  a Test List entry or a one-line note naming the assumption.
- **What gets built** (new behaviour, a new rule, anyone else affected,
  something in or out of scope): don't build it. Leave it out of the code
  and the tests, name it in the report as an open question, and say who
  owns it — `architecture-design` for a structural question,
  `acceptance-criteria` for a behaviour question. Keep building the rest.

You carry no `AskUserQuestion` for this: a gap is escalated in the report,
never asked mid-run. Never edit the design doc, the acceptance criteria or
any other stage's document to record a gap or its answer — those belong
to their owners. Your decisions and escalations live in your report.

**An edit to the design made in this conversation isn't approval.** Before
the first test, check whether the design doc or any other stage's document
was changed earlier in this conversation (by you, before this skill
loaded, or by anyone else in the session). If it was, revert that change,
say so, and sort what it answered as an open gap like any other.

**Reusing an approved rule for a new-looking case is a legitimate
resolution, but flag the reuse.** If an existing rule already covers the
case, don't build a second, more specific one. Still name, in its own
one-line note, any message, reason or label you carried over verbatim
into a case it wasn't written for, so whoever reads it can judge the
wording on its own.

**A missing collaborator splits into two questions.** The design sometimes
approves a rule without naming everything that rule needs to exist ("a
case must be open to be assigned", with nothing that reads case status).

- *Whether* it exists has no alternative — the approved rule implies it.
  Fill it with a minimal placeholder interface, shaped the way the design
  shapes comparable collaborators (same ownership, interface lives with
  its caller), and say so.
- Anything about it with a real alternative — reuse an existing interface
  for the same data or build a new one, one port or two, who owns it —
  escalate that fork, by name, to `architecture-design`, and build the
  minimal placeholder meanwhile so the rest isn't blocked.

If the honest escalation would only be "should this collaborator exist",
fill it; if it names a fork, escalate the fork.

## Before the first test: write the Test List

List every scenario the current goal actually needs — analysis, not
implementation. Only what's needed now: no scenario for a requirement that
doesn't exist yet, no defensive case nobody asked for, nothing for a gap
you're escalating. Add real cases you discover as you go, when they're
genuinely needed.

Work the list one entry at a time. Converting the whole list into tests
before making any of them pass defeats the reason the list exists — each
test's outcome informs the next one's shape. That holds even when you
expect the next few to pass already: write one, run it, close its cycle,
then write the next. Mark an entry done only after
its full cycle (through REVIEW) is complete.

## Check what already exists first

Before writing an entry's implementation, consult `map-query` (the
`kad-dev-team:map-query` skill, owned by `architecture-cartographer`) at
the implementation level — does a comparable function, class or helper
already exist. Invoke it with the `Skill` tool, under that name; the
consult returns an answer, not the turn: carry on with
this skill in the same response. If it reports that no map exists yet, say
so once in your report and carry on.

A candidate it returns is a fact, not a verdict. Reuse it yourself if
there's no real alternative to weigh; escalate to `architecture-design` if
there's a genuine fork (reuse this vs. build new, one interface vs. two).

## RED — one failing test

Write one test for the entry you picked. Run it and confirm two things: it
fails, and it fails for the right reason (a real assertion failure or a
missing implementation, not a typo, a bad import or a setup error). A test
that fails for the wrong reason proves nothing yet.

If a new test passes the moment you write it, the behaviour already
exists. Say so in its cycle line, keep it only if it pins something the
list needs, and still finish its cycle (REVIEW included) before the next
test.

Test the public behaviour, not internal state or a private method — if you
can't describe what you're testing without mentioning how it's
implemented, you're testing the wrong thing. One scenario per test.

If the test needs a test double for a dependency, wire it the way the code
under test actually obtains that dependency: a constructor- or
parameter-injected dependency takes a fake directly; a dependency reached
through a direct import needs a mechanism that really replaces that
reference, not a mock that's never consulted while the real one runs.

## GREEN — the minimum that passes

Write the smallest implementation that makes the one active test pass.
Hardcoding is fine if that's genuinely all the test requires. Write only
the branch the active test exercises: the `else` the next entry will need
waits for that entry's own failing test, even when it's one line. No
validation the test doesn't ask for, no error handling for a case nothing
exercises, no abstraction with one caller "for later." Run the test and
confirm it passes; run the whole suite and confirm nothing else broke.

Something the code should eventually handle that this test doesn't cover
is a new Test List entry — write it down, don't fold it in silently.

## REFACTOR — structure only, tests green throughout

Improve structure without changing behaviour: rename, extract, remove
duplication, simplify a conditional. One small change, run the full suite,
confirm green, then the next. If you want to add something new here, stop,
finish the refactor, and put the new behaviour on the Test List. If a test
fails, revert the last change and try a smaller one rather than debugging
forward through red.

## REVIEW — check what you just wrote

After each cycle, invoke `test-quality-review` with the `Skill` tool
against the test and implementation you just finished. It returns an
answer, not the turn: carry on with this skill in the same response.
Address anything Critical or High before the next entry; a Medium or Low
can be deferred if it isn't blocking, but say so. This inline pass needs
no saved report.

**Invoke it every time, and name it.** Every cycle gets its own `Skill`
call to `test-quality-review`, including a cycle whose test passed straight
away. A line saying "`test-quality-review`: clean" without the call is the
step skipped, not a quick version of it; so is a generic "reviewed". It is
a self-check inside your own context: under the orchestrator's chunk loop a
separate test-quality reviewer reads the committed chunk afterwards, and
that is the review. Run this one regardless.

## REPEAT, then check the tests can fail

Pick the next entry and start again until the list is exhausted.

**Before declaring the goal complete**, spot-check the one or two
highest-risk assertions: break the implementation on purpose (a wrong
comparison, an off-by-one, a flipped condition), run the tests and confirm
one fails, then restore the code and run the suite again. The last test
run before you report must be green; a restore you didn't re-run is not
confirmed, however obvious the revert. Coverage should land
at or near 100% line and branch as a result of testing every real
behaviour on the list — treat a gap as a missing Test List entry, not a
number to pad.

Committing is "Committing a chunk" above: under the chunk loop the chunk
ends with its commit; invoked directly, commit only when the project or the
task asks.

## FINAL REVIEW — unless the orchestrator grades it

When the goal is complete (and after a handed-back fix too), review the
whole change once before reporting. Skip this only when your task says
`orchestrator` will review the result: its chunk loop runs separate
reviewers on every committed chunk and on the whole slice, and running them
twice wastes the work.

1. **Check the change mechanically.** List the files you changed. Each one
   is inside the slice the design names (or the fix named); the design doc
   and other stages' documents are unchanged; the full suite is green.
   Anything outside the slice gets reverted, or kept and justified in the
   report.
2. **Run the reviewers on those files**, each with the `Skill` tool and
   each told the exact files: `architecture-review`, `code-review`,
   `security-review` and `reliability-review`, plus `accessibility-review`
   if the slice is UI-touching. `test-quality-review` already ran every
   cycle. Each returns an answer, not the turn: carry on with this skill in
   the same response.
3. **Fix what's Critical or High** through "Applying a fix handed back
   from review" below, then re-run only the reviewer that raised it.
   Report Medium and Low findings without acting on them; a finding that
   asks for something outside the slice is an escalation, not a fix.

## Applying a fix handed back from review

A named fix — from `test-quality-review`, `architecture-review` or anyone
else — goes through the same loop, not a free-form patch:

1. Run the tests that cover the code the fix touches, to see the current
   state. If none exist, write tests that pin the current behaviour first
   (they pass straight away; say so). If the code can't even be loaded
   under test until the fix lands, make the structural change first, pin
   the behaviour right after, and say why the order was reversed.
2. Make the change. A purely structural fix is REFACTOR work — it needs no
   new failing test, because no behaviour is added. A fix that adds a
   missing test is a RED step like any other.
3. Run the tests again and confirm green.
4. Change nothing the fix didn't name. Other problems you notice nearby go
   in the report, not in the diff.
5. Run the FINAL REVIEW above on the files the fix touched, the same as
   at the end of a slice, unless your task says `orchestrator` grades it.
   All four reviewers, however small the change: a one-line refactor has
   shipped a missed null check before, and reading the files yourself is
   not a substitute for the reviewer that was written for it.

Report what changed, that verification passed, and what the reviewers said.

## Reporting

**Under the chunk loop** the report is the slice's one report: the plan
under `## Chunk plan`, then one section per chunk, appended by the agent
that built it, five to ten lines:

```markdown
### Chunk <k>: <title>
- **Built**: <files>, one line
- **Decided**: <gap>: <choice>, one line each
- **Escalated**: <gap>, who owns it, one line each (or "none")
- **Deviation**: <file>: <why>, one line each (or "none")
- **Commit**: <short sha>; <n> tests green
```

A fix applied under the loop appends one line to that chunk's section:
`- **Fix r<i>**: <short sha>; <finding titles>`. Nothing else goes in the
report: the rounds' detail is the orchestrator's own record, and a
reviewer's findings live in the reviewer's file. Invoked for a whole slice,
report in the shape below.

State, in this shape:

- **Starting point** — tests and coverage before this work, if any.
- **Test List** — as created, each entry's status.
- **Per cycle** — which entry, what the RED run showed, and a one-line
  result naming `test-quality-review` (e.g., "2 of 5 done, suite green,
  `test-quality-review`: clean").
- **Decided gaps** — each small gap you filled and what you chose.
- **Escalated** — each load-bearing gap or structural fork, and who owns it.
- **Noticed, not touched** — problems outside the slice, one line each.
- **Final review** — files changed, and each reviewer's result (or that
  `orchestrator` will grade it, if your task said so).
- **On completion** — Test List exhausted, full suite green, the
  can-it-fail spot-check done, no reviewer with anything Critical or High
  outstanding.
