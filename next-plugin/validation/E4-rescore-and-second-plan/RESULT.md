# E4 results (2026-11-21)

## 1. Every method scored again under the matcher's second version

The fourth project's slice 1, 30 defects, three runs each, the
majority class. The first version's figures are in brackets.

| | Frozen tables | E2: library crossed with everything | E3: triage, dossier, answers |
|---|---|---|---|
| Named (N or D) | 10 (10) | 12 (10) | **13** (10) |
| Named or part | 23 (24) | **25** (20) | 23 (22) |
| Decided wrongly (W) | 3 (3) | 2 (5) | 1 (5) |
| Not named (X) | 4 (3) | 3 (5) | 6 (3) |
| Named, run by run | 9, 11, 9 | 13, 11, 12 | 13, 11, 12 |
| Runs give the same class | 25 of 30 | 21 | 22 |
| Runs agree on named or not | 27 of 30 | 26 | 25 |
| Cells | 675 | 1,172 | 470 |

- The tie-break did what it was written for: the defects a
  contradicting or silent cell names in full no longer fall to
  "decided wrongly" on a coin toss. E3's W went from 5 to 1, E2's from
  5 to 2; the frozen tables, which seldom had both kinds of cell for
  one defect, did not move.
- **The two library methods are level with each other and a little
  ahead of the frozen tables on named (12 and 13 against 10), and all
  three are level on named or part (23 to 25).** Each method's own
  runs range over two or three defects, so "a little ahead" is at the
  edge of what three runs of one filling can show.
- **Which defects:** five are named by all three, nineteen of the
  thirty by at least one. Four are named only by E3 (the one-minute
  give-up against a slower first pull; the saved access lost after the
  connection exists at the provider; a port already in use; a second
  connect refused only at the end). Four only by E2 (a setting taken
  for the wrong mode; an empty result shown as connected; a damaged
  file at start; a key of the wrong length). None only by the frozen
  tables.
- E3 has the most "not named" (6): it asks fewer questions, and what
  the triage did not think to apply a question to is simply absent.
  E2's crossing of everything catches some of those at 2.5 times the
  cells.
- This re-scoring changed the rule after the first results were read.
  It is one sentence, applied to all three alike, and the owner was
  told before the runs; the first version's figures stay in the
  earlier result files.

## 2. Where the list of settings comes from

`settings_inventory.py` on the fourth project's `light` build:

| | |
|---|---|
| Settings the build reads from its environment | 5 (a port, the provider's base address, the database path, the provider's client id and secret) |
| Of those, named anywhere in the plan | 0 |
| Lookups whose name is built at run time | 1 (a family of per-institution settings), reported for a person to read |

The two defects E3 missed (a non-numeric port, an empty base address)
are about settings the plan never names: the build introduced them. No
inventory taken from the plan could list them. So the proposal changes:
at plan time the question is answered once, as a rule for every
setting (what happens when one is missing or malformed); at build time
this script lists what the code actually reads, and each is held
against the rule. It belongs with the traceability scripts of V7.

## 3. The same steps on a second plan

Not finished at the time of writing: see below when added.
