# Notes on this case

## Rework done: graders split into portable and fixture-specific

Every LLM grader here used to assert specifics of one fixture — a
CSV-export slice with a synchronous-vs-asynchronous decision and an
engineer proposing a generic pluggable-formatter interface. That meant a
real dogfooding run's design doc (`evals/example/design-001.md`) had
nothing in this case that applied to it — every other artifact in that run
was gradable by borrowing its owning case's graders; this one wasn't. See
`evals/example/summary.md`.

Split per the plan this section used to describe:

- **`portable-*` graders** hold for any design doc: an explicit importance
  ordering is stated rather than left implicit
  (`portable-states-importance-ordering`); the doc stays conceptual, no
  code/file paths/signatures (`portable-stays-conceptual`); every real
  decision shows as presented-and-approved rather than autonomously
  settled (`portable-decisions-shown-as-approved`); at least one boundary
  names what crosses it (`portable-boundaries-name-what-crosses`, new —
  nothing previously checked Good Fences at all).
- **`fixture-*` graders** keep asserting this case's own content —
  the sync/async decision (`fixture-asks-about-structural-fork`), the
  premature-abstraction rejection (`fixture-catches-premature-abstraction`),
  and that both approved choices survived into the final structure
  (`fixture-reflects-approved-decisions`, trimmed to drop the general
  approval-narrative check once `portable-decisions-shown-as-approved`
  covered it).

Only the `portable-*` graders get borrowed when grading real artifacts
going forward (`skill-invoked` and phase-targeted graders still don't
apply to a dogfooded artifact regardless of this split — see
`evals/README.md`'s note on the `example/` directory).

## Format note

This case is three-phase, extending the two-phase ask-then-continue format
`agent-eval` documents. See its own `prompt.md`.
