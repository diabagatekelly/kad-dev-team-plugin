# V1 result (2026-11-20 and 21): the owner's word is that the judge holds, with 11 of the 15 sampled calls agreeing against a bar of 13

Fifteen matcher runs (three per plan, each a fresh agent on Opus that
saw one folder) over the 65 defects, counted by `agreement.py summary`.

| Line of the bar | Bar | Result | |
|---|---|---|---|
| All three runs on the same side of named / not named | 59 of 65 | 63 of 65 (97%) | met |
| All three runs give the same class | 52 of 65 | 58 of 65 (89%) | met |
| The owner agrees with the majority class | 13 of 15 | 11 of 15 | **not met** |

Defects named (N or D), run by run:

| Plan | Defects | Run 1 | Run 2 | Run 3 | Scoring of 2026-11-19 |
|---|---|---|---|---|---|
| Fourth project, slice 1 | 30 | 10 | 10 | 10 | 17 |
| Third project, slice 1 | 13 | 1 | 1 | 1 | 4 |
| Third project, slice 2 | 10 | 0 | 0 | 0 | 4 |
| Third project, slice 3 | 7 | 0 | 0 | 0 | 1 |
| Third project, slice 4 | 5 | 0 | 0 | 0 | 0 |
| **All** | **65** | **11** | **11** | **11** | **26** |

Majority classes: N 9, D 2, W 7, P 36, X 11. The seven defects the runs
split on: five between P and X, two between N and P.

## What it says

**The judge agrees with itself.** The count of defects named did not
move across the three runs on any plan.

**It is a stricter judge than the one of 2026-11-19, on the same
tables.** Against that scoring, bug by bug: 15 defects went from N to P,
5 from X to P, 1 from P to W; the other 44 kept their class. So the
same tables name 11 of 65 defects (17%) by this judge against 26 of 65
(40%) by the earlier one: 33% against 57% on the fourth project, 3%
against 26% on the third. The 15 are cells that name the defect's
trigger without stating what goes wrong: this prompt asks an N cell to
state both, and the earlier matcher (whose prompt was not kept) gave N
on the trigger alone when it read the scenario as the same.

That is a choice of where the line sits, not something the three runs
can settle: a consistent judge can be consistently too hard. The
owner's 15 calls are the measure of it. Until they are read, neither
set of percentages is the baseline, and no later step is scored.

## The owner's 15 calls (2026-11-21)

Read out one at a time in the session, the matcher's class hidden until
all 15 were given. 11 agree. The four that differ all cross the line
between named and not named:

| Sampled defect | Owner | Matcher (all three runs) | What separates them |
|---|---|---|---|
| Third project, slice 1, defect 5 | D | P | a decision in general terms against a defect that is one specific way round it |
| Third project, slice 3, defect 4 | N | P | a defect in two parts, the cells covering one |
| Third project, slice 2, defect 8 | N | P | the same harm under a neighbouring trigger |
| Fourth project, slice 1, defect B7 | P | N | the same harm under a neighbouring trigger, read the other way |

On the eleven others, among them every W, every X and both defects no
cell was cited for, owner and matcher agree. So the disagreement is not
about the classes but about one line: how far a cell's trigger may sit
from the defect's, and how much of a defect it must cover, to count as
naming it. The owner drew that line more generously three times and
more strictly once, the last two rows being the same kind of case
judged in opposite directions, which says the line is soft for a
person too.

By the count, the third line is not met. **The owner's word, read with
the four differences in front of them (2026-11-21):** "I don't disagree
with the matcher's assessment necessarily, some of my decisions could
have been due to me not fully understanding the bug. There were also a
few where I was between 2 so I'm ok to call it a success." So V1 holds
on the owner's word, not on the count, and the count stays recorded as
11 of 15.

## The baseline this judge gives

From the majority class of the three runs, on the tables the frozen
method built on 2026-11-19. Two counts are kept from here on, because
the line between them is the one a person finds soft: **named** (N or
D) and **named or part** (N, D or P).

| Plans | Defects | Named | Named or part | Decided wrongly (W) | Not named (X) |
|---|---|---|---|---|---|
| Fourth project, slice 1 | 30 | 10 (33%) | 24 (80%) | 3 | 3 |
| Third project, slices 1 to 4 | 35 | 1 (3%) | 23 (66%) | 4 | 8 |
| All | 65 | 11 (17%) | 47 (72%) | 7 | 11 |

These replace the 57% and 26% of the 2026-11-19 scoring as the figures
later steps are compared with. A later step's gain is read on both
counts.

How the calls were taken, since it bears on the count: the first pass
was abandoned after eight calls when it turned out the question had
been put unclearly (the owner was judging whether the plan was silent,
not whether a cell described the defect) and all 15 were taken again
from the first. The session described each defect and cell in plainer
words than the sheet's and, on five calls, pointed out a difference
between the cell's trigger and the defect's. On two calls the sheet had
dropped a cell's tag and its row heading; the full rows were then shown
and one call was changed by the owner (W to N) before any matcher class
was seen. A cleaner repeat would give the owner the full rows from the
start and no gloss.

## Cost

Twenty agents: five scenario writers (about 330,000 tokens in all) and
fifteen matcher runs (about 1,190,000 tokens, 72,000 to 101,000 each,
36 to 112 seconds each). Not yet priced from the transcripts.

## Limits

- The earlier scorings read the code reads themselves; these runs read
  scenarios written from them. A scenario is fixed text, which is the
  point of a benchmark, but it is one writer's reading of each defect.
- The owner's sheet shows only the cells some run cited. A cell every
  run missed is not on it, so the owner's line cannot catch a defect
  wrongly given X for that reason.
- A matcher agent is told to read only its folder; nothing enforces it.
  Each run's report says it did.
- The sample of 15 was drawn after the runs, with a fixed seed, three
  per plan: majority classes P 7, X 3, W 2, N 2, D 1.
