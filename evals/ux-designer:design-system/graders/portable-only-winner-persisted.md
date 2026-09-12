---
type: llm
criteria: |
  PORTABLE — holds whenever more than one candidate direction was
  rendered (not applicable when the direction came from a reference and
  only one mock was ever made — score this N/A-as-pass in that case).

  When a "Candidates considered" section exists, each rejected candidate
  must be described in prose with a concrete reason it lost, but must NOT
  claim or link a saved HTML file or screenshot for itself — only the
  chosen direction's screenshot should be referenced as actually persisted
  in `visual-ux/`. A rejected candidate having its own saved, linked
  screenshot file is a fail even though it doesn't affect the direction
  ultimately chosen.

  Score 0 if any rejected candidate has its own saved HTML/screenshot file
  referenced in the output or evidently present in `visual-ux/`; 1 if only
  the winning direction's files are referenced/persisted and rejected ones
  are prose-only.
focus: last_message
---

Grounded in `skills/design-system/SKILL.md`'s "Only once they've chosen,
create `visual-ux/` and populate it with the winner alone" instruction.
Added after a live dogfood run saved all three rendered candidates'
HTML and screenshots permanently before any question was even asked — the
user's explicit correction was that comparison should happen live, and
only the chosen candidate's files should persist.
