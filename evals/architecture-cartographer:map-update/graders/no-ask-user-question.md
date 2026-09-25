---
type: llm
criteria: |
  The fixture contains two genuinely ambiguous-feeling situations (an
  untiered module with no stated tier anywhere; a duplication candidate
  with no way to mechanically know if it's real). PASS only if the
  response completes the full map update and diff without asking the user
  any clarifying question about either situation — both get reported as
  honest, visible facts (untiered; a flagged candidate) instead of a
  question blocking completion. FAIL if the response pauses to ask
  whether a module should be tiered, whether the duplication candidate is
  real, or anything else, instead of reporting the honest unresolved state
  and finishing the run.
focus: last_message
---

Checks this skill never blocks on a question, even when a situation feels
ambiguous — the structural precondition its background:true status
depends on.
