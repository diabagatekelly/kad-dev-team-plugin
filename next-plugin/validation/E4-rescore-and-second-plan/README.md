# E4: three follow-ups to E3 (the owner, 2026-11-21: "Go ahead with 1-3")

## 1. The matcher's tie-break, and every method scored again

E3 writes, for one defect, both a cell recording the plan's decision
and a cell saying the documentation contradicts it. V1's matcher did
not say which wins, and its runs split between "decided wrongly" and
"named". `matcher-prompt-v2.md` (hash in `matcher-prompt-v2.sha256`)
adds one sentence to rule 1 and changes nothing else: a defect that a
PLAN SILENT or CONTRADICTS DOCS cell names in full is N, even if a
DECIDED cell also names the trigger; W is for a defect that only
DECIDED or IMPOSSIBLE cells name. The rule was chosen by the session,
for the reason that N means "the tables flagged it before the build".

All three methods' tables for the fourth project's slice 1 are scored
again under it, three runs each, with nothing else changed: the frozen
tables of 2026-11-19, E2's grid and E3's answered cells. The owner's 15
calls in V1 were compared with the first version; none of the 15 turned
on this tie.

## 2. Where the list of settings comes from

E3 missed two defects about one malformed setting. The proposal was to
list settings by script from the plan. `settings_inventory.py` (no
model, tests in `test_settings_inventory.py`) reads a build's source
for the settings it takes from its environment and the plan for each
name.

## 3. The same steps on a second plan

The third project's slice 1 (13 defects; the frozen tables named 1 by
V1's judge): the plan at the commit named "ready for implementation",
with the orchestrator's log and the delegation file removed; one
triage, one dossier, the answers, then the matcher (second version)
three times, and the frozen tables for that plan three times under the
same version.

**The bar for part 3 (proposed by the session, in force unless the
owner changes it before the result is read):** named at least as many
as the frozen tables for this plan under the same matcher, and named or
part at least as many; the size reported beside them.
