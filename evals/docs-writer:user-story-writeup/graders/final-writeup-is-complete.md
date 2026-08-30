---
type: llm
criteria: |
  This grades the FINAL output, after the agent received the answer to its
  clarifying question (file it, use GitHub). It must be an actual finished
  write-up, written as a user story (who benefits, what they can do once
  this ships, why) pulled from the slice's own thin path and AC — not a
  PR description narrating a change that already happened, and not another
  question or hedging on whether/where to file. It should not fabricate
  GitHub specifics it can't know (e.g. a real issue number, an assignee) —
  a title + description is enough; a placeholder reference line for the
  eventual issue ID is fine. FAIL if it's still a question, ignores the
  answer, reads like a PR description of completed work, or fabricates
  unearned specifics.
focus: last_message
---

Regression test for the ask-then-continue gap: the persona should actually
finish the write-up once it has the answer it asked for, not just
demonstrate that it knows how to ask. Also checks the user-story framing
specifically, since this skill was split out of the old pr-issue-writeup
precisely because a not-yet-built work item needed different framing than
a completed-change PR description.
