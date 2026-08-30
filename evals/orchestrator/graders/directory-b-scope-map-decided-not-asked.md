---
type: llm
criteria: |
  For Directory B (only a problem framing doc exists), the output must
  route to docs-writer to decide — per scope-map's own trigger criteria,
  by reading the problem doc's content — whether this problem needs a
  scope map or is small enough to treat as one unit. It must NOT ask the
  user directly "small enough to slice, or does this need a scope map?"
  as an orchestrator-level blocking question — that decision belongs to
  docs-writer's own judgment, not a default ask. Score 0 if the output
  poses that question to the user itself as the next action; 1 if it
  routes to docs-writer to decide and does not itself ask that question.
focus: last_message
---

Tests a deliberate reversal from an earlier version of this routing table:
scope-map-or-not is inferable from the problem doc's own content (same
judgment scope-map's own "skip for small problems" text already asks the
persona to make), so it's the persona's call, not a blanket orchestrator
question. Regressing to "ask the user" here would be reintroducing a fixed
bug, not a stylistic choice.
