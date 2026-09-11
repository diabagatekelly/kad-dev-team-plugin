---
type: llm
criteria: |
  PORTABLE — holds for any design doc, not just this case's fixture.

  The "Decisions" section (or equivalent) must show that real decisions
  were presented to the user for approval and either approved or changed
  by them — not stated as though the persona decided them unilaterally and
  only reported the outcome afterward. Each entry should carry visible
  approval-loop provenance: what was proposed (a recommendation and the
  alternative(s) considered), and what the user approved or changed — not
  just a bare final choice with no trace of how it was reached. Score 0 if
  any decision reads as autonomously settled with no approval trace, or if
  there's no Decisions section at all despite the design containing real
  decisions; 1 if every decision shown carries visible approval-loop
  provenance.
focus: last_message
---

Extracted from the retired `reflects-approved-decisions` grader's general
half. The specific structural checks that grader also ran (does the final
design actually reflect *this fixture's* two approved choices) stay in
`fixture-reflects-approved-decisions` — this version checks only the
narrative shape of the Decisions section, which holds for any design this
skill produces, whatever the decisions actually were.

