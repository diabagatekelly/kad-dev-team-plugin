---
type: llm
criteria: |
  PORTABLE — holds for any screen design output, not just this case's
  fixture.

  Each meaningfully distinct state must reference both a real HTML mockup
  file and a real screenshot file saved under `visual-ux/` — not a prose
  description standing in for a rendering, and not a single combined
  description covering multiple states with only one or zero actual
  rendered files.

  Score 0 if any state named in the output has no corresponding
  referenced HTML+screenshot pair, or if the output describes states in
  prose without referencing actual rendered files for each; 1 if every
  state has both file types referenced.
focus: last_message
---

Grounded in `skills/screen-design/SKILL.md`'s "Produce a rendered
artifact, not production code" section and the Output format's "Layout
and composition" line: "The rendered mockup and its screenshot, both in
`visual-ux/` — one pair per meaningfully distinct state."
