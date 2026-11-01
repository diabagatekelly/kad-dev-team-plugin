---
name: test-quality-review
description: Critique existing tests — over-mocking, false positives, tests that verify nothing, untested exports and branches, implementation-detail assertions. Use whenever someone asks whether tests are any good ("are these tests actually testing anything?", "review my tests", "can you check this test file?"), and inline in tdd-implementation's loop after each cycle. Reports only; never edits the tests.
---

# Test Quality Review

## Scope

You're reading and judging tests that already exist — a test
`tdd-implementation` just wrote, or any test file someone hands you
directly. You don't write or fix tests here; you produce findings.
Applying a fix is `tdd-implementation`'s job, through its own loop.

Read the test file, then the implementation file(s) it exercises — enough
to understand what's actually being verified. Don't go broader than that;
if you can't answer a question about the relationship between the test and
its subject from those two files, that's a sign of the issue itself
(excessive mocking, wrong boundary), not a reason to keep exploring.

**Sweep for missing coverage first, as its own mechanical step, before
judging any individual test.** Every other category below is something
you notice while reading a test and asking whether it's doing its job.
Missing coverage is different — it's what never shows up at all, so
reading test-by-test won't surface it reliably, especially once a more
interesting per-test finding is competing for the same attention. Before
judging anything else: list every exported function in the implementation
file, and every branch a switch, if/else chain, or parameterized case
table makes explicit, and check each one off against the test file. Any
export or branch with nothing exercising it is a finding on its own,
found by this sweep — not something left to surface incidentally while
reading through the tests for other issues.

## The seam check and the fake inventory

Under the orchestrator's chunk loop (as a lens of the combined chunk
review, and again at the slice review) these two run before the per-test
categories, on the chunk's tests as a set. The report goes to the path
the task names, and what is handed back is the counts by severity and
that path, nothing else: the fixer reads the file, and a finding restated
in the reply is read twice and acted on once.

- **Seam check.** The chunk's tests must include at least one that goes
  through the real composition root with the real adapters and the real
  local store, faking only the external service at its wire boundary
  (HTTP). Read the chunk plan's Done when entry marked `seam "<name>"` and
  find that test: if it is missing, or every test that could be it fakes a
  port of the project's own code, that is a **High** titled "the seam is
  untested", naming the chunk and what the real wiring would need. A
  suite where every test either fakes the feed at the port or exercises
  the adapter alone is exactly how both real runs shipped a bug that lived
  between the two.
- **Fake inventory.** List every test double in the chunk's tests
  (`vi.fn`, `vi.mock`, `jest.mock`, `sinon.*`, `unittest.mock`,
  `Fake*`/`Stub*`/`InMemory*` classes, `stub*` helpers, `new Function`,
  hand-rolled DOM objects) and what each replaces, as a table under `##
  Fake inventory` (double, replaces, verdict) before the findings. Then: a
  fake of the project's own module where the real one can run in the test
  (a local database the suite already uses, a temp-directory store, the
  real use case behind the real route) is **High** ("fake of own code with
  a real local equivalent"); a `new Function` over a script string or a
  hand-rolled DOM harness is **High**, and its fix line points at moving
  the code into a real module the build serves (the Definition of Done's
  "no application code inside string literals"), not at a better harness;
  a fake of the external service at its wire boundary, the clock,
  randomness or a browser-only API is fine and listed as such; a port
  fake of own code kept for a branch the seam test cannot reach is fine
  when the Test List names that branch, and Medium when it is a shared
  default fixture.
- **Padding measures, at the slice review only** (the task says it is the
  whole slice): report the test-to-source non-blank line ratio and the
  share of test files that assert on source text, `package.json` or a
  script's body (a test that reads a source file or manifest and asserts
  on its content). A share over 10% is a **Medium** naming the tests; the
  ratio alone is information. The Definition of Done computes the same
  figures mechanically; yours names which tests to delete or rewrite.

## Issue categories

**Mocking the code under test.** The test mocks or stubs a method on the
very thing it's supposed to be exercising. If the subject under test has
had its own behavior replaced, the test proves nothing about it. This is
the ceiling of severity — a test in this state is not weakened, it's
invalid.

**A mock that doesn't actually intercept anything.** The test double is
wired for a dependency-injection style the code doesn't actually use — for
example, substituting a value that's never read because the code reaches
the real dependency through a direct import instead. The test passes
whether the mocked behavior is right or wrong, because the mock was never
consulted. Distinct from mocking the subject itself: here the target is a
genuine external dependency, just wired incorrectly.

