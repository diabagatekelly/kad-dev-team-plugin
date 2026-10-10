# library-app: the shared eval fixture

A lending service for a community library, written to be reviewed by this
plugin's personas under `claude plugin eval`. One realistic app rather
than clean-vs-dirty snippets: most of it is sound, and every deliberate
exception is catalogued in `answer-key.md`. The first persona to use it is
`software-architect` (`evals/library-app-*`); the layout is meant to carry
other personas' plants too.

## Layout

```
app/
  catalog/        books and search                 clean module (T10)
  members/        registration, suspension         V4 (port imports a driver type), V5 (table-shaped domain type)
  lending/        loans, renewals, holds           V1 (ORM in a use case), V2 (runtime import cycle), V3 (HTTP request crosses in), V15 (use case imports main/), T1 (type-only cycle)
  fines/          overdue fines, payment, waivers  V6 (policy mixed with mechanics), V7 (leaky payment port), V8 (premature strategy), T5 (documented rounding split)
  notifications/  due-date reminders               V9 (missing channel abstraction), V10 (port on the implementer's side), T3 (one-impl port over I/O)
  reporting/      legacy reports and CSV export    V13 (SQL-level port), V14 (orchestration mixed with CSV bytes), V12 (SDK in a report), T4, T8
  services/       refunds                          V11 (technical-role directory), V12 (SDK outside its adapter)
  utils/          date helpers                     V11, T6 (low-risk date library)
  infra/          postgres, email, sms, postal, payments, files, http, logging, monitoring adapters   T9; S1, S2, S3, S5, S7, ST1, ST3, ST4, ST6
  main/           server.ts, wiring.ts, jobs.ts    T7 (bootstrap and composition root, exempt); S4, S8, ST2, ST7
  test/           node:test tests and fixtures     S11
  .github/        deploy workflow                  S9, S10, ST5
  types/          ambient declarations for the fictional third-party packages
answer-key.md     every V (planted violation) and T (trap), with the principle each exercises
verify.sh         type-checks, proves the runtime cycle crashes and the type-only one doesn't, runs test/
scaffold.sh       copies app/ into an eval run's working directory; each case has a stub that execs it
```

The third-party packages (`pg-orm`, `express-lite`, `stripe-sdk`, ...) are
fictional. `types/vendor.d.ts` declares them for `tsc`; `verify.sh` stubs
them at runtime for the module-load checks. Nothing in the app is meant to
run for real.

## Invariants, in order of how often they were broken while building it

1. **No accidental problems.** Every unplanned issue a reviewer finds is a
   gift to the no-plugin baseline and noise for the pairwise judge. The
   first calibration found five (an availability count nothing
   decremented, a report using two clocks, an unvalidated value in a file
   path, a waiver that marked a fine settled, three modules never wired).
   `verify.sh` catches type errors, not incoherence; read the app as a
   reviewer would before planting anything.
2. **No hints.** No comment explains a defect, no prompt names one. The
   earlier snippet cases gave the answer away in comments and the base
   model found everything.
3. **`answer-key.md` is the source of truth.** Graders are derived from it.
   When a run disagrees with a grader, decide first whether the key is
   wrong (it was, four times), then the grader, then the skill.
4. **Traps are not optional.** A planted violation shows a reviewer can
   find things; a trap shows it knows when not to. Each principle in the
   skill under test should have one of each where the principle has a
   "looks wrong but isn't" side. `verify.sh` must prove any trap that
   depends on runtime behaviour (the type-only cycle).
5. **Keep it compiling.** Run `verify.sh` after every edit to `app/`.

## Extending it for another persona

Plant in the same app; don't fork it. Each persona gets its own prefix in
`answer-key.md` (`S` for security, `R` for reliability, `Q` for test
quality, ...) and its own `evals/<persona-or-skill>-*` cases; a module can
carry plants for several personas as long as each case's prompt scopes
the reviewer to what that persona grades. Candidates the app already
invites:

- `devsecops-engineer` / `security-review`: done, see the `S`/`ST` rows in
  `answer-key.md` and `evals/security-review-*`.
- `devsecops-engineer` / `reliability-review`: `main/jobs.ts` runs on a
  timer with no error handling outside the reminder loop and no idempotency; `fines/collect-fine.ts`
  charges before it settles.
- `tdd-coach` / `test-quality-review`: there are no tests. Add a `test/`
  directory with planted smells (a spy that replaces the subject, a test
  that asserts a mock was called) and clean tests as traps.
- `code-reviewer` / `code-review`: `reporting/export-report.ts` and the
  three `*-reminder.ts` files carry duplication and naming material.
- `architecture-cartographer` / `map-update`: the import graph is real;
  V2 and T1 are a ready-made cycle pair, V1/T9 a ready-made duplication
  candidate.

When a plant for one persona would change what another persona's case
expects, update the other persona's answer-key rows and re-run its cases
before committing; `answer-key.md`'s "known observations" section is
where cross-persona overlap gets recorded so a grader on one side doesn't
read the other side's plant as a false alarm.

## Running

```
bash evals/fixtures/library-app/verify.sh
claude plugin eval . --case 'library-app-*' --ablation with-without --scaffold \
  --judge-model sonnet --max-cost-usd 14 --no-publish --trust-plugin
python3 -I evals/tools/pairwise_judge.py evals/results/<timestamp>
```

`--scaffold` is not optional; without it the agent gets an empty working
directory and the judge grades an empty review (it passed one, once).
