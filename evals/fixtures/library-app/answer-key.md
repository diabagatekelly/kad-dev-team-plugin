# library-app answer key

Never visible to an agent under evaluation: each case's `scaffold.sh` copies
only `app/` into the run's working directory (runs need `--scaffold`), so
this file, `verify.sh` and the graders stay outside the agent's reach.
Graders are derived from this file; when a grader and this file disagree,
this file is wrong or stale, fix it first.

`app/` is a lending service for a community library. Most of it is sound;
the rows below are the deliberate exceptions. Everything not listed is
meant to be clean, and `verify.sh` proves the app type-checks, that the
planted runtime cycle really crashes, and that the type-only one really
doesn't. Each row names the principle from `agents/software-architect/AGENT.md`,
`skills/architecture-review/SKILL.md`, or `.synthesis/software-architect.md`
it exercises.

## Planted violations (a good review flags these)

| # | Where | Principle | What is wrong | Expected verdict |
|---|---|---|---|---|
| V1 | `lending/checkout-book.ts` | Dependency Rule, high entanglement | Imports `OrmRepository`/`OrmRow`/`PgClient` from `pg-orm`, declares its own ORM row class, queries through it, and `run()` returns the ORM row. The `LoanStore` port already exists and is unused here. | Must fix; top severity for a Dependency Rule finding, since the whole class is built around the ORM (constructor, field, query, return type). Fix: depend on `LoanStore`. |
| V2 | `lending/loan.ts` ↔ `lending/loan-policy.ts` | Circular dependency (Critical) | Mutual value-level imports; `Loan.policy = new LoanPolicy()` and `LoanPolicy.sample = new Loan(...)` run at module load. `require('lending/loan')` throws `TypeError: Loan is not a constructor`. | Critical / must fix. Fix: drop `LoanPolicy.sample`, or inject the policy. |
| V3 | `lending/place-hold.ts` | Good Fences (framework type crossing as-is) | `run(req: HttpRequest)` takes the `express-lite` request object; parsing `params`/`body` happens inside the use case. | Flag. Fix: `run(isbn, cardNumber)`, parse in `infra/http/lending-routes.ts`. |
| V4 | `members/member-directory.port.ts` | Two-direction check (backward) | The port file imports `PgClientOptions` from `pg-orm` and exposes `connection` on the interface. `register-member.ts` and `suspend-member.ts` look clean but inherit the dependency. | Flag, located in the port file, not in its callers. Fix: remove `connection`; connection config belongs to the Postgres adapter / `main/wiring.ts`. |
| V5 | `members/member.ts` | Dependency Rule without an import ("design influence") | Domain type mirrors the table: `member_row_id`, `row_version`, `created_at_utc`, `updated_at_utc`, single-letter DB codes `status_code: 'A'\|'S'\|'L'`, `contact_pref_code: 'E'\|'S'\|'P'`. No import to grep for. | Flag. Fix: domain-named fields and enums, mapping in `infra/postgres/postgres-member-directory.ts`. |
| V6 | `fines/assess-overdue-fine.ts` | Mixing what and how | Fee policy (3-day grace, 25¢/day, $10 cap) interleaved with millisecond arithmetic and id generation (base-36 timestamp + random nonce). | Flag. Fix: named policy values/function; id generation and date math out of the rule. |
| V7 | `fines/fine-payments.port.ts` + `fines/collect-fine.ts` | Leaky abstraction | The port's failure shape is `stripeCode` with Stripe's literal decline codes; the use case switches on them. | Flag. Fix: provider-neutral outcome (declined / insufficient funds / provider unavailable) mapped inside `infra/payments/stripe-fine-payments.ts`. |
| V8 | `fines/waiver-strategy.ts` + `standard-waiver.ts` + `waive-small-fine.ts` | Premature abstraction | `WaiverStrategy` has one implementation, pure in-memory, no I/O to isolate. `waive-small-fine.ts` also hardcodes `new StandardWaiver()`. | Flag as premature (Medium-ish). Fix: fold into the use case until a second policy exists. |
| V9 | `notifications/send-due-reminder.ts` + the three `*-reminder.ts` | Missing abstraction | Three concrete channels with different method names (`deliver`/`text`/`queueLetter`) chosen by `if/else` on `contact_pref_code`; three implementations exist today, no shared interface. | Flag as missing (not speculative). Fix: a reminder-channel interface, selection outside the use case. |
| V10 | `infra/sms/sms-gateway.port.ts` ← `notifications/sms-reminder.ts` | Interface parked on the wrong side | The `SmsGateway` interface lives with its implementer in `infra/`, and the caller in `notifications/` imports it from there. | Flag (Medium). Fix: move the interface to `notifications/`. |
| V11 | `services/payment-service.ts`, `utils/date-utils.ts` | Screaming Architecture | Directories named by technical role with no business concept. | Flag both. `services/payment-service.ts` belongs with fines (refunds); `utils/date-utils.ts` is two wrappers that can live with their callers. |
| V12 | `stripe-sdk` in `services/payment-service.ts` and `reporting/revenue-report.ts` | Invasive Species | High-lock-in SDK imported outside its single adapter (`infra/payments/stripe-fine-payments.ts`); both also read `process.env` directly. | Flag. Fix: one payments port/adapter. |
| V13 | `reporting/report-queries.port.ts` | Wrong abstraction level | The port is `runSql(sql)`; `monthly-circulation-report.ts` and `overdue-report.ts` write SQL. The boundary exists but is drawn at the wrong level. | Flag. Fix: report-shaped query methods on the port. |
| V15 | `lending/return-book.ts` → `main/wiring.ts` | Dependency Rule (business code reaching into the composition root) | The use case imports `loanStore()` from `main/wiring.ts` and calls it in a field initializer. The function returns the interface type and the use case never names `PostgresLoanStore`, which is what the skill's old composition-root exemption keyed on, but the use case now depends on the module that imports every adapter, the ORM and `process.env`, and it is the only use case not given its store by `main/server.ts`. | Flag. Fix: take `LoanStore` through the constructor like `RenewLoan`; only `main/` may import `main/wiring.ts`. The composition-root exemption covers `main/` knowing both sides (T7), not business code knowing `main/`. |
| V14 | `reporting/export-report.ts` | Inconsistent abstraction level | One method orchestrates which report to run and where to write it, and also assembles CSV character by character (BOM, quoting, CRLF). | Flag. Fix: extract CSV formatting. |

