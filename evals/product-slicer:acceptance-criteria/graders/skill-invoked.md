---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?acceptance-criteria"'
---

Verifies the `acceptance-criteria` skill gets invoked on its own, without
requiring a slice-cutting trigger first — this is the standalone-use case
the skill was split out to support.
