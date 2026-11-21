# E3 result (2026-11-21): triage, research, then answers names as many defects as either grid, at the smallest size, and reaches the defects that came from wrong beliefs about a dependency

Part A (the triage keeps what matters) is in `README.md`: met in all
three runs. This is part B, on the fourth project's slice 1, 30
defects, V1's matcher unchanged, the majority of three runs.

| | Frozen tables | E2: library crossed with everything | **E3: triage, dossier, answers** |
|---|---|---|---|
| Named (N or D) | 10 | 10 | **10** |
| Part (P) | 14 | 10 | 12 |
| Named or part | 24 | 20 | **22** |
| Decided wrongly (W) | 3 | 5 | 5 |
| Not named (X) | 3 | 5 | 3 |
| Cells | 675 | 1,172 | **470** |
| Cells left open (silent or contradicting) | about 255 | 443 | 277 |
| Cells "cannot happen" | not counted | 388 | 9 |
| Cells where the plan contradicts the documentation | 27 mentions | 6 | 40 |
| Named, run by run | 10, 10, 10 | 11, 10, 12 | 10, 9, 13 |
| Runs agree on named or not | 28 of 30 | 27 | 24 |

| Line of the bar | Bar | Result | |
|---|---|---|---|
| Named | at least 10 | 10 | met, with nothing to spare |
| Named or part | at least 24 | 22 | **not met**, by two |
| Cells | at most 600 | 470 | met |

Of the 277 open cells, 192 are a choice the planner makes and records,
61 a fact about a dependency, and 24 a decision for the owner: 20
distinct questions. 29 answers are marked for a test against the real
thing, the documentation being silent.

## What it says

**On the count it is level with both grids, at 70% of the frozen
tables' size and 40% of E2's.** Two defects short on "named or part" is
inside what one run can show (the three matcher runs alone range from 9
to 13 named), so the honest reading is "about the same number, for
less".

**It names different defects, and the ones that mattered.** The three
defects the frozen tables could only record as decisions the plan made
wrongly are, here, flagged before the build:

- the one-minute give-up against a first pull that the provider says
  "may take 2 minutes or more": named;
- the saved access lost after the provider has already created the
  connection: named;
- a second connect for an institution already connected, refused only
  at the end: the plan's own decision named as sound and missed.

The dossier marked 14 of the plan's 101 statements about its
dependencies as contradicting their documentation, among them the free
limit that removal does not give back and "disconnect and connect
again", which spends one of ten. Neither build of 2026-11-19 had these
in front of it, and both built them wrongly. Across the three methods
18 of the 30 defects are named by at least one.

**Where it is weaker.**
- *One malformed setting, one malformed field.* A non-numeric port and
  an empty base address are named by no cell: the triage listed the
  settings it thought of, and those two were not among them. The
  frozen method's table of every value against every way of being
  wrong touched these. The list of settings and fields should come
  from the plan's own inventory by script, not from the triage's
  recall.
- *The judge is less steady here* (24 of 30 on named or not), for one
  reason: this method writes both a cell that records the plan's
  decision and a cell that says the documentation contradicts it, and
  the matcher's tie-break ("the less favourable class") sends such a
  defect to "decided wrongly" in two runs and to "named" in the third.
  Three of the five W are of this kind. The matcher's rule does not say
  which wins; it should, and every method would then be scored again
  under the same rule. No count here was changed after the fact.
- *Three kinds of answer, assigned by the answering agents and checked
  by no one.* 192 open cells are called the planner's to decide. Some
  of those will be the owner's.

## Cost

About 440,000 tokens for the three triages, 800,000 for the four
answering agents, 510,000 for the three matcher runs, and the research
agent's dossier (its count was lost when its session ended on a login
error after the file was written; a retry was stopped unused).

## Limits

- One plan, one triage of three, one dossier, one answering. The
  spread of the dossier and of the answers is not measured.
- The dossier's quotes came through a summarising fetch tool and were
  not compared word for word with the pages.
- No test against a real dependency was run; 29 were named.
- `answers.py check` asks for a source only where a cell is tagged as
  contradicting the documentation or is called a fact. A cell called
  the planner's or the owner's that still says something about a
  dependency passes without one: no script can tell that from the
  words, so it stays with the brief and with whoever reads the answers.
- The benchmark is one product of one field. The same steps on a
  product with no provider are untried.
- The bars were proposed by the session and not confirmed by the owner
  before the results were read.
