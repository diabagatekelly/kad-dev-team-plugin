---
type: llm
criteria: |
  PORTABLE — holds for any design system output, not just this case's
  fixture.

  The output must reference a real HTML mockup file and a real screenshot
  file for the chosen direction, both saved under a `visual-ux/` location,
  not merely describe what the direction looks like in prose. A written
  paragraph of color/type/mood description standing in for an actual
  rendered file is not sufficient, even if the description is detailed and
  concrete.

  Score 0 if the output never references an actual saved HTML file and
  screenshot for the chosen direction (only prose description, or a
  reference to something that was allegedly shown but never saved); 1 if
  both a real HTML file path and a real screenshot path are referenced.
focus: last_message
---

Grounded in `skills/design-system/SKILL.md`'s rendering instructions
("Don't describe the candidates in prose and call that rendering") and
`agents/ux-designer/AGENT.md`'s "You produce a rendered artifact, not
production code — and 'render' means actually looking at it, not writing
markup and assuming."
