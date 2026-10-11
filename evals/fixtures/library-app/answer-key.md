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
routes (public search has one); the image build ignoring the lockfile (`SC2`, a `supply-chain-review` concern).

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

## Supply-chain plants (`SC`, `SCT`) — `devsecops-engineer:supply-chain-review`

Principles come from `skills/supply-chain-review/SKILL.md`. The question it
answers: if an upstream package, registry or maintainer account were
compromised right now, would the next build pull the bad version? The
production path is: CI `deploy` job runs `npm ci` and `tsc`, builds the
`Dockerfile`, pushes the image tagged with the commit SHA, and
`ops/release.sh` rolls the ECS service onto it. Packages are fictional;
`package-lock.json` is lockfileVersion 3 with an `integrity` hash per
package.

### Planted violations

| # | Where | Principle | What is wrong | Expected verdict |
|---|---|---|---|---|
| SC1 | `Dockerfile` `FROM node:22-slim` | Base images pinned by digest | A mutable tag on the image that runs in production; `dependabot.yml`'s docker entry updates tags, it does not pin. | High. Fix: pin `node:22-slim@sha256:...`; let Dependabot bump the digest. |
| SC2 | `Dockerfile` `COPY package.json` + `RUN npm install --omit=dev` | Frozen installs on the production path | The image build copies only the manifest and runs `npm install`, so it resolves every caret range fresh at build time: the lockfile CI tested against never reaches production. | Critical/High (nothing pins on the path that reaches production). Fix: copy `package-lock.json` and run `npm ci --omit=dev`. |
| SC3 | `native-phone-codec` (`hasInstallScript: true` in `package-lock.json`, transitive via `sms-sdk`); no `.npmrc` | Install-time code execution | npm runs lifecycle scripts by default; one transitive dependency has an install script, and it runs in CI's `npm ci` (with every workflow secret in `env`) and in the image build. | Medium. Fix: `ignore-scripts=true` with a narrow allowlist (or rebuild only the packages that need it). |
| SC4 | `.github/workflows/deploy.yml` `slackapi/slack-github-action@v1.27.0` | CI workflow references pinned to a full SHA | A third-party action referenced by tag, running in the `deploy` job after AWS credentials are configured and with every workflow secret in `env`. | High. Fix: pin to the commit SHA with the version as a comment, as the other actions are. |
| SC5 | `.github/workflows/release-notes.yml` `changelog-tools/release-notes-action@main` | Same | A branch reference, the most mutable kind, in a workflow with `contents: write`. | High. Fix: pin to a SHA. |
| SC6 | `audit-ci.jsonc` `GHSA-9xj7-p3hc-r5mw` | Accepted findings need a classification and a reason | A bare allowlist entry: nobody can tell later whether it was a false positive, mitigated, or an accepted risk. | Medium. Fix: name the classification and the reason, or remove it and triage; the user picks the classification. |
| SC7 | `audit-ci.jsonc` `GHSA-hq6c-2f8v-7wxp` "Accepted until 2026-12-01, revisit then" | Temporary acceptance needs an enforced expiry | audit-ci's allowlist has no expiry; nothing will surface the entry on that date, so it is a permanent acceptance that reads as a temporary one. | Medium (the advisory itself is dev-only, Low). Fix: record it as a plain accepted risk with its reason, or use a mechanism that actually expires. |
| SC8 | `stack-symbolicate` (AGPL-3.0-only in `package-lock.json`, transitive via `monitor-sdk`) | License risk | A strong-copyleft license arriving through a dependency nobody chose, in a network service. | Medium: a decision for whoever owns licensing, not a verdict the reviewer makes. Fix: decide, and record it; or replace the dependency. |

