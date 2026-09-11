Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/acceptance-criteria/SKILL.md

**Verdict: Not done.**

**Why:** "Correctly" is doing all the work in this sentence and it isn't defined — there's no concrete starting state and no way to look at the result and say pass/fail without someone's personal judgment call. It also doesn't name what a transaction is being matched against, which is the same vagueness one level removed: "categorizes correctly" is exactly as untestable as "matches correctly" without saying what makes the match.

**Rewrite:**

Given a transaction whose merchant name matches an entry in the user's historical categorization sample, when that transaction is imported, then it is assigned the category recorded for that merchant in the sample — not a generic or inferred category.
