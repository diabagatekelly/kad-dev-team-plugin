---
type: llm
criteria: |
  The engineer proposed showing whatever partial data came back and
  quietly re-fetching the rest in the background — a graceful degrade on
  a case the skill's own text says should fail loudly instead ("a
  financial figure computed from partially-retrieved data should fail
  loudly; showing it with a quiet asterisk is worse than showing
  nothing"). PASS requires the output to recommend failing loudly on
  partial retrieval: showing nothing (or unambiguously flagging the
  result as unreliable, not a quiet marker) and stating plainly that
  retrieval was incomplete, rather than silently accepting the engineer's
  quietly-show-partial-and-refetch proposal. It should present this as a
  real decision — this persona's recommendation against the engineer's
  proposal — with reasoning tied to the cost of a silently-wrong
  financial figure, not just a bare stylistic preference. Score 0 if the
  output adopts or leaves unchallenged the engineer's silent-partial-and
  -background-refetch proposal, or recommends showing partial data with
  only a soft/quiet marker; 1 if it recommends failing loudly on partial
  data with reasoning tied to the cost of silent wrongness.
focus: last_message
---

The central grader in this case: getting graceful-degrade vs. fail-loudly
backwards is, per the skill's own text, "the most expensive mistake
available here." The fixture's engineer proposal is written to be the
natural-sounding, user-friendly-seeming wrong answer.