### Traps

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| SCT1 | `package.json` caret ranges | Version ranges in the manifest. | `package-lock.json` is committed with integrity hashes and CI installs with `npm ci`: the lockfile is the anchor there. The manifest's ranges only matter where something installs without it (SC2). |
| SCT2 | `.github/dependabot.yml` | An update bot that changes dependencies. | Update automation is fine and covers npm, docker and actions; it simply is not pinning (see SC1). |
| SCT3 | `actions/checkout`, `actions/setup-node`, `aws-actions/configure-aws-credentials` | Third-party code in CI. | Each is pinned to a full commit SHA with the version as a comment. |
| SCT4 | `audit-ci.jsonc` `GHSA-4w2q-8m3v-c9rf` | An allowlisted advisory. | Classified ("Not vulnerable, mitigated by design") with a reason someone can check: the service never calls `parse()`. |
| SCT5 | `GHSA-hq6c-2f8v-7wxp` itself | An advisory in TypeScript. | Dev-only (the language service, never in the image): Low on reachability. The finding is how it was accepted (SC7), not the advisory. |

## Operational-readiness plants (`OR`, `ORT`) — `devsecops-engineer:operational-readiness`

Principles come from `skills/operational-readiness/SKILL.md`. Every case is
phase-chained: the skill must establish the situation before judging, so
phase 1 grades the question and phase 2 resumes it with this answer
(scripted in each phase-2 case): two staff desks at one branch plus a
member portal used by about 3,000 members; if it is down, desks fall back
to paper slips and members cannot renew online; the one developer finds out
from a staff phone call or a page; nobody has ever rolled a release back.

### Planted violations

| # | Where | Principle | What is wrong | Expected verdict |
|---|---|---|---|---|
| OR1 | `.github/workflows/deploy.yml` deploy job, `ops/release.sh` | Something confirms the deploy actually worked | `release.sh` returns as soon as `update-service` accepts the new task definition; the job then posts "deployed" to Slack. Nothing waits for the service to stabilise or checks a health endpoint. | High. Fix: wait for the service to stabilise (`aws ecs wait services-stable`) and check a health signal before announcing. |
| OR2 | `ops/migrations/0012_fines_charge_id.sql` run by `ops/migrate.sh` in the same deploy job, before the release | What can't be rolled back; data change separable from code change | Copies `stripe_charge_id` into `charge_id` and drops the old column, then ships the code that uses `charge_id`. Rolling the image back to the previous release breaks settling fines (its column is gone), and a failed release after the migration leaves the old code running against the new schema. | Critical/High. Fix: expand/contract — add and backfill now, drop the old column in a later release once rollback past this one is no longer needed; keep the migration separable from the code release. |
| OR3 | Rollback path (SHA-tagged images, `release.sh <previous image>`) | Rollback is a tested capability | A path exists, but by the user's answer nobody has ever run it. | High. Fix: rehearse a rollback (to a staging service or in a quiet window) and write down how long it took. |
| OR4 | `main/jobs.ts` nightly run vs `ops/alerts.yml` | First signal doesn't depend on a user | No alert covers the nightly job; a run that dies or skips is noticed when members complain about missing reminders or wrong fines. | Medium/High. Fix: a heartbeat or completion signal for the nightly run, alerted when missing. |
| OR5 | `main/wiring.ts` `env.MONITOR_DSN ?? ''`, `env.STRIPE_SECRET_KEY ?? ''`, `env.TWILIO_* ?? ''` | Startup fails loudly on missing configuration | A missing `MONITOR_DSN` silently turns error reporting off (`monitor-sdk` treats an empty DSN as "disabled"); a missing Stripe or Twilio key starts the service and fails at the first payment or text. Required variables are listed nowhere. | High (monitoring off with nobody knowing) / Medium. Fix: validate required configuration at startup and exit if absent; list the variables. |
| OR6 | `ops/` | What someone needs at 2am | One runbook (catalog search). Nothing says which version is running and where its logs are, what the service depends on (Postgres, Stripe, SendGrid, Twilio, the postal queue file, monitoring) and what happens when each is down, or that 0012 is irreversible. | Medium. Fix: a short operations note next to the code covering those. |

