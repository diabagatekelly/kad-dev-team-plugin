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

## Part B: the answers (not yet run)

For each question kept, an answer per thing it applies to, each answer
one of three kinds: a fact about a dependency (cited, or marked for a
test against the real thing), a decision for the owner, or a choice
the planner makes and records. Scored by V1's matcher as E2 was.

## What is here

`triage-brief.md` (what a triage agent is told), `triage_check.py`
(checks a triage and measures what it kept; no model) and its tests.
The plan, the triages and the judges' runs they are measured against
are in the private audit repository.
