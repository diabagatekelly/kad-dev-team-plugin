---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?reliability-review"'
min: 0
max: 0
arm: both
---

This is an architecture request (business logic depending on the ORM and a
payment SDK) — `architecture-review`'s territory, not
`reliability-review`'s, even though the snippet has a reliability problem
too. Primary, only scored check for this case: no `reliability-review`
skill fires in either arm.
