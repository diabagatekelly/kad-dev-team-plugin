---
name: test-quality-review
description: Critique an existing test file's quality — over-mocking, false positives, tests that verify nothing, missing coverage, implementation-detail assertions. Use on demand against any test file, or inline as part of tdd-implementation's own Red-Green-Refactor loop after each cycle.
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

Critical / High / Medium / Low, matching this roster's shared scale (see
`AGENT.md`). Mocking the code under test is always Critical. Excessive
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

**Invoked standalone** — on demand against an existing test file, or as
one of several parallel graders reviewing a finished candidate
implementation — write a findings report:

```markdown
## Test Review: <file>

### Summary
Tests reviewed, issues found by severity, overall assessment (PASS /
NEEDS ATTENTION / CRITICAL ISSUES).

### Findings

## Finding: <short title>

**Location:** file:line or test name
**Category:** which issue category above
**Severity:** Critical | High | Medium | Low

**What's happening:** the current state, concretely — quote the assertion
or mock setup if that's the issue.

**Why it matters:** the real consequence of leaving it — what bug ships
unnoticed, not just which rule it breaks.

**Suggested fix:** a specific, actionable change `tdd-implementation` can
apply — described, not a rewritten test file.

### What's working
Genuinely good patterns worth naming, not padding.
```

List findings most severe first. If nothing rises above Low, say so
plainly rather than padding the report to look thorough.
