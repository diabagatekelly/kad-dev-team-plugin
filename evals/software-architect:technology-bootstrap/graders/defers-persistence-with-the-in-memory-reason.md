---
type: llm
criteria: |
  The design names a persistence boundary, and slice 1 explicitly states its
  transactions need only last for the current session. The output must
  therefore treat storage technology as NOT forced by this slice, and must
  give the reason: an in-memory implementation behind the strategic-owned
  persistence interface satisfies every test slice 1 has, so the technology
  choice can wait until data must outlive a restart.

  Score 0 if the output: chooses a database or asks the user to choose one;
  treats the existence of a persistence boundary as itself forcing a storage
  technology; or defers it with no reason given. Score 1 if it defers with
  the in-memory reasoning (or clearly equivalent), and identifies who owns
  the decision when it does arrive.
focus: last_message
---

Tests the skill's "Why persistence usually isn't forced" section, which
exists to correct the most common misreading: that naming a boundary in a
design means a database must be chosen. It doesn't — the boundary is what
makes deferring free, and that is the payoff the architecture was for.

The fixture is built so the right answer is unambiguous: the slice says in
so many words that nothing needs to survive a restart.