## Traps (a good review does NOT flag these as violations)

| # | Where | Principle | Why it looks wrong | Why it isn't |
|---|---|---|---|---|
| T1 | `lending/hold.ts` ↔ `lending/hold-queue.ts` | Type-only cycle | The two files import each other. | Both use `import type`; erased at compile time, `verify.sh` shows `hold.js` loads. Not a runtime or build problem. |
| T3 | `notifications/mailer.port.ts` | YAGNI vs. Dependency Rule | One implementation (`SendgridMailer`). | An interface the Dependency Rule requires is not premature with one implementation; it isolates real I/O. Compare V8, where there is nothing to isolate. |
| T4 | `reporting/report-files.port.ts` | Same as T3 | One implementation (`LocalReportFiles`). | Isolates filesystem I/O. |
| T5 | `fines/money.ts` vs `reporting/rounding.ts` | Documented tradeoff | Two rounding helpers instead of one shared one. | Comment explains: fines round half-up per the board's published fee schedule, reports round half-even for accounting; unifying them caused LIB-2291. Mention as deliberate at most. |
| T6 | `date-fns-lite` in `utils/date-utils.ts`, `members/register-member.ts`, `lending/loan-policy.ts` | Invasive Species tiers | A third-party library used directly in three places. | A date library is lower lock-in; a note at most, not a blocking finding. |
| T7 | `main/server.ts`, `main/wiring.ts` | Screaming Architecture bootstrap exemption | Technical names, framework imports. | Entry and wiring files with no business logic are exempt. |
| T8 | `reporting/report-processor.ts` | Screaming Architecture near-miss | `processor` is on the near-miss list. | Worth a second look, not an automatic violation. |
| T9 | `infra/postgres/postgres-loan-store.ts` | Good Fences, done right | Imports the ORM and defines a row class. | It is the adapter; it maps rows to plain `LoanRecord` and never leaks `LoanRow`. The duplicate `LoanRow` class in `checkout-book.ts` is a consequence of V1, not a problem here. |
| T10 | `catalog/` + `infra/postgres/postgres-catalog-reader.ts` + `infra/http/catalog-routes.ts` | Clean module | Nothing. | Port owned by `catalog/`, adapter maps rows to `Book`, use case pure and wired to a route. Availability is deliberately not catalog's concern (lending counts its own open loans), so the adapter touches only `books`. A review of `catalog/` should report nothing above Low. |

## Known observations that are not architecture findings

A thorough reviewer may also raise these; none is a false alarm and none is
graded: `CollectFine` charges before it settles with no idempotency key;
`RegisterMember` and `CheckoutBook` check-then-write without a transaction;
`LoanStore.add` takes an id the domain never assigns; `main/jobs.ts` is
wired on a timer with no error handling; a fine is assessed once and never
grows; holds are placed but never consulted at checkout; checkout never
checks the member's status; "overdue" is computed in `lending/loan.ts`,
`fines/assess-overdue-fine.ts` and `reporting/overdue-report.ts`
separately. These are product gaps or reliability notes a broad reviewer
will raise, and the blind pairwise judge rewards raising them; they are
not planted, not graded, and not false alarms. Accidental problems a reviewer
found in the first calibration run (nothing decremented `copiesAvailable`,
`OverdueReport` used two clocks, an unvalidated `month` reached a file path,
waiving marked a fine settled, fines/reminders/reports were never wired)
were fixed rather than left as noise.

## Boy Scout scoping (same code, different framing)

`library-app-reporting-pr` frames V14 plus the new `ReportFiles` port (T4) as
a PR against the pre-existing `reporting/` module (V12's revenue report, V13).
Expected: V14 is flagged against the PR; V12/V13 are named as pre-existing and
not blocking; the PR is not asked to rewrite `reporting/`.
`library-app-reporting-review` reviews the same module with no PR framing and
expects V12, V13 and V14 all flagged.

## Also in the persona's spec, graded lightly

The agent prompt says to state the importance ordering being assumed rather
than asserting a universal one. `library-app-lending-review` carries a
half-weight grader for it.
