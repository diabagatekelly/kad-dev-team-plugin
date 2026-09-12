---
type: llm
criteria: |
  PORTABLE — holds for any screen design output, not just this case's
  fixture.

  Interface copy shown in the mockups/interaction flow must follow the
  skill's specific content rules: calls to action name the specific
  outcome verb-first (not "OK"/"Continue"); any error state says what
  happened and what to do next, without blaming the user; the empty state
  explains what belongs there and how to fill it (never just "No
  results" / "Nothing here"); confirmations, if any, name the action that
  succeeded in past tense.

  Score 0 if the empty state is a bare "no results"-style message with no
  explanation of how to fill it, if a call-to-action label is generic
  ("OK", "Submit", "Continue") where a specific verb was available, or if
  an error/unreachable-title state doesn't say what to do next; 1 if the
  shown copy follows these rules.
focus: last_message
---

Grounded in `skills/screen-design/SKILL.md`'s "Get the copy right too"
section — specifically the empty-state rule ("explain what belongs here,
why it's empty right now, and how to fill it — never just 'No results'")
and the calls-to-action rule ("name the specific outcome, verb first").
