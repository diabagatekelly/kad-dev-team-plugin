---
type: llm
criteria: |
  PORTABLE — holds whenever an upstream artifact (the slice's own
  acceptance criteria, in particular) names something as still genuinely
  unresolved, most commonly an unfilled accessibility-criteria placeholder
  left open because `accessibility-engineer` doesn't exist in this roster
  yet.

  This skill doesn't have to resolve that item, but it must not make it
  disappear either: the output's "Open questions" section must carry it
  forward, naming what it is and who resolves it next (or that no owner
  exists yet), rather than reporting "none left open" or omitting it
  silently.

  Score 0 if an upstream artifact names a still-open item (e.g. the
  acceptance criteria's unfilled accessibility placeholder) and the output
  either says nothing is open or otherwise fails to carry that specific
  item forward; 1 if every genuinely unresolved upstream item is still
  visible in this output's own "Open questions."
focus: last_message
---

Grounded in the new carry-forward paragraph in `skills/screen-design/SKILL.md`'s
"What this decides, and what it doesn't" section: "this skill doesn't
close it by designing well, and doesn't get to make it disappear either
... silently dropping it because this document didn't need to touch it is
a regression, not tidiness." Added after auditing a real dogfood run of
`evals/example/screen-design-001.md`: an earlier run of the same slice
correctly carried the slice's unfilled accessibility placeholder into its
own Open Questions, but a later run reported "None left open by this
screen design" — the exact silent-drop this grader exists to catch.
