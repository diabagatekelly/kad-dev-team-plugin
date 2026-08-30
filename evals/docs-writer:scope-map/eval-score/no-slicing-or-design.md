PASS (llm judge, after fixing a grader-wording bug — see below)

First run FAILed on the original grader wording, which flagged two things
as violations that turn out to be correct persona behavior, not bugs:

1. The output's "Sequencing notes" section explained why the four steps are
   ordered as they are. The original criteria said "no sequencing
   dependencies" without distinguishing per-step dependency annotations
   (disallowed) from the template's own dedicated "Sequencing notes"
   section (explicitly sanctioned for exactly this content). `skills/scope-map/SKILL.md`
   itself had the same ambiguity — fixed there too, not just in the grader.
2. Step one-liners restated constraints already stated in the source
   problem doc ("a read-only connection," "seeded from the historical
   sample") rather than inventing new design. The original criteria didn't
   distinguish "restates an existing constraint" from "invents a new
   design/technology choice" — only the latter is a real violation.

Both the grader (`graders/no-slicing-or-design.md`) and the skill
(`skills/scope-map/SKILL.md`) were tightened to make this distinction
explicit. Re-judged against the same captured output (no persona re-run
needed — the output was never actually wrong): judge confirmed every step
stays at name-plus-one-line, restated constraints don't count as new
design, and ordering rationale lives only in the separate Sequencing notes
section.
