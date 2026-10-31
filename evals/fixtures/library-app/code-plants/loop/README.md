# loop: the chunk loop's states for the cancel-hold slice

The orchestrator's chunk loop (`skills/orchestrator/SKILL.md`, "The chunk
loop") cannot be run end to end in an eval: a whole slice is hours of
agent launches. What can be run is one step at a time, from the state a
previous session left behind: the loop writes `handoff-slice-<nnn>.md`
when a session ends mid-build and resumes from it on the next invocation.
`state.sh <state>` builds that state for real (the git history the loop
would have made, the gate files `validation_gate.py` really printed, the
sidecar `rounds_record.py` really wrote from the planted reports), and the
`orchestrator-*` cases under `evals/` resume the orchestrator from it and
grade the one step they are about.

- `state.sh`: the builder; its header lists the states.
- `snapshots/<name>/`: the code at each point, complete overlays over the
  app plus the `tdd` runner, each type-checked and its tests run by
  `verify.sh` (`slice-fixed` is a delta the delivery state layers over
  `slice-built`). `chunk1-comments` and `seam-fake` are review plants for
  the `code-review-comments-chunk` and `test-quality-review-seam-fake`
  cases, not loop states.
- `docs/`: the planning-stage log entries, the delegation file, the plan
  (every Done when names its seam test), the chunk sections the builders
  append, a reliability document and a slice that points at it (for the
  delegated-consult cases), the README the `readme` skill would write.
- `records/`: the reports, in the shared finding format, with `@PLAN@`,
  `@C1@`, `@F1@`, `@BASE@`, `@HEAD@`, `@FIX@` for the commit hashes the
  builder fills in. Line numbers in them point at the snapshots' lines.
- `package.json`, `eslint.config.js`, `.prettierrc`, `bin/`: the manifest
  with `lint` and `typecheck` scripts, and the `eslint` and `tsc` stand-ins
  the builder copies into `node_modules/.bin/` (the sandbox cannot install
  packages; the Definition of Done and the gate only need the scripts to
  exist and exit 0). They are Bash scripts, so this fixture runs on Linux
  and WSL, not on native Windows.
- `tools/gh`: a recording stand-in for the GitHub CLI, for the delivery
  state; it logs each call to `gh-calls.log` beside it and answers in the
  real command's shape.

Plants, for `answer-key.md`'s `L` rows:

| # | Where | What |
|---|---|---|
| L1 | `chunk1-deviation`: `lending/hold.ts` | a file inside a design module that the chunk's Files line does not name: a deviation, not a failure |
| L2 | `chunk1-outside`: `utils/card-number.ts` | a file outside every design module: the gate fails, once, to a fixer |
| L3 | `records/chunk-1-r1-review.md` | one finding on the fix's own line (a regression) and one on a line the fix did not touch (pre-existing, standing) |
| L4 | `records/chunk-1-r0-review-gap.md` | a `needs-decision (devsecops-engineer:reliability-requirements)` finding, in a state with no delegation file |
| L5 | `docs/implementation-report-plan.md` with chunk 2's seam entry stripped (`plan-no-seam`) | a plan that fails the B step's seam check |
| L6 | `chunk1-comments/lending/cancel-hold.ts` | nine WHAT-comments and one citing "decision 7 in design-001"; the WHY-comment in `in-memory-hold-queue.ts` is the trap |
| L7 | `seam-fake/test/cancel-hold.test.ts` | every test fakes `HoldQueue` with a hand-rolled class although `InMemoryHoldQueue` is the real local adapter; no seam test; the fixed clock is the trap |
| L8 | `slice-built` | no README; a `<script>` body in `lending/cancel-hold-notice.ts`'s template literal; comment density over 5% |
| L9 | `chunk1-done`'s handoff | the loop's start time six hours before the scaffold ran: the 5 h budget is exceeded at the chunk boundary |
| L10 | `delivery-ready` | two standing Mediums and three Lows in the sidecar; the tracker is GitHub; the `gh` stand-in records what gets filed |
