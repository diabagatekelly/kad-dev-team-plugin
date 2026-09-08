> **STALE — do not cite this score.** This case now has 6 graders and 3 scenarios; the run below covered 4 graders across 2 scenarios. The result below predates that change and is kept only as history. Re-run required.

# product-slicer:vertical-slicing — 4/4 PASS

Overall: **PASS**

| Grader | Type | Target | Result |
|---|---|---|---|
| skill-invoked | tool_used | output | PASS |
| scenario-a-asks-how-not-what | llm | phase1 | PASS |
| scenario-a-final-slice-is-complete | llm | output | PASS |
| scenario-b-declines-without-requirements | llm | phase1 | PASS |

Re-run after this session added two things to `vertical-slicing`: **name the
whole slice set, specify only the first**, and **a ranked procedure for when
a later stage forces a scope change** (new slice ahead > narrow > grow last).
No regression on any existing grader.

**Coverage gap, not a failure:** neither addition is actually tested here.
The slice set appears in the output and the judge was instructed not to
mistake it for scope creep, but no grader checks that it is present,
provisional, or one line per entry. Nothing exercises the scope-change
procedure at all — that needs a third scenario where a downstream persona
hands back a finding, and the correct answer is a new slice ahead of this
one rather than growing it. That scenario is the one this session's
dogfooding actually failed, so it is the highest-value case to add.
