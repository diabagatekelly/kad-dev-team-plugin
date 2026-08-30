PASS (llm judge, after fixing a second grader/skill wording gap)

First run on this re-run FAILed a correct output: step 4's line ("based on
the budget-vs-actual picture") was flagged as a "per-step dependency
annotation." On inspection this was a false positive — that phrase
describes what data the step's own decision uses (the same way step 2
says "categorize *retrieved* transactions"), not a build-order/timing
meta-note like "(depends on step 3)." Both `skills/scope-map/SKILL.md` and
this grader had the same latent ambiguity (this is the second time this
exact category of false positive has hit this case — see the first,
different root cause, in this file's git history / the grader's own
comments) — tightened both to distinguish "a step naturally describing
the data/output it works from" from "explicit sequencing/timing
meta-notation bolted onto a step's line." Re-judged the same captured
output against the corrected criteria: passed.
