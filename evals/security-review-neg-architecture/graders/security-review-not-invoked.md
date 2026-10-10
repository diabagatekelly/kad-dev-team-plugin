---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?security-review"'
min: 0
max: 0
arm: both
---

This is an architecture request (ORM inside a use case, dependency
direction) — `architecture-review`'s territory, not `security-review`'s.
Primary, only scored check for this case: no `security-review` skill
(the plugin's or any other) fires in either arm.
