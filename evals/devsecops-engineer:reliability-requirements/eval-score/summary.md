# devsecops-engineer:reliability-requirements — eval summary

**Result: PASS — 5/5 graders passed**

| Grader | Result |
|---|---|
| skill-invoked | PASS |
| catches-partial-data-as-distinct-failure-mode | PASS |
| fails-loudly-on-partial-not-degrades | PASS |
| distinguishes-expected-from-unexpected | PASS |
| observability-driven-by-diagnostic-question | PASS |

## Notes

First run of this case. Graders are grounded directly in `SKILL.md`'s own
text (quoted in each grader's rationale) rather than in
`evals/example/reliability-requirements-001.md`'s specific content — that
document was consulted only for narrative realism when shaping the
fixture, after an explicit correction mid-session not to treat a real
historical artifact as ground truth without checking it against the spec
first.

The fixture's central trap — an engineer's proposal to show partial data
and quietly re-fetch the rest in the background — is the inverse of the
skill's own explicit worked example ("a financial figure computed from
partially-retrieved data should fail loudly... showing it with a quiet
asterisk is worse than showing nothing"). The persona correctly rejected
it, and also wrote a criterion specifically forbidding the *silent
background re-fetch* half of the proposal, not just the *show-partial-data*
half — that second half doesn't appear explicitly in the skill's own
"quiet asterisk" phrasing, so catching it is a genuine additional
application of the same underlying principle (nobody should learn a
problem existed only after the fact), not just a restatement.

One case-authoring gap caught before running: the skill explicitly lists
"choosing to degrade rather than fail on a given path" as a decision
requiring the approval loop, but the fixture's scripted answers didn't
originally cover approving that specific call. Fixed by adding a scripted
answer before running, per the agent-eval procedure's own instruction not
to invent an answer mid-run.
