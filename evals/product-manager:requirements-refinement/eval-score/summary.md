> **STALE — do not cite this score.** This case now has 6 graders and its prompt now supplies the problem doc's Constraints; the run below covered 5 graders against a prompt with no problem doc. The result below predates that change and is kept only as history. Re-run required.

# product-manager:requirements-refinement — 5/5 PASS

Overall: **PASS**

| Grader | Type | Target | Result |
|---|---|---|---|
| has-required-sections | regex | output | PASS |
| skill-invoked | tool_used | output | PASS |
| asks-before-deciding | llm | phase1 | PASS |
| captures-priority-reasoning | llm | output | PASS |
| no-thin-path-or-ac | llm | output | PASS |

Re-run after this session added the **Constraints in force** pass and
template section — every problem-doc constraint either binds this unit (say
what it *forces*) or doesn't (say why). No regression.

Worth recording about this run: the case supplies a scope map but **no
problem framing doc**, so there were no Constraints to reconcile against.
The persona did not invent any. It wrote the section, stated the pass could
not be completed, named the three constraint categories it knew were
outstanding, and marked the doc not yet safe to slice against. That is the
intended failure mode for the new rule — a constraint that silently doesn't
appear is indistinguishable from one nobody read.

**Case-authoring gap this exposes:** `prompt.md` should carry the problem
doc's Constraints section so the new pass has something real to reconcile.
Until it does, this case cannot positively test the behavior it was just
changed to add — only that the persona refuses to fake it.
