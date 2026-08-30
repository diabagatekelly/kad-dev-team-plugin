---
type: llm
criteria: |
  Check each individual step's own line in the Steps section (not the
  Sequencing notes section, which is explicitly allowed to explain overall
  step order per the scope-map template). No step's line may contain
  acceptance criteria, Given/When/Then, a thin path, or a per-step
  dependency/estimate annotation. A step's one-liner may restate a
  constraint already present in the source problem doc (e.g. "a read-only
  connection," "seeded from the historical sample") without that counting
  as a violation — that's carried-forward context, not new design. It IS a
  violation if a step names an actual technology, vendor, or implementation
  approach that was not already stated in the problem doc. Score 0 if any
  step's line crosses into slicing, AC, or new (not-already-stated) design;
  1 if every step stays at name-plus-one-line and any ordering rationale
  lives only in a separate Sequencing notes section, not inline per step.
focus: last_message
---

Scope maps chunk the problem, they don't slice or design any step — this is
the skill's own core rule under test, mirroring the never-design boundary
`problem-framing-doc` holds for the problem itself. Narrowed after the first
run of this case flagged a false positive: the template's own "Sequencing
notes" section legitimately explains overall step order, and a one-liner
restating a constraint the problem doc already stated isn't new design —
see `evals/README.md` for the root-cause note.
