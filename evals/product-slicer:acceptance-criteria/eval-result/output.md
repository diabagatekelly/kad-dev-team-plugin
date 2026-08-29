Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/acceptance-criteria/SKILL.md

**Verdict: Rejected.**

**Why:** "Categorizes transactions correctly" is exactly the vague-language failure this criterion type is supposed to catch — "correctly" is doing all the work and isn't testable. There's no concrete starting state, no single action, and no observable outcome two reviewers could check without arguing about what "correct" means. It also only implies a happy path; there's no signal for what should happen when no match exists.

**Fixed rewrite:**

> Given a transaction with the same merchant name as one in the provided sample data, when it's imported, then it is assigned that sample's category automatically.

**Gap this exposes (not resolved here):** The rewrite only covers the case where a matching merchant exists in the sample data. What happens when there's no match is undecided and needs its own criterion — this isn't mine to fold in silently. Concrete options for whoever owns this behavior:

- Leave the transaction uncategorized (e.g., category field empty/null) and surface it as needing manual categorization.
- Assign a default/fallback category (e.g., "Uncategorized") explicitly.

Either is a reasonable product call, but the AC set isn't done until one is picked and written as its own Given/When/Then.
