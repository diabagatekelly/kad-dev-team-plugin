---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?security-review"'
min: 0
max: 0
arm: both
---

This is a reliability request (slow or failing provider, retries,
detecting failure) — `reliability-review`'s territory, not
`security-review`'s. Primary, only scored check for this case: no
`security-review` skill fires in either arm.