### Traps

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| ORT1 | SHA-tagged images + `ops/release.sh` | "No rollback" is the reflex claim. | Every image is tagged with its commit SHA and `release.sh <image>` rolls the service onto any of them: the path exists. The finding is that it has never been exercised (OR3), and that 0012 breaks it (OR2). |
| ORT2 | The situation itself | Production service, real users. | Two desks, one developer: on-call rotations, severity matrices, incident-commander roles or post-mortem templates are ceremony this situation does not warrant. |
| ORT3 | `deploy.yml` `snapshot` job | — | A nightly RDS snapshot exists: data can be restored to the previous night (its long-lived keys are a security finding, S9, not a readiness one). |

## Requirements plants (`SR`, `SRT`, `RR`, `RRT`) — `devsecops-engineer:security-requirements`, `reliability-requirements`

Both skills write acceptance criteria for a slice that is not built yet:
**a member pays an outstanding fine from the portal** (thin path and
functional criteria in each case's prompt). Nothing is planted for them:
the "plants" are what the existing code means for that slice, which the
criteria must cover. Each chain has three phases: phase 1 must ask only
what the repository cannot answer; phase 2 answers (members are
individuals, about 3,000, one developer, Stripe's terms only, an hour down
means paying at the desk) and must write criteria and present the
engineer's proposal in the prompt as a decision; phase 3 rejects the
recommendation and must write the user's choice in, made safe or
workable.

### Security (`SR`, `SRT`)

| # | Where | Principle | What the slice must handle | Expected criterion |
|---|---|---|---|---|
| SR1 | `fines/fine-ledger.port.ts` `find(id)`, `POST /fines/:id/pay` | Authorization distinct from authentication | Every `Fine` carries `cardNumber`, but `find` returns any fine by id and the pay route checks no ownership (the portal's `GET /portal/members/:cardNumber`, S2, is the same mistake). | A member views and pays only their own fines; another member's fine id is refused without revealing it. |
| SR2 | `GET /payments/config`, `cardToken` in the pay route | Prefer absence over careful handling | The card is tokenised in the browser; the server sees a token. | The application never receives, stores or logs a card number or security code. |
| SR3 | `infra/http/respond.ts`; the 402 in `POST /fines/:id/pay` | The five exits | A route on `respond` returns `error.message` and sends the session token (headers) and card token (body) to the error reporter (S3, S5). | Error responses, error reports and logs carry none of the slice's sensitive data. |
| SR4 | the engineer's proposal; `requireRole('staff')` on `/fines` in `main/server.ts` | A real fork is presented, not decided | Allowing members on `/fines` also opens `POST /fines/:id/waive` and keeps the unscoped pay route. | Phase 2: presented with a recommendation and alternatives, left for approval. Phase 3 (user keeps the shared route): criteria that members pay only their own fines and cannot waive; decision recorded with its risk. |

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| SRT1 | `stripePublishableKey` (`pk_live_...`) served by `/payments/config` | A live key sent to the browser. | Publishable keys are public by design and cannot charge, refund or read (ST2). |
| SRT2 | Phase 1 questions | Asking how members sign in or which payment provider is used looks diligent. | The code answers both (`requireRole`, `sessionOf`, the Stripe adapter); the skill asks only what it cannot read. |

### Reliability (`RR`, `RRT`)

| # | Where | Principle | What the slice must handle | Expected criterion |
|---|---|---|---|---|
| RR1 | `fines/collect-fine.ts` charge, then `ledger.settle` | The operation is interrupted partway | A charge that succeeds before a failed settle leaves a paid fine outstanding (R6). | A charge without a settled fine is visible to the developer with the fine and charge to reconcile; while duplicates are prevented (phase-2 framing), it is also never charged again. |
| RR2 | `CollectFine` early return | The same thing happens twice | The guard only works once the fine is settled; two overlapping submissions both charge. | Double or concurrent submission is covered: at most one charge, or named within the duplicate risk the user accepts in phase 3. |
| RR3 | `POST /fines/:id/pay` 402 for every error | Expected vs unexpected failures | Declines and outages look the same and nothing is reported (R8). | Declines tell the member what to do; faults are visible to the developer and not shown as a decline. |
| RR4 | the engineer's proposal (fail after 10 s) | A real fork is presented, not decided; a dependency is slow | After a timeout the charge may have succeeded; "failed, try again" invites a duplicate. | Phase 2: the duplicate risk named and its handling left as a decision, framed either as what the member is told or as making a retry safe (one charge per fine) versus refunding duplicates by hand. Phase 3 (user keeps "show failed" and refunds by hand): criteria for that, plus duplicates findable for the refund; decision recorded with its risk. |

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| RRT1 | `CollectFine` retry loop | Retrying a failed payment looks resilient. | Declines are deterministic answers; criteria must not call for retrying them (R7). |
| RRT2 | Phase 1 questions | Asking whether any error reporting exists looks diligent. | `infra/monitoring/error-reporter.ts` and `ops/alerts.yml` answer it. |

## Design plants (`AD`, `ADT`) — `software-architect:architecture-design`

The same pay-a-fine slice, at the stage before its design exists
(`planning/pay-fine-design/`, copied into `docs/pay-fine/`). Nothing is
planted for it; these are what the existing code means for the design.
The prompt carries the engineer's proposal of a generic `PaymentGateway`
with a provider registry. Phase 1 must recommend against it and wait;
phase 2's answer overrules that (a second provider is signed for next
quarter, so the abstraction has a real second case) and approves the rest.

| # | Where | Principle | What the design must handle | Expected |
|---|---|---|---|---|
| AD1 | the engineer's proposal | YAGNI, premature abstraction; approval loop | One provider, and `FinePayments` already isolates Stripe. | Phase 1: presented as a decision, recommended against, left for approval. Phase 2: built as approved, owned by the fines side, Stripe behind it, not re-argued. |
| AD2 | `CollectFine`, `FineLedger`/`FinePayments`, the portal's session pattern | Check what already exists | The slice's pieces mostly exist. | The design builds on them (a member-facing step that checks ownership and delegates to `CollectFine`), not a parallel payment path. |
| AD3 | `fines/fine-payments.port.ts` `stripeCode` (V7) | Leaky abstraction; existing violations touched | The port speaks Stripe's decline vocabulary; a second provider makes it untenable. | Listed under existing violations touched, with fix-now-or-defer recorded as an approved decision. |

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| ADT1 | `FinePayments`, one implementation | A one-implementation interface looks premature. | It is the interface the Dependency Rule requires to keep the Stripe SDK out of the fines module (compare T3, V8). Generalising it is fine; calling it premature is not. |

## Docs plants (`D`, `DT`) — `docs-writer:why-comments`, `staleness-audit`

These live outside `app/`, in `docs-plants/`, and only the case that uses
them copies them in: `why-comments/fines/collect-fine.ts` replaces the app's
file (same code, comments added), `staleness/docs/` becomes the run's
`docs/`. No other case sees them.

| # | Where | Violation | Expected |
|---|---|---|---|
| D1 | `fines/collect-fine.ts` "Look up the fine.", "Throw if there is no fine." | WHAT comments: the next line already says it. | Delete. |
| D2 | `fines/collect-fine.ts` "Charge once; Stripe retries failed charges on its side." | Contradicts the loop under it, which charges up to three times. | Delete or rewrite to match; flagged as wrong, not just redundant. |
| D3 | `docs/lending-rules.md` | Stale: 14-day loans, 3 renewals, renewal adds to the due date. The code has 21 days, 2 renewals, and the new due date is 21 days from the renewal day. | Update to the code or delete. |
| D4 | `docs/collect-fine.md` | Restates `CollectFine.run` line by line. | Delete. |
| D5 | `docs/release-signoff.md` | Ceremonial: every row the same person and a tick, nothing a reader could act on. | Delete; no replacement process. |
| D6 | `docs/adr/adr-002-reminders-email-only.md` | Orphaned decision: Accepted, but `notifications/` sends SMS and postal reminders. | Supersede (or mark superseded), not edit in place. |

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| DT1 | `fines/collect-fine.ts` "Return quietly instead of throwing: the desk screen resubmits..." | A long comment on a one-line guard. | It records a caller behaviour the code can't show. Keep. |
| DT2 | `docs/fines.md` | Describes a rule the code also implements. | It records why (processing fees, the only-fine condition), which the code doesn't say. Keep. |
| DT3 | `docs/adr/adr-001-stripe-for-card-payments.md` | An old ADR. | Still true: payments go through Stripe with tokenised cards. Keep. |

## Test-quality plants (`Q`, `QT`) and build cases — `tdd-coach`

Like the docs plants, these live outside `app/` so no other case sees
them: `code-plants/tdd/` (a `package.json` whose `test` script runs the
TypeScript tests in place through `test/ts-resolve.mjs`, plus an approved
design doc) and `code-plants/test-quality/fines/` (a planted
`test/fines.test.ts` and its fake). Every planted test passes; that is
the point.

| # | Where | Violation | Expected |
|---|---|---|---|
| Q1 | `test/fines.test.ts` 'returns the assessed fine' | Replaces `AssessOverdueFine.run` on the subject itself, then asserts the stub's own return value. Can't fail. | The most serious finding. Fix: call the real `run` and assert the fine it returns. |
| Q2 | 'does not charge inside the grace period' | `record = mock.fn()` is never wired to the ledger; `callCount() === 0` holds whatever the code does. | Flag the unwired mock. Fix: assert `ledger.recorded` is empty (and the result is null). |
| Q3 | 'caps the fine at ten dollars' | `amountCents > 0` passes for an uncapped fine too. | Flag as a weak assertion. Fix: assert exactly 1000. |
| Q4 | 'looks up outstanding fines before recording a new one' | Asserts the order of two ledger calls, not an outcome; a refactor that kept the behaviour (one query by loan id) breaks it. | Flag as implementation detail. Fix: drop it; 'does not assess a loan that already has an outstanding fine' covers the behaviour. |
| Q5 | `fines/money.ts` `percentOf` | Exported, imported module, no test. (The not-yet-due branch, `daysLate <= 0`, is also untested; flagging it is correct too.) | Flag missing coverage. |

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| QT1 | `FakeFineLedger`, and `mock.method(ledger, 'outstandingFor', ...)` in 'does not assess a loan that already has an outstanding fine' | Mocking. | A designated fake for an external port, stubbed per test; the subject runs for real. |
| QT2 | 'charges 25 cents a day...', the three `isOutstanding` tests, 'rounds half a cent up' | Nothing. | Exact assertions on real behaviour. |
| QT3 | `test/send-due-reminder.test.ts` inline gateways passed to the constructors | Hand-rolled doubles. | Constructor-injected fakes that capture what was sent. Its real gap is coverage: the email channel (and the missing-phone/address throws) are untested. |

Build cases (`tdd-implementation-*`), graded on the trace and the files written:

- `cancel-hold`: the design in `docs/cancel-hold/design.md`. Expected: CancelHold with its queue injected, a removal operation on the `HoldQueue` port and in `InMemoryHoldQueue`, plain-data result, nothing else touched (`place-hold.ts` carries V3 and `loan.ts` V2; both stay). The prompt's question 1 (renumber positions, notify the next member) is load-bearing: escalate, don't build. Question 2 (reason wording) is decide-and-note.
- `named-fix`: V15 handed back as a review finding. Expected: `LoanStore` through the constructor, `main/server.ts` updated, behaviour unchanged, ReturnBook's behaviour pinned by tests (none existed; `return-book.ts` can't load under test before the fix because `main/wiring.ts` imports the fictional vendor packages), nothing else in `lending/` touched.

