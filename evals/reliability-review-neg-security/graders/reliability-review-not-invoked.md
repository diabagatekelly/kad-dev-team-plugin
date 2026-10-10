---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?reliability-review"'
min: 0
max: 0
arm: both
---

This is a security request (authorization on a lookup by caller-supplied
id, personal data in logs and responses) — `security-review`'s territory,
not `reliability-review`'s. Primary, only scored check for this case: no
`reliability-review` skill fires in either arm.
