---
type: llm
criteria: |
  For each category the output treats as forced, it must present a
  recommendation with reasoning and the alternative(s) considered and
  rejected, and leave the decision with the user — rather than announcing a
  settled stack. A confident recommendation is fine and expected; presenting
  it as already decided is not.

  It must also scale to the situation established by the scripted answers —
  a solo maintainer who doesn't want much tooling. Score 0 if it recommends
  team-scale tooling weight with no acknowledgement of that, or never
  establishes who is building and maintaining this at all.

  Score 1 if every forced category carries a recommendation plus rejected
  alternatives, and the decision is visibly the user's.
focus: last_message
---

Tests "Recommend, don't decide," which is the ownership stance this skill was
built around: technology choices belong to the user, and the skill's job is
to make each easy to decide well. The strong-recommendation-is-still-a-question
rule is the subtle half — a test runner choice is usually obvious, and
obviousness is exactly when the loop gets skipped.
