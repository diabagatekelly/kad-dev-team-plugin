# Notes on this case

## Its graders are fixture-bound and don't port

Every LLM grader here asserts specifics of one fixture — a CSV-export
slice with a synchronous-vs-asynchronous decision and an engineer proposing
a generic pluggable-formatter interface:

- `asks-about-structural-fork` requires "exactly one decision (the
  synchronous-vs-asynchronous export question)" with a named recommendation.
- `catches-premature-abstraction` requires rejecting a specific generic
  export interface.
- `reflects-approved-decisions` requires "no job-status/notification
  component" and "no generic pluggable-formatter interface" in the output.
- `stays-conceptual-and-states-importance` is the only broadly portable one.

**Consequence, observed rather than theorised:** the dogfood run in
`evals/example/` produced a real design doc (`design-001.md`) that could
not be graded at all. Every other artifact in that run was gradable by
borrowing its owning case's graders; this one had nothing that applied. See
`evals/example/summary.md`.

## What the rework looks like

Split the graders into two kinds, rather than loosening the existing ones:

1. **Portable property graders** that hold for any design doc — an explicit
   importance ordering is stated rather than left implicit; the doc stays
   conceptual (no code, no file paths, no signatures); every real decision
   shows as presented-and-approved rather than autonomously settled;
   boundaries name what crosses them.
2. **Fixture-specific graders** that keep asserting this case's particular
   sync/async and premature-abstraction content, clearly labelled as such.

Only the first kind gets borrowed when grading real artifacts. Keeping both
is better than replacing one with the other: the fixture-specific graders
test the two behaviours this case was built for, and losing them to gain
portability would be a bad trade.

## Also unrun

This case is stale on two counts as of the last commit: `AGENT.md` and
`SKILL.md` both changed (the "Technology at a boundary" section was added
to the skill), and it was missed on the first re-run pass. It sits last in
`evals/README.md`'s run backlog because running it before the grader rework
just re-confirms a fixture-bound result.

## Format note

This case is three-phase, extending the two-phase ask-then-continue format
`agent-eval` documents. See its own `prompt.md`.
