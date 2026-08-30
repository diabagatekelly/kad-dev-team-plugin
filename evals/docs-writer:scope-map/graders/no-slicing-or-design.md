---
type: llm
criteria: |
  Check each individual step's own line in the Steps section (not the
  Sequencing notes section, which is explicitly allowed to explain overall
  step order per the scope-map template). No step's line may contain
  acceptance criteria, Given/When/Then, a thin path, or explicit
  build-order/timing meta-notation bolted onto the line (e.g. "(depends on
  step 2)," "(3 days)"). A step's one-liner may restate a constraint
  already present in the source problem doc (e.g. "a read-only
  connection," "seeded from the historical sample"), and may naturally
  describe what data or output it works from — including data an earlier
  step produces (e.g. "categorize retrieved transactions," "based on the
  budget-vs-actual picture") — without either counting as a violation:
  that's ordinary content describing what the step covers, not new design
  or a dependency footnote. It IS a violation if a step names an actual
  technology, vendor, or implementation approach that was not already
  stated in the problem doc, or bolts on explicit sequencing/timing
  meta-notation. Score 0 if any step's line crosses into slicing, AC, new
  (not-already-stated) design, or explicit order/timing meta-notation; 1
  if every step stays at name-plus-one-line content and any *overall*
  ordering rationale lives only in a separate Sequencing notes section.
focus: last_message
---

Scope maps chunk the problem, they don't slice or design any step — this is
the skill's own core rule under test, mirroring the never-design boundary
`problem-framing-doc` holds for the problem itself. Narrowed twice after
false positives on re-runs: first, the template's own "Sequencing notes"
section legitimately explains overall step order, and restating a
constraint the problem doc already stated isn't new design; second, a
step naturally describing the data/output it works from (even when that
data comes from an earlier step) isn't a "dependency annotation" — only
explicit build-order/timing meta-notes bolted onto a step's line are. See
each case's `eval-score/no-slicing-or-design.md` for the specific
root-cause each time.
