---
type: llm
criteria: |
  PORTABLE — holds whenever a slice's acceptance criteria already name its
  states, density precedent exists in the design system, and its
  acceptance criteria are silent on any extra interaction.

  The skill must proceed directly to producing the screen design without
  asking the user which states to show, how dense the screen should be, or
  what interactions to include, when the acceptance criteria and existing
  design system already answer all of these. Asking about something the
  given artifacts already resolve — just to look thorough — is itself a
  failure, not a safe default.

  Score 0 if the response asks the user any question about state coverage,
  density, or interaction scope that the acceptance criteria already
  settle; 1 if it proceeds straight to the design, resolving those from
  the artifacts as given.
focus: last_message
---

Grounded in `skills/screen-design/SKILL.md`'s "Resolve from what's already
decided before asking" section: "Don't manufacture a question about
something the artifacts already answered just to look thorough." This is
the mirror image of every other persona's "asks before deciding" grader —
here the correct behavior is silence, because a live dogfood run raising
the question "why didn't it ask me anything?" turned out to have a
legitimate answer (everything actually was resolvable), which this grader
makes an explicit, checked expectation rather than an assumption.
