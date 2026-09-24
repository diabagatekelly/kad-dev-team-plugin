# code-reviewer:code-review — eval summary

**Result: 17/17 PASS, single-phase, four runs.**

| Grader | Result |
|---|---|
| skill-invoked | PASS |
| catches-triplicate-duplication-not-guard-clauses | PASS (after two skill fixes) |
| catches-bad-naming-and-what-comment | PASS |
| flags-misleading-comment-as-critical | PASS |
| preserves-legitimate-why-comment | PASS |
| defers-invasive-species-finding | PASS |
| deprioritizes-pre-existing-untouched-code | PASS |
| treats-two-instance-duplication-as-watch-not-finding | PASS |
| flags-duplicated-type-switch-as-local | PASS |
| flags-primitive-obsession | PASS |
| flags-feature-envy | PASS |
| flags-data-clump-and-long-parameter-list | PASS |
| flags-long-multi-concern-function | PASS |
| does-not-auto-flag-long-uniform-function | PASS |
| rates-actively-wrong-name-worse-than-vague-name | PASS |
| applies-ordinary-checks-to-test-file | PASS |
| does-not-grade-test-mocking-quality | PASS |

## Notes

**Fixture grew in two stages.** The original fixture (`orders.ts` only, 7
graders) covered duplication, naming, comments (WHAT-restatement and a
legitimate WHY-comment), severity calibration on a misleading comment, the
Boy Scout Rule, and the architecture-review boundary. After that first
round passed 6/7 (one fix, see below), the user asked for the skill to be
validated "in its entirety" — a review of the skill text found three
checklist items (primitive obsession, feature envy, data clumps) and
several stated-but-unexercised rules (the 2-instance-not-yet-a-finding
threshold, the size-anchor-as-prompt-not-gate rule in both directions,
wrong-name-vs-vague-name severity, test-file scope in both directions,
local-vs-handed-off duplication in both directions) with no grader at all.
Added two more files to the fixture (`pricing.ts`, `pricing.test.ts`, 10
more graders) to close every one of those gaps. Deliberately did not add a
`product-slicer`-handoff fixture — no realistic code-only trigger for
"should this capability exist" was found that wasn't just relabeled
dead-code or premature-abstraction, both already covered elsewhere.

**Four runs total, one real skill gap, caught and fixed twice.**
1. First run (small fixture): 6/7 graders passed self-checked;
   `catches-triplicate-duplication-not-guard-clauses` sent to an
   independent judge, which returned FAIL — the duplication finding's own
   description folded the exempt guard clause into "what's identical."
   Fixed in `skills/code-review/SKILL.md` with an abstract instruction not
   to do that.
2. Second run (small fixture, post-fix): re-emulated, all six `llm`
   graders independently re-judged — 6/6 PASS, confirming the fix on the
   original fixture.
3. Third run (expanded fixture, all three files, first time run against
   the full 16-grader set): 15/16 substantive graders PASS, but
   `catches-triplicate-duplication-not-guard-clauses` FAILed again — the
   busier, larger task caused the same fold-the-guard-clause-in phrasing
   to recur ("same shape — null guard, weight-based cost... then a
   domestic/international flat add-on"). Confirmed as a genuinely
   recurring gap, not a fluke — the first fix's abstract wording wasn't
   robust enough. Strengthened with a concrete before/after phrasing
   template (what not to write, what to write instead, how to mention the
   exempt part if at all).
4. Fourth run (expanded fixture, post-second-fix): re-emulated from
   scratch, all 16 `llm` graders independently re-judged in four batches
   of four (each judge grading multiple criteria independently against
   the same output, to keep repeated large-fixture text out of 16 separate
   calls without ever self-grading) — 16/16 PASS, including the
   twice-failed one, now explicitly excluding the guard clause by name.
   This run also self-reported the "Skills consulted" line correctly (an
   earlier intermediate run had dropped it — a one-off mechanical miss,
   not reproduced here). This is the canonical `eval-result/output.md`.

**Bonus findings beyond what any grader required**, worth noting since
they show the skill generalizing rather than just pattern-matching the
fixture: a real unit/dedup inconsistency inside `reconcileNightlyLedger`
(two of its outputs silently use different arrays and units), `process`
shadowing Node's global `process` (an earlier run), and a cross-file
consistency observation (money values in `orders.ts` lack the `*Cents`
suffix convention `pricing.ts` establishes in the same PR).

Background: true (neither skill blocks on `AskUserQuestion`) — ran via the
spawned-agent path, not inline.
