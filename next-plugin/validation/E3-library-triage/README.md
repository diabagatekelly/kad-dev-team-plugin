# E3: the library used as the owner pictures it

The owner, 2026-11-21, after E2: "In the planning phase, once we have a
slice, we look at all the areas in the library that are relevant to
that slice, and we ask, is this question important for what we are
building in this slice? What is the answer? This would also need to
overlap with deep product research, because some of those answers may
have to come from [what the product depends on]."

So not every question against every thing (E2), but a triage first,
then answers, with any answer that states a fact about a dependency
resting on its documentation or on a test against the real thing.

## Part A: does the triage keep what matters? (this folder, so far)

**Question:** when a fresh agent reads the fourth project's plan and
the library and marks which questions matter for the slice, does it
keep the entries that the slice's real defects were cases of?

**The bar (proposed by the session, in force unless the owner changes
it before the result is read).** E1's judges tied 18 of this slice's
30 defects fully to a library entry and 8 partly. A defect is kept
when the triage marks at least one of its entries as relevant. Three
triages by three fresh agents:

1. Every triage keeps at least 17 of the 18 fully tied defects.
2. Every triage keeps at least 7 of the 8 partly tied.
3. The size is reported: entries kept of 250, and the number of things
   they must be answered for, against E2's 1,172 cells.

If a triage drops what matters, nothing built on it can catch those
defects, and part B is not run on it.

### Part A result (2026-11-21): the bar is met

| Triage | Questions kept of 250 | Things to answer for | Fully tied defects kept | Partly tied kept |
|---|---|---|---|---|
| 1 | 171 | 470 | 18 of 18 | 8 of 8 |
| 2 | 173 | 433 | 18 of 18 | 8 of 8 |
| 3 | 162 | 345 | 18 of 18 | 8 of 8 |

159 questions were kept by all three and 180 by at least one; they
disagree on 21, five of them about a fixed body of content (does the
provider's list of institutions count as one). No triage dropped an
entry a real defect depended on.

What it does and does not show: the triage is told to keep when
unsure, and it keeps about two thirds of the library, so losing
nothing is the easier half. The saving is in the other number: 345 to
470 things to answer for against 1,172 cells when every thing was
crossed with every question (E2), because a kept question is tied only
to the things it applies to.

## Part B: the answers

For each question triage 1 kept (the first, chosen before any was
measured), an answer per thing it applies to. Before any answering, a
research agent writes a dossier: what the public documentation of
everything the slice depends on says, each fact cited, each statement
the plan makes about a dependency marked as agreeing, contradicting or
not covered, and what the documentation leaves open with the test that
would settle it (`dossier-brief.md`). Then fresh agents answer the
cells with the plan and the dossier in front of them
(`answer-brief.md`), giving each answer a kind (a fact about a
dependency, a decision for the owner, a choice for the planner), a tag
as in E2, and a source for anything said about a dependency: a dossier
fact, a quoted page, or "needs a test". `answers.py check` refuses an
answer that leans on a dependency with no source.

**The bar (proposed by the session, in force unless the owner changes
it before the result is read).** V1's matcher unchanged, majority of
three runs, on the fourth project's 30 defects, against 10 named and
24 named or part for the frozen tables, 10 and 20 for E2's grid:

1. Named: at least 10.
2. Named or part: at least 24.
3. At most 600 cells (half of E2's grid).
4. Reported beside them: how many questions would reach the owner, and
   how many answers are marked for a test against the real thing.

## What is here

`triage-brief.md`, `dossier-brief.md` and `answer-brief.md` (what each
agent is told); `triage_check.py` (checks a triage and measures what it
kept) and `answers.py` (builds, checks, renders and counts the
answered cells), neither using a model, with their tests.
The plan, the triages and the judges' runs they are measured against
are in the private audit repository.
