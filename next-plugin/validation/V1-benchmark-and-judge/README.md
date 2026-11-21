# V1: the benchmark and its judge

**Question:** can the judge that scores every later step be trusted? It
is a model making a call per defect ("did the tables name this one?"),
so before anything leans on it we measure whether it agrees with itself
and with the owner.

## The bar (set before the run, 2026-11-20)

Proposed by the session and taken by the owner's word to start ("Yes,
then start on V1"), over 65 defects and three runs of the matcher:

1. **Named or not:** all three runs put the defect on the same side of
   the line (N or D against W, P or X) for at least 59 of 65 (90%).
2. **Exact class:** all three runs give the same class for at least 52
   of 65 (80%). This line was added to `TODO.md`'s proposal.
3. **Against the owner:** the owner's class matches the matcher's
   majority class on at least 13 of 15 sampled calls.

If a line fails, the judge is fixed and measured again before anything
after V1 is scored.

## What is run

- **The benchmark:** 65 defects from five plans (the fourth project's
  slice 1, the third project's slices 1 to 4), each written once as a
  scenario (trigger, what the build does, what the person meets) by a
  fresh agent that saw only the independent code read and the list of
  ids and titles, never the tables or an earlier scoring. The fourth
  project's list is fixed at the 30-defect split.
- **The matcher:** `matcher-prompt.md`, frozen with its hash in
  `matcher-prompt.sha256` after `wording_check.py` found no term of the
  finance projects in it. A fresh agent per run, on Opus (as the earlier
  scorings were), sees one folder: the prompt, one set of tables (those
  the frozen method built on 2026-11-19) and that plan's scenarios.
  Three runs per plan, fifteen in all.
- **The count:** `agreement.py summary` (no model). Its tests are
  `test_v1.py` (`python3 -m unittest test_v1`).
- **The owner's sample:** `agreement.py sample` draws 15 calls with seed
  20261120, spread over the majority classes and the plans, and writes
  a sheet that shows each defect and the cells the runs cited, without
  any run's class. `agreement.py owner` compares the answers.

Not measured here: the earlier scorings also counted how many of each
table's top 15 cells hit a defect; no bar of this step is in that
count, so the frozen prompt does not ask for it.

## Where the material is

The scenarios, the tables, every run's output and the owner's sheet
quote the projects, so they are in the private audit repository, folder
`v1-benchmark-and-judge/`. This folder holds the prompt, the scripts
and `RESULT.md` (counts only).
