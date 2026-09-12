---
type: llm
target: phase1
criteria: |
  PORTABLE — holds whenever a first design system is being established
  and no direction has already been stated.

  Before rendering anything, the skill must ask whether the user has a
  concrete reference to work from (a screenshot, an existing product, a
  named comparison) or wants candidate directions generated for them to
  choose between — these are different mechanisms (extract-and-match vs.
  invent-and-compare) and the skill must not guess which one is wanted.

  Score 0 if the first question asked is anything else (e.g. it skips
  straight to naming a direction, or asks a narrower question like "what
  colors do you like" without first checking whether a reference exists at
  all), or if no question is asked before a direction gets asserted; 1 if
  the reference-vs-generate fork is what's actually asked first.
focus: last_message
---

Regression test for the "Establishing a design system starts with asking
how, not with generating" principle in `agents/ux-designer/AGENT.md` and
the matching lead-in of `skills/design-system/SKILL.md`'s "Commit to an
intentional direction" section. Added when that branch was introduced —
before it, the skill only ever generated candidates unprompted, with no
path for a user who already has a concrete look in mind to hand it over
directly.
