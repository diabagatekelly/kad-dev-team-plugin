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

## 3. The same steps on a second plan: the bar is met

The third project's slice 1, 13 defects, the matcher's second version,
three runs each.

| | Frozen tables | E3: triage, dossier, answers |
|---|---|---|
| Named (N or D) | 1 | **4** |
| Named or part | 9 | 10 |
| Not named (X) | 4 | 3 |
| Named, run by run | 1, 1, 1 | 4, 4, 4 |
| Runs give the same class | 12 of 13 | 10 of 13 |
| Cells | 283 | 493 |
| Cells where the plan contradicts the documentation | 135 mentions of a silent or contradicting tag in all | 42 |

The bar was at least as many named and at least as many named or part
as the frozen tables on this plan under the same matcher: met on both
(4 against 1, 10 against 9), in every run.

The four it names, the same four in all three runs:

- the connection left at the provider when the reply to its creation
  is lost (the defect that came back in every project);
- the provider library's error object carrying the secret (the frozen
  tables had this one too, as a decision the build missed);
- a locked secret store at start, with nothing said on screen;
- the last save lost to a power cut just after it is reported done.

The first two rest on dossier facts: 14 of this plan's 111 statements
about its dependencies contradict their documentation, and this
dossier's quotes were machine-checked against the downloaded pages.
The other two come from the library's questions on calling a
dependency at start and on durable writes. The triage kept every entry
E1's judges had tied to this slice's defects (7 of 7 full, 4 of 4
part), with 180 of 250 questions kept for 493 things.

Of 281 open cells, 182 are the planner's, 64 a fact about a
dependency, 35 the owner's (26 distinct questions); 51 answers are
marked for a test against the real thing.

What it still does not reach on this plan: a body that is the word
"null", a response header, a line of the README (none); a non-numeric
port, a letter-case way round a folder guard, a log step for one route
(part at best). These are code-level or the plan's own detail.

**Cost:** this plan's triage about 143,000 tokens, its dossier
357,000, its four answering agents 890,000, its three matcher runs
470,000: about 1.9 million for one slice, of which the dossier and
the answers are the method and the matcher is only the measurement.

## Both plans together, under the second version

| | Frozen tables | E3 |
|---|---|---|
| Named, of 43 defects | 11 (26%) | 17 (40%) |
| Named or part | 32 (74%) | 33 (77%) |
| Cells | 958 | 963 |

The gain is in turning "touched" into "named": the same share of
defects is reached, and half again as many are stated outright, for
the same number of cells. Two plans, one filling each, both from one
field and one provider: the direction agrees on both, the size of the
gain is not yet pinned down, and a product with no provider is untried.

## Limits

- One triage, one dossier and one answering per plan; their spread is
  not measured. The matcher's three runs agree with each other on
  named for the second plan (4, 4, 4) and range 11 to 13 on the first.
- The second plan was chosen as the first slice of the third project
  before any of its results were seen; the other three slices of that
  project are not run.
- The bars were proposed by the session and not confirmed by the owner
  before the results were read.
