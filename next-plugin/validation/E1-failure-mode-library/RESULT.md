# E1 result (2026-11-21): the bar is met; a library from public sources holds the question behind 30 of our 65 defects

`library.json`: 250 entries over 21 kinds of action, resting on 115
public pages, written by four agents that saw only the brief and the
web. Three fresh judges on Opus each classed all 65 benchmark defects
against it; `coverage.py` counted.

| Line of the bar | Bar | Result | |
|---|---|---|---|
| Fully a case of a library entry | 26 of 65 | 30 (46%) | met |
| Fully or partly | 47 of 65 | 55 (85%) | met |
| The three runs give the same class | 55 of 65 | 59 (91%) | met |

| Plans | Defects | Full | Part | None |
|---|---|---|---|---|
| Fourth project, slice 1 | 30 | 18 | 8 | 4 |
| Third project, slices 1 to 4 | 35 | 12 | 17 | 6 |
| All | 65 | 30 | 25 | 10 |

The six defects the runs split on are each one class apart (four
between full and part, two between part and none).

## Beside the tables of 2026-11-19, defect by defect

Rows: the class V1's judge gave the tables. Columns: the library.

| Tables | Defects | Library full | Library part | Library none |
|---|---|---|---|---|
| Named (N or D) | 11 | 8 | 2 | 1 |
| Part (P) | 36 | 16 | 16 | 4 |
| Decided wrongly (W) | 7 | 2 | 4 | 1 |
| Not named (X) | 11 | 4 | 3 | 4 |

- Of the 36 defects the tables only touched, the library holds the
  full question for 16.
- Of the 11 the tables did not name at all, it holds the question for 4
  and part of it for 3. Four are in neither.
- On the third project the tables named 1 of 35; the library is full
  for 12.

**These two are not the same measure, and the library's is the easier
one.** A table cell had to state this product's trigger and what goes
wrong; a library entry only has to be the general condition the defect
is a case of. "Full" says the right question exists in the library. It
does not say that a grid built from the library, filled in for a real
plan, would have flagged the defect, nor that the plan would then have
answered well (two of the seven wrongly decided defects have the
question in the library, and were decided wrongly anyway). That grid is
the next thing to measure, with V1's judge, like for like.

## What the library does not reach

The ten "none" are, by the judges' reasons: a rule of the product
itself being wrong or worded wrongly (about six), a choice of request
parameter, a defect of the documentation and one of the test suite,
and a response header no entry names. A general library cannot hold a
product's own rules; those stay with the plan's review and with facts
checked against what the product depends on.

## The cost side

- 57 of the 250 entries were the reason for a full or part call; 193
  were not used by these 65 defects. Three kinds of action were never
  used (time, a fixed body of content, accessibility) and two barely
  (limits, authorization): these two projects are small local tools
  with one provider. That is expected of a library meant for any
  product, and it is also unproven until a product of another kind
  uses those entries (the held-out product of V8).
- A grid for one slice would take only the entries of the kinds of
  action that slice performs; how many cells that makes, and how many
  a person has to read, is not measured here.
- Tokens: about 530,000 for the four compiling agents and 340,000 for
  the three judges.

## Limits

- Most of the entries' short evidence quotes came through a summarising
  fetch tool and were not compared word for word with the pages. Two
  sources are copies of pages that refused the request (a list of
  falsehoods about time, a testing cheat sheet). Before the library is
  relied on, each entry's source is checked by a script that fetches
  the page.
- Some entries in different kinds of action state neighbouring
  conditions; none was removed.
- One judge's report gave a wrong count of the library's entries (192);
  its output cites entries from every part of the file, like the other
  two, so its run is kept.
- The 65 defects are all from two products of one field. The library
  was written blind to them, which guards against tuning, not against
  the benchmark being narrow.
- The bar was proposed by the session and not confirmed by the owner
  before the result was read.
