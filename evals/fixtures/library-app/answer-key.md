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
wired on a timer with no error handling outside the reminder loop; a fine is assessed once and never
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

## Security plants (`S`, `ST`) — `devsecops-engineer:security-review`

Principles come from `skills/security-review/SKILL.md` and
`agents/devsecops-engineer/AGENT.md`. The app is a staff-facing desk
service (`/loans`, `/holds`, `/fines`, staff sessions) plus a member
self-service portal (`/portal`, member sessions). Sessions are issued by an
external sign-in service and looked up by SHA-256 digest
(`infra/postgres/postgres-session-store.ts`); `requireRole` in
`infra/http/sessions.ts` is mounted per prefix in `main/server.ts`.

### Planted violations

| # | Where | Principle | What is wrong | Expected verdict |
|---|---|---|---|---|
| S1 | `infra/http/fines-routes.ts` `POST /charges/:id/refund` | Authentication on new entry points | Matches none of the protected prefixes, so anyone can refund any Stripe charge id. | Critical/High. Fix: staff-only (protected prefix or middleware). |
| S2 | `infra/http/portal-routes.ts` `GET /portal/members/:cardNumber` | Authorization distinct from authentication (IDOR) | Member-authenticated, but returns whichever member the path names: name, email, phone, address. | High/Critical. Fix: use `sessionOf(req).cardNumber` or reject a mismatch. |
| S3 | `infra/http/respond.ts`, fine pay handler in `fines-routes.ts` | Error handling as information disclosure | Catch-alls return `error.message` for every error, so adapter/driver/SDK errors reach callers, including portal members. | Medium. Fix: generic message for unexpected errors, detail server-side. |
| S4 | `main/jobs.ts` `log.error('reminder failed', { member, loan, ... })` | Logging a whole object | Entire `Member` record (PII) written to logs on every failed reminder. | High. Fix: log loan id / member id. |
| S5 | `infra/http/respond.ts` → `infra/monitoring/error-reporter.ts` | Telemetry exit | Every failed request sends `req.headers` (bearer session token) and `req.body` to a third-party monitoring service. | High. Fix: allow-list path, error id, opaque ids. |
| S7 | `infra/postgres/postgres-loan-history.ts` | Injection | `titleContains` (portal `?title=`) interpolated into SQL text next to a bound `$1`. | High/Critical. Fix: bind it as a parameter. |
| S8 | `main/wiring.ts` `mailer()` | Secret in source | Hardcoded SendGrid-style key as `??` fallback. (Deliberately one character off the real key format so secret scanners don't block pushes.) | Critical/High. Fix: secret store, fail fast; rotate the key. |
| S9 | `.github/workflows/deploy.yml` `snapshot` job | Long-lived credential where federation exists | Static AWS access keys, while `deploy` in the same file already uses OIDC. | High. Fix: OIDC with a narrow role; retire the keys. |
| S10 | `.github/workflows/deploy.yml` | Broad-by-default grants | Every runtime secret in workflow-level `env:` (the `test` job needs none and runs `npm ci`); no top-level `permissions:`. | Medium. Fix: per-job secrets, `permissions: contents: read` at top. |
| S11 | `test/fixtures/members.ts` | Real-looking sensitive values in fixtures | Plausible names, gmail/comcast addresses, real-format phone, real-looking Portland addresses. | Medium. Fix: reserved/obviously fake values. |

### Traps

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| ST1 | handlers in `lending-routes.ts`, `/fines/...` in `fines-routes.ts`, `portal-routes.ts` | No auth check in any handler. | `main/server.ts` mounts `requireRole` on `/loans`, `/holds`, `/fines` (staff) and `/portal` (member). The control is one layer up. |
| ST2 | `main/wiring.ts` `stripePublishableKey = 'pk_live_...'` | A live Stripe key in source. | Publishable keys are public by design (browser payment forms) and cannot charge, refund or read. |
| ST3 | `infra/http/catalog-routes.ts` | Unauthenticated route. | Public catalog search over book data only, capped at 50 rows; failures return a generic 503 and report the path and a failure reason, and report only the path to monitoring (the safe counterpart to S5). |
| ST4 | `infra/postgres/postgres-catalog-reader.ts` `search` | `%${escapeLike(terms)}%` looks like interpolation into SQL. | The string is the bound `$1` value; `escapeLike` only neutralises wildcards. |
| ST5 | `deploy.yml` `deploy` job `id-token: write` | Looks like a write permission. | Required for OIDC, scoped to one job, grants no repository write. |
| ST6 | `/portal/loans`, `/portal/history` | Portal routes returning per-member data. | Both take the card number from the session, not the request. |
| ST7 | `main/jobs.ts` `log.info('reminder sent', { loanId, channel })` | A log line in a PII-heavy loop. | Opaque id and channel code only: the "log the identifier" pattern. |

`catalog/` remains the clean module for security too (ST3, ST4): a review
of it should report nothing above Low.

Ungraded but not false alarms: env-var secrets in `main/wiring.ts`
generally (the skill prefers a managed store); the AWS account id in the
deploy role ARN; card numbers interpolated into exception messages that
reach the `reminder failed` log; `PlaceHold` and checkout taking the card
number from the body (staff-only routes); no rate limiting on portal
routes (public search has one); no lockfile (a `supply-chain-review` concern).

## Reliability plants (`R`, `RT`) — `devsecops-engineer:reliability-review`

Principles come from `skills/reliability-review/SKILL.md`. Most rows were
already in the app as "known observations" for the architecture and
security suites; for reliability they are graded. Vendor SDKs document
their timeout knobs in `types/vendor.d.ts` (`timeoutMs`, no default, waits
indefinitely; `queryTimeoutMs` on `PgClientOptions`; `PgClient.end()`
closes a pool). `ops/runbooks/catalog-search.md` states the catalog's
scale (about 60,000 titles, 40 ms p95), the fact a speed concern about
search has to be judged against. The service targets Node 24, where an unhandled promise
rejection terminates the process.

### Planted violations

| # | Where | Principle | What is wrong | Expected verdict |
|---|---|---|---|---|
| R1 | `main/server.ts` `setInterval(() => { void runNightly(); }, ...)` | Every call that can fail has a defined outcome | `runNightly` has no top-level catch, and `void` discards its promise, so any throw outside the reminder loop (a `findOpen` or fine-insert failure, a report write) is an unhandled rejection: Node 24 terminates the process, taking the HTTP server with it, and nothing reaches the app logger or monitoring. | Critical/High. Fix: catch at the job boundary, log and report the failure, keep the server alive (ideally run the job outside the web process). |
| R2 | `main/jobs.ts` fine-assessment loop | Partial completion / failure isolation | `await assess.run(loan)` per overdue loan with no per-item handling: one failure abandons the remaining assessments, every reminder and the monthly reports for that night. | High. Fix: per-loan try/catch that logs the loan id and continues; summarise failures at the end. |
| R3 | `infra/postgres/postgres-member-directory.ts` via `main/wiring.ts` `memberDirectory()` | Resource lifecycle | Each `PostgresMemberDirectory` opens its own `PgClient` pool and nothing calls `end()`; `runNightly` calls `wiring.memberDirectory()` on every run, so one more pool leaks per night until Postgres runs out of connections. | High/Critical (a leak that will exhaust something). Fix: share `wiring.pgClient()` as every other adapter does, or end the pool. |
| R4 | `infra/email/sendgrid-mailer.ts` | Slow is a failure mode; timeouts | `new MailClient(apiKey)` with no `timeoutMs` (the SDK waits indefinitely), called serially from the nightly reminder loop: one hung request stalls every reminder after it and the monthly reports, with nothing logged. The SMS adapter sets 5 s. | High. Fix: set `timeoutMs`. |
| R5 | `infra/postal/file-postal-queue.ts` | Errors aren't swallowed | A failed `appendFile` is logged at `info` and the method resolves, so `SendDueReminder` succeeds and `main/jobs.ts` logs `reminder sent` for a letter that was never queued. | High/Medium. Fix: let the error propagate to the job's per-reminder catch. |
| R6 | `fines/collect-fine.ts` | Partial completion leaves defined state | Charges, then settles in a separate step with no idempotency key: if `ledger.settle` fails (or the process dies) after a successful charge, the member has paid and the fine stays outstanding; paying again charges the card again. | Critical/High. Fix: idempotency key derived from the fine id on the charge, record the attempt before charging, reconcile. |
| R7 | `fines/collect-fine.ts` retry loop | Retry only what is transient; resilience in the adapter | Re-charges up to three times on any `!ok` outcome, which are the provider's deterministic answers (declined, expired, insufficient funds); the transient failures (network errors, timeouts) are thrown by the adapter and not retried. The loop also lives in the use case. | High. Fix: no retry on declines; any transient retry belongs in `StripeFinePayments`, with backoff and an idempotency key. |
| R8 | `infra/http/fines-routes.ts` `POST /fines/:id/pay` | Expected vs unexpected; diagnosability | Every error becomes 402 and nothing is logged or reported: a database or payment-provider outage reads as a declined card at the desk and is invisible to whoever maintains the service. | High/Medium. Fix: map expected payment outcomes to 402; report unexpected errors and answer 5xx. |
| R9 | `infra/http/respond.ts` | Expected vs unexpected failures | Every thrown error answers 400 and is sent to monitoring: routine refusals (no copy available, loan limit, cannot renew, member not found) and genuine faults (database down) are indistinguishable to callers and to monitoring. | Medium/High. Fix: typed expected errors answer 4xx unreported; anything else answers 5xx and is reported. |
| R10 | `infra/postgres/postgres-loan-history.ts` `forCard` | Performance as correctness (unbounded result) | No limit or pagination; a member's history only grows and `GET /portal/history` returns all of it. | Medium/High. Fix: limit and paginate. |
| R11 | `infra/memory/in-memory-hold-queue.ts` (wired as a singleton in `main/wiring.ts`) | Resource lifecycle; state that must survive | Holds exist only in process memory: every deploy, restart or crash (R1) silently drops every hold, and nothing ever removes one, so the map only grows. | High. Fix: persist holds behind the existing `HoldQueue` port. |
| R12 | `ops/alerts.yml` `request-errors` | Alert fatigue | Pages on any error event in five minutes; since `respond.ts` reports every refusal (R9), routine validation failures page on-call. | High/Medium. Fix: alert on the rate of unexpected errors against a target; ticket rather than page below it. |
| R13 | `ops/alerts.yml` `high-cpu` | Actionable alerts | Pages on CPU above 70% with no objective, no user-facing symptom and no runbook: nobody can say what to do when it fires. | Medium. Fix: drop it, or tie it to a symptom and make it a ticket. |

### Traps

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| RT1 | `main/jobs.ts` reminder loop `catch` | Catches and continues. | Logs at `error` with the reason and isolates one member's failure from the rest: the right pattern (its PII problem is S4, a security finding). |
| RT2 | `fines/assess-overdue-fine.ts` on a re-run | The nightly job may run twice. | `alreadyAssessed` skips a loan that already has an outstanding fine, so a sequential re-run does not double-fine. Two *overlapping* runs could both pass the check before either inserts (no unique constraint); that race is a valid finding, not a false alarm. |
| RT3 | `infra/sms/twilio-sms-gateway.ts` | A retry loop. | Retries only 408/429/5xx, backs off exponentially, stops at three attempts, sets a 5 s timeout, and lives in the adapter. A duplicate text after a timed-out-but-delivered send is a Low note at most. |
| RT4 | `fines/collect-fine.ts` early `return` | Returns silently for a settled or waived fine. | Idempotent guard: paying a settled fine is a no-op, not a failure. |
| RT5 | `infra/http/catalog-routes.ts` | Catches everything. | Answers 503 with a generic message and reports the path: a dependency failure is visible and distinguishable. |
| RT6 | `catalog/search-catalog.ts` | Search over the whole catalog. | Capped at 50 rows. |
| RT7 | `ops/alerts.yml` catalog-search burn alerts | Two alerts for one route. | Multi-window error-budget burn against the stated 99.5% objective, page for the fast burn and ticket for the slow one, both with a runbook. |
| RT9 | `main/wiring.ts` `publicSearchClient()`, `rateLimit` on `/books` in `main/server.ts` | A second connection pool, and an unauthenticated route. | The bulkhead done right: public search gets its own memoized 4-connection pool with a 2 s timeout, connecting as a separate `catalog_reader` role, so a slow database or a search burst exhausts only search, never the 20-connection pool that session checks, checkout and fines share; search is also rate-limited per client. Contrast R3, where a pool is created per call and never closed. |
| RT8 | Every `PgClient` | Database calls with no visible timeout. | `pgOptions()` sets `queryTimeoutMs: 10_000` (client-side, covering the wait for a connection), and every client, including the member directory's, is built from it. |

`catalog/` remains the clean module for reliability (RT5, RT6, RT8): a
review of it should report nothing above Low.

Ungraded but not false alarms: the nightly loops issue a query per loan
(`outstandingFor`, `findByCard`); `findOpen()` loads every open loan;
`setInterval` schedules from process start, so a restart moves or skips
the nightly run and the day-1 report; `CheckoutBook` and `RegisterMember`
check-then-write without a transaction, and so does `AssessOverdueFine` across overlapping runs; loan updates are read-modify-write with no version check; the catalog's leading-wildcard `ILIKE` cannot use a plain index, (a speed note; at the stated scale, Low at most); no correlation id ties a request's
log, monitoring and database records together; no alert covers the nightly
job or fine payments; report files are written non-atomically.

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