## Readability plants (`C`, `CT`) — `code-reviewer:code-review`

Case-only overlays in `code-plants/code-review/`, each a PR of new files.

| # | Where | Violation | Expected |
|---|---|---|---|
| C1 | `fine-notices`: `emailFineNotice`/`smsFineNotice`/`letterFineNotice` | The same four lines (filter outstanding, empty check, format amount, count phrase) three times. | A real finding; extract the shared part. |
| C2 | `fine-notices`: comment above `countOutstanding` | "Amounts are in whole dollars"; the value is cents. | Among the most serious: actively misleading. Correct or delete. |
| C3 | `fine-notices`: `countOutstanding` | Says count, returns a cents total. | Wrong name, ranked above the merely vague `build`. Rename (`totalOutstandingCents`). |
| C4 | `fine-notices`: "Check the member's contact preference." in `build` | WHAT comment. | Delete. |
| C5 | `fine-notices`: `test/fine-notice.test.ts` | Both tests named `'works'`. | Rename to say what each checks. |
| C6 | `fines-report`: `FinesReport.run` | Validates, queries, filters, de-duplicates, calls Stripe, totals, logs, assembles. | Split into named steps. |
| C7 | `fines-report`: `FineChaseList.shouldChase` | One check on its own `minimumCents`, four rules about the member (active, not expired, reachable on the preferred channel); `members/member.ts` already has `isActive`. | Feature envy; move the member checks next to the member (reuse or extend `isActive`). An earlier plant, a formatter reading member fields, was dropped: formatting another object's data is a formatter's job, and reviews rightly passed it. |
| C8 | `fines-report`: `fromYear, fromMonth, toYear, toMonth` | Data clump across three signatures; `runFinesReportForPeriod` takes seven parameters. | One period object. |
| C9 | `fines-report`: the reporting month | A `YYYY-MM` string checked by regex, split to numbers, rebuilt from numbers elsewhere. | Primitive obsession; one owner for "month". |

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| CT1 | `fine-notices`: `if (owed.length === 0) return null;` in all three | Repeated. | A one-line guard; not a duplication finding of its own. |
| CT2 | `fine-notices`: the "within 14 days" comment in `letterFineNotice` | A long comment. | Records the fee-schedule rule the code can't show. Keep. |
| CT3 | `fine-notices`: the second `'works'` test | Mocks `build` and asserts the mock ran. | A test-quality problem (it never runs real code), for `test-quality-review`, not a readability finding. Its name is C5. |
| CT4 | `fines-report`: `StripeClient` built from `process.env` inside `FinesReport` | An SDK in a report (V12's pattern). | Structural: named for `architecture-review`, not ranked as readability. |
| CT5 | `catalog/` | Nothing. | The clean module (T10); nothing above Low. |

## Accessibility plants (`A`, `AT`) — `accessibility-engineer:accessibility-review`

Case-only overlay in `ui-plants/accessibility-review/`: one mockup,
`visual-ux/pay-fine-declined.html`, the declined-payment state of the
pay-a-fine slice (`ui-plants/pay-fine/slice-001.md`, which adds the
accessibility placeholder the original slice lacks). Every other colour
pair clears its threshold and every target is at least 44px high, so
nothing else on the page should be a finding.

| # | Where | Violation | Expected |
|---|---|---|---|
| A1 | `.fine-card` `<div onclick="selectFine(...)">` | No role, tabindex or key handling: keyboard and screen-reader users can't choose which fine to pay. | The most severe finding (no accessible path to a required action). Fix keeps the choice: a radio group (the design system's choosable Card) or buttons. |
| A2 | `.notice` (declined) | No `role="alert"`/`role="status"`/`aria-live`. | A finding now; whether it announces is deferred. |
| A3 | `.fine-meta` | `--text-subtle` `#777777` on `#FFFFFF` at 14px: 4.48:1, under 4.5:1. The value sits behind a custom property. | High. Darker token. |
| A4 | "Name on card" input | Placeholder only; no label. | High. A real `<label>`. |

| # | Where | Why it looks wrong | Why it isn't |
|---|---|---|---|
| AT1 | `:focus-visible` rule | One global rule rather than per component. | 3px `#B35C00` outline, 4.72:1 on white and 4.42:1 on the page: visible on every focusable element. The fine cards' lack of focus is A1, not this. |
| AT2 | Warning icon in the notice | An `<svg>` with no alt text. | `aria-hidden="true"`, decorative, next to a heading saying the same. |
| AT3 | Card number input | No `<label for>`. | `aria-labelledby="card-label"` names it "Card number". A Low note about using `<label>` is fine. |

`ui-plants/design-system/` is the binding design system `screen-design-payfine`
composes against; it has no plants.

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
