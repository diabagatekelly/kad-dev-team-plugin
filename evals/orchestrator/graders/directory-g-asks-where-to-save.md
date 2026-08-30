---
type: llm
criteria: |
  For Directory G (invoked with no artifacts directory parameter), the
  output must recognize this is orchestrator's step 1 "not given one"
  branch and say it would ask the user where this problem's artifacts
  already exist or should be created (a directory/location question)
  BEFORE routing to any persona or skill. It must not silently invent a
  save location, must not search the project for one instead of asking,
  and must not skip the question just because a problem statement was
  given. Score 0 if it picks/invents a location or routes onward without
  asking; 1 if it correctly asks before anything else.
focus: last_message
---

Tests orchestrator's step 1 "not given a parameter" branch — unaffected by
this round's routing-table changes, kept as regression coverage.
