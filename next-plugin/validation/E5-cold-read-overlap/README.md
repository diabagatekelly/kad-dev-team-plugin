# E5: how many cold reads

The owner, 2026-11-21, on the review end of the plan: "maybe cold read
would be sufficient to catch any remaining blind spots", and then "We
can evaluate how many cold reads and answer the question now."

**Question:** when several readers who know nothing of each other read
the same build cold, how much of what one finds do the others find, and
how many readers is it worth running?

## What is run

- **The build:** the fourth project's slice 1 as built by the `light`
  arm, at the commit its first cold read assessed.
- **The readers:** three new ones, each a session of the model the
  brief names, each in its own VM (V0's Docker Sandboxes, from the
  image prepared there), given the existing brief
  `evals/tools/cold_read.md` unchanged and a neutral clone: no remote,
  no tags, the branch named `work`. No reader sees another's report,
  the earlier cold read, a plan, a table or the benchmark. The earlier
  cold read of the same commit (2026-11-19, on the host) is the fourth.
- **The matching:** a fresh agent is given the four lists of confirmed
  and to-verify bugs and says which are the same defect: the same
  trigger and the same faulty behaviour. When unsure, they are
  different defects, which counts against overlap.
- **The count:** by script, no model: how many distinct defects in all,
  how many each reader found, how many each further reader added, and
  an estimate of how many remain unfound from how often defects were
  found once and twice.

## The rule for reading the result (set before any read came back)

A further reader is worth running while it adds at least 3 defects that
no earlier reader found, taken over every order the readers could have
come in. The number of readers the result supports is the largest
number for which that holds on average.

Limits known beforehand: one build of one product; four readers; the
three new reads run in a VM and the earlier one on the host under the
old sandbox; "the same defect" is one agent's judgment.

The reads, the matching and the build quote the project and stay in
the private audit repository, folder `e5-cold-read-overlap/`.
