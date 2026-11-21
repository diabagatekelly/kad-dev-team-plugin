# E1: a failure-mode library by kind of action

Outside the V list, at the owner's word (2026-11-21), after V1: "is this
really the best way to improve our requirements", and then "we need a
mechanism to also accurately anticipate failure points even for
something like a Qura'an app". The idea tried here: the columns of a
completeness grid should not come from a model's imagination on each
run, nor from one product's field, but from a library of the ways each
kind of action commonly fails, each entry resting on a public source.

**Question:** does a library written from public sources, by agents who
never saw our defects, hold the failure modes our 65 benchmark defects
are cases of?

## The bar (proposed by the session, in force unless the owner changes it before the result is read)

Over the 65 defects, majority of three runs of the coverage judge:

1. At least 26 (40%) are fully a case of a library entry.
2. At least 47 (72%) are fully or partly one: no fewer than the tables
   of 2026-11-19 touched by V1's judge.
3. The three runs give the same class on at least 55 (85%).

What the measure is and is not: "full" says the library holds the
question whose answer would have settled the defect. It does not say a
plan would have answered it well (seven defects were decisions made
wrongly), and it is a ceiling for a grid built from the library, not
that grid's own score. The cost side is the size: how many entries
there are and how many were never used.

## What is run

- **The library:** four agents, each given `brief.md` (in the private
  folder, copied here as `library-brief.md`) and a set of action types,
  working only from the web, never from this machine's files. Every
  entry cites a page the agent fetched. `library_check.py` refuses an
  entry that is malformed or uses a word of one field of business in
  its own text.
- **The judge:** `coverage-prompt.md`, frozen with its hash. Three fresh
  agents on Opus, each seeing one folder: the prompt, the library, and
  the 65 scenarios of V1's benchmark with their plan names.
- **The count:** `coverage.py` (no model), tests in `test_coverage.py`.

The scenarios and the runs' outputs quote the projects and stay in the
private audit repository, folder `e1-failure-mode-library/`. The
library itself quotes no project and is here: `library.json`.
