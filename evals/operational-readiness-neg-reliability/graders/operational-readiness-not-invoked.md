---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?operational-readiness"'
min: 0
max: 0
arm: both
---

This is a reliability question about one piece of application code, not about
shipping or operating the service — `operational-readiness` must not fire
in either arm.
