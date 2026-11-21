# E2: a grid built from the library, scored like for like

E1 showed the library holds the question behind many of our defects.
That is a ceiling. This step measures the thing itself: a grid for one
real plan, its rows and columns chosen by a script, filled in by a
model, and scored by V1's judge exactly as the tables of 2026-11-19
were.

**Question:** on the fourth project's slice 1 (30 defects), does a
library-built grid name at least as many defects as the tables the
frozen method built, and at what size?

## The bar (proposed by the session, in force unless the owner changes it before the result is read)

By V1's matcher, majority of three runs, against the frozen tables'
10 named and 24 named or part of 30:

1. Named (N or D): at least 10.
2. Named or part: at least 24.
3. The size is reported beside them (cells in all, and cells tagged
   PLAN SILENT or CONTRADICTS DOCS, which are what a person would have
   to read): the frozen tables had 675 cells.

One plan and one filling: a difference of two or three defects either
way is within what one run can show, and is read as "about the same".

## What is run

1. **The slice's actions:** one fresh agent, given `actions-brief.md`
   and the plan at the commit both builds started from (the
   orchestrator's log removed, no code, no web), lists what the slice
   does under the library's 21 kinds of action.
2. **The grid:** `grid.py make` crosses each listed thing with every
   library entry of its kind. No model.
3. **The filling:** `grid.py split` cuts the grid into parts; one fresh
   agent per part, given `fill-brief.md`, the plan and its cells, tags
   each cell and says what would go wrong there. It may read the public
   documentation of what the plan depends on, as the frozen method's
   builder did. `grid.py check` refuses a filling that adds, drops or
   alters a cell.
4. **The score:** `grid.py render` writes the filled grid as tables;
   V1's matcher (its prompt unchanged, same hash) runs three times
   against the 30 scenarios; V1's `agreement.py` counts.

No agent in steps 1 to 3 sees a defect, a cold read or the earlier
tables. The plan, the filled grid and the matcher's runs quote the
project and stay in the private audit repository, folder
`e2-library-grid/`.
