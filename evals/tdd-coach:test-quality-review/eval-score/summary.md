# tdd-coach:test-quality-review — eval score

**10/10 PASS**, reached across three runs — one case-authoring fix, one
real skill-text fix.

| Grader | Final result |
|---|---|
| skill-invoked | PASS |
| catches-mocking-code-under-test-critical | PASS |
| flags-excessive-mocking | PASS |
| catches-weak-assertion-false-positive | PASS |
| catches-mock-that-doesnt-intercept-anything | PASS |
| catches-missing-coverage-on-formatReceiptLine | PASS |
| catches-revealed-defensive-code | PASS |
| catches-incomplete-guard-edge-cases | PASS |
| no-false-positive-on-stub-spying | PASS |
| severity-and-report-format | PASS |

Dry-run emulation via the `agent-eval` skill (single run per iteration,
not the real CLI's 3-run average — see `evals/README.md`'s known
limitations). This skill needs no real tool use to do its job (static
read of a given test file), so unlike `tdd-implementation` this case has
no Bash-restriction gap.

## The three runs

**Run 1.** 9/10. `catches-mocking-code-under-test-critical` FAILed — the
fixture's intended Critical-tier trap (`vi.spyOn(service, 'applyRounding')`
with no `.mockReturnValue`/`.mockImplementation` chained on) was a bare
passthrough spy, not an actual behavior replacement. The review correctly
called it "tests depending on implementation details" (High), which was
the *right* read of that code — the grader's expectation was wrong, not
the review. **Case-authoring bug**, not a skill defect. Fixed the fixture
to a genuine mocking-the-code-under-test case
(`vi.spyOn(service, 'calculateTotal').mockReturnValue(999)`, asserting
the mock's own configured value).

**Run 2 (after the fixture fix).** 9/10. The intended finding now caught
correctly, but `catches-missing-coverage-on-formatReceiptLine` FAILed —
present on the very first run of this fixture (before the case-authoring
fix), absent on this run. Diagnosed, not dismissed as noise: `SKILL.md`'s
"Missing coverage" category sat as one item in a prose list of things to
notice while judging individual tests — but missing coverage is
structurally different from the other seven categories, since it's about
what's *absent*, not what's present in any one test. Nothing in the skill
forced a systematic cross-check of the implementation's exports against
the test file, so it was vulnerable to losing out to whatever else
grabbed attention that pass — in this run, specifically, an actual bug in
`isValidCustomerId` the model found and spent effort reasoning through.
**Genuine skill-text gap**, confirmed by identifying the mechanism, not
just observing the miss. Fixed by adding an explicit "sweep for missing
coverage first, mechanically, before judging any individual test" step to
`SKILL.md`, ahead of the per-test issue categories.

**Run 3 (final, after the coverage-sweep fix).** **10/10.**
`formatReceiptLine`'s missing coverage caught explicitly this time, and
the sweep generalized past the one gap it was written for — it also
caught a second, previously-unfound gap (`calculateTotal`'s multi-item
summing behavior was never asserted by any test, all of which use
single-item arrays). This is the version shipped in
`skills/test-quality-review/SKILL.md`.
