---
type: llm
target: phase2
criteria: |
  PORTABLE — holds whenever candidates were generated (the reference path
  never reaches this question at all, since only one mock is ever
  rendered there).

  The second question must present multiple genuinely distinct rendered
  directions and ask the user to pick one — it must not already declare a
  winner, hedge toward one option, or read as a formality after the choice
  was effectively made. Each candidate presented should read as a real,
  fully-committed point of view, not three variations on the same idea.

  Score 0 if this question doesn't actually exist (i.e. a direction got
  asserted without ever pausing for this choice), if it presents fewer
  than two real candidates, or if it's phrased to lead toward one answer;
  1 if it's a genuine, neutral choice among distinct rendered options.
focus: last_message
---

Checks the "stop and ask — with a real question, not a narrated choice"
rule in `skills/design-system/SKILL.md`. Added after a live dogfood run
wrote up a "chosen" direction in the past tense — three candidates were
rendered and screenshotted, but no actual question was ever posed to the
user before one got recorded as selected. The existence of a real
`phase2-question.md` for this case is itself part of what this grader
checks: a run that skips straight to `output.md` with a direction already
picked fails it by construction.
