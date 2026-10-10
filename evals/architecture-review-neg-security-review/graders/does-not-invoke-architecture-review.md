---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?architecture-review"'
min: 0
max: 0
arm: both
---

This is a security-vulnerability request (signature bypass, algorithm
confusion, missing expiry) — `devsecops-engineer:security-review`'s
territory, not `architecture-review`'s. Primary, only scored check for
this case: `architecture-review` must not fire in either arm.
