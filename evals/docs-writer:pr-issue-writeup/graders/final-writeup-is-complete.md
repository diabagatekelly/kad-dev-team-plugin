---
type: llm
criteria: |
  This grades the FINAL output, after the agent received the answer to its
  clarifying question (file it, use GitHub). It must be an actual finished
  write-up — plain-language description of the work, in GitHub-appropriate
  format since that's what was specified — not another question, and not
  hedging on whether/where to file anymore. It should not fabricate GitHub
  specifics it can't know (e.g. a real issue number, an assignee) — a
  title + description is enough; a placeholder reference line for the
  eventual issue ID is fine. FAIL if it's still a question, ignores the
  answer, or fabricates unearned specifics.
focus: last_message
---

Regression test for the ask-then-continue gap: the persona should actually
finish the write-up once it has the answer it asked for, not just
demonstrate that it knows how to ask.
