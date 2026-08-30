Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/acceptance-criteria/SKILL.md

**Verdict: not done.** "The app categorizes transactions correctly" is untestable — "correctly" names no concrete precondition or verifiable outcome. Two people could disagree about whether a given categorization counts as "correct" with no way to settle it by looking at the system.

**Rewrite:**
Given a transaction with the same merchant name as one in the provided sample data,
When it's imported,
Then it is assigned that sample's category automatically.
