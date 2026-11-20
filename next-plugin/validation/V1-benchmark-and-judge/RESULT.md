# V1 result (2026-11-20): two lines of the bar met, the owner's line open

Fifteen matcher runs (three per plan, each a fresh agent on Opus that
saw one folder) over the 65 defects, counted by `agreement.py summary`.

| Line of the bar | Bar | Result | |
|---|---|---|---|
| All three runs on the same side of named / not named | 59 of 65 | 63 of 65 (97%) | met |
| All three runs give the same class | 52 of 65 | 58 of 65 (89%) | met |
| The owner agrees with the majority class | 13 of 15 | not yet judged | open |

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
