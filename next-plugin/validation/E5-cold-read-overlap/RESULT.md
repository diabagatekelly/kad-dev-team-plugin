# E5 result (2026-11-21): one cold read finds about half of what four find; the rule supports three readers

Four independent readers of the same build (three new ones in VMs, the
read of 2026-11-19 as the fourth), their findings matched twice by two
agents that did not see each other's work. Where the two matchings
differ, both figures are given.

| | Matching 1 | Matching 2 |
|---|---|---|
| Distinct defects found by the four | 25 | 26 |
| Found by each reader | 12, 14, 15, 14 | 12, 15, 15, 14 |
| Found by one reader only | 8 | 9 |
| Found by two | 8 | 8 |
| Found by three | 5 | 5 |
| Found by all four | 4 | 4 |
| Added by the 1st, 2nd, 3rd, 4th reader, on average over every order | 13.8, 5.9, 3.3, 2.0 | 14.0, 6.2, 3.6, 2.3 |
| Share of everything found, after 1, 2, 3 readers | 55%, 79%, 92% | 54%, 78%, 91% |
| Estimated defects no reader found | 4 | 5 |
| **Readers the rule supports** (a further one adds at least 3) | **3** | **3** |

## What it says

**One cold read is not a net.** Any one reader found 12 to 15 of the
25 or 26 defects the four found between them, and by the estimate
there are four or five more that none found: so one reader sees a
little under half of what is there, two about two thirds, three about
three quarters.

**The second reader is worth most, the third still clears the rule,
the fourth does not.** A second reader adds about six defects, a third
between three and four, a fourth about two.

**What every reader finds and what one finds differ in kind.** All
four found the same four: a malformed stored date bringing every page
down, and three ways of crashing at start (a damaged file, an older
layout, a port in use). The defects only one reader found are the
quieter ones: a connect still running shown as failed after a reload,
a time limit that can be overrun, a leftover access never removed when
a key is malformed, a duplicate id failing a connect.

**A cold read is cheap in time and dear in tokens.** Each new read took
9 to 11 minutes and about 105,000 tokens of output, with 7.5 to 9
million tokens of input, nearly all of it its own context read again
from cache over 60 to 70 tool calls.

**It does not reach what the dossier reaches.** No reader had the
provider's documentation, by design. Counting mentions in the four
reports: how long a first pull can take, the window of history a first
update covers, and a slot that removal does not give back come up
rarely or not at all (the counts are in the private folder), and where
they do it is as something to verify. The plan-time research and the
cold read look at different things; neither replaces the other.

## For the plan

- V6's blind cold read is three readers for a slice that carries real
  harm (a first slice, a new dependency), and at least two otherwise;
  one is not enough to call a slice read.
- Three readers in three VMs ran side by side in about eleven minutes,
  so the cost is tokens, not time.
- The estimate of what no reader found (four or five here) is a number
  the review can report each time, from the same script.

## Limits

- One build of one product. Four readers is few for an estimate of the
  unseen; it is a lower bound by construction.
- The three new reads ran in a VM on 2026-11-21 and the fourth on the
  host on 2026-11-19; all four used the same brief and model.
- "The same defect" is a judgment. Two agents made it independently and
  agree on every figure but one (25 against 26 distinct, from one
  finding split in two).
- The readers' findings were not themselves re-verified here; each
  reader marks its own as confirmed by execution or to verify.
- The rule (a further reader is worth it while it adds at least three)
  was set by the session before the reads came back and not confirmed
  by the owner.