**Excessive mocking.** More than a handful of mocks in one test, mocking
something safe to use directly (a pure utility, a simple in-memory
structure), or a mock setup elaborate enough to mirror the implementation
it's replacing. Ask whether fewer mocks would still let this test do its
job — if the answer is no, that's often a sign the code under test is more
tightly coupled than it needs to be, worth naming even though restructuring
it isn't this review's call to make.

**Tests depending on implementation details.** An assertion on a private
method call, an internal call count, or execution order rather than an
observable outcome. The test for it: would this test break from a
refactor that changed nothing about what the code produces? If yes, it's
testing how, not what.

**Testing through the wrong boundary.** A test for one unit asserts on
what a *dependency* of that unit does internally — a parent component's
test reaching into a child's rendered output, a use case's test asserting
on a repository's internal query shape rather than the use case's own
result. The fix usually isn't more mocking, it's finding the right
boundary: what does *this* unit actually promise, and does the test check
that promise or something one layer deeper?

**Useless tests and false positives.** A test whose assertion is weak
enough to pass regardless of whether the implementation is correct (a
bound check like "greater than zero" where the real requirement is an
exact value), a test that only re-asserts what a mock was told to return,
a test with no real assertion, or a test that exists only to move a
coverage number rather than to specify real behavior. All of these run,
report green, and prove nothing.

**Missing coverage.** An exported function, a branch, or a case in a
parameterized table with zero tests exercising it — including the
unglamorous half of a pair (a function has both an `exists` and a
`notExists` check and only one is tested), and a case an in-code TODO or
comment already flags as a known risk with nothing verifying it.

**Defensive code the tests reveal as unneeded.** A null check for a value
that can't be null, a type guard for a type the caller already guarantees,
error handling for a condition that can't occur given how this code is
actually called. If no test — including a reasonable one that isn't
written yet — could ever hit this path, question whether the code needs
to defend against it at all.

**Incomplete edge-case coverage on a guard or validator.** A function
whose job is to validate or narrow an input is tested against a valid
instance and, at most, one obviously-empty case — but not against every
input *shape* that can actually reach it in practice (wrong type, absent
entirely, the specific malformed shape most likely to crash the guard
rather than fail it cleanly). The gap here isn't line coverage, it's shape
coverage.

## What's not an issue

Configuring a designated test stub or fake that stands in for an external
dependency (spying on it, setting its return value per test) is normal
test infrastructure, not a mocking violation — the subject under test is
still genuinely exercised; only its external dependency is standing in for
the real thing. Only flag stub usage when the stub itself has grown
complex enough to need its own tests, or when assertions target the
stub's internals rather than the outcome it produces.

## Severity

Critical / High / Medium / Low, the scale every reviewer in this roster
uses. Critical is a test that can't fail whatever the code does. High is a
test that can fail but checks the wrong thing or the wrong layer. Medium
is a test that verifies nothing real, or a real gap in what's tested. Low
is style. Mocking the code under test is always Critical. Excessive
mocking, implementation-detail assertions, wrong-boundary tests, and a
mock that doesn't intercept anything are High. Useless tests, false
positives, missing coverage, revealed defensive code, and incomplete
edge-case coverage are Medium unless the gap is on a path with real
consequence (an untested branch that would ship a security or data-loss
bug reads High, not Medium — severity tracks real cost, not just category).
Style and naming are Low.

## Output

**Invoked inline, as part of `tdd-implementation`'s own loop**, after a
single cycle: a short pass/fail plus anything Critical or High that needs
fixing before moving on. No persisted file needed for this — the whole
point is a fast check on the newest thing on the stack, not a standing
archive of every cycle.

**Invoked standalone** — on demand against an existing test file, as a
lens of the chunk loop's combined chunk review, or as one of the six slice
reviewers at its D step — write a findings report as your response. Save it to a
file only when whoever invoked you named one; never search the project for
a place to put it. Read and report only: don't edit the test file or the
code, even for a one-line fix — describe the fix instead.

The report opens with `# Test review: <file or chunk>`, then `## Summary`
(tests reviewed, issues by severity, PASS / NEEDS ATTENTION / CRITICAL
ISSUES), `## Fake inventory` under the chunk loop, `## Findings` in the
shared format, and `## What's working` (genuinely good patterns worth
naming, not padding).

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

This skill's **Location** may be a test name when a line would mislead;
its **Category** is the issue category above (prefixed `test-quality:` in
a combined report); its **What's happening** quotes the assertion or mock
setup when that is the issue; its **Why it matters** names the bug that
ships unnoticed, not the rule broken; its **Suggested fix** is a change
`tdd-implementation` can apply, described, not a rewritten test file.

If nothing rises above Low, say so plainly rather than padding the report
to look thorough.
