# Architecture map — updated 2026-09-28

## Modules
| Path | Tier | Internal edges (imports) | External packages | Public exports |
|---|---|---|---|---|
| catalog/book.ts | tier 1 | none | none | Book |
| catalog/catalog-reader.port.ts | tier 1 | catalog/book.ts | none | CatalogReader, CatalogUnavailable |
| catalog/search-catalog.ts | tier 1 | catalog/book.ts, catalog/catalog-reader.port.ts | none | SearchCatalog |
| fines/assess-overdue-fine.ts | tier 1 | fines/fine-ledger.port.ts, fines/fine.ts, lending/loan.ts | none | AssessOverdueFine |
| fines/collect-fine.ts | tier 1 | fines/fine-ledger.port.ts, fines/fine-payments.port.ts | none | CollectFine |
| fines/fine-ledger.port.ts | tier 1 | fines/fine.ts | none | FineLedger |
| fines/fine-payments.port.ts | tier 1 | none | none | StripeDeclineCode, PaymentOutcome, FinePayments |
| fines/fine.ts | tier 1 | none | none | Fine, isOutstanding |
| fines/money.ts | tier 1 | none | none | roundHalfUpCents, percentOf |
| fines/standard-waiver.ts | tier 1 | fines/fine.ts, fines/waiver-strategy.ts | none | StandardWaiver |
| fines/waive-small-fine.ts | tier 1 | fines/fine-ledger.port.ts, fines/standard-waiver.ts, fines/waiver-strategy.ts | none | WaiveSmallFine |
| fines/waiver-strategy.ts | tier 1 | fines/fine.ts | none | WaiverStrategy |
| infra/email/sendgrid-mailer.ts | tier 3 | notifications/mailer.port.ts | mail-sdk | SendgridMailer |
| infra/files/local-report-files.ts | tier 3 | reporting/report-files.port.ts | node:fs, node:path | LocalReportFiles |
| infra/http/catalog-routes.ts | tier 3 | catalog/catalog-reader.port.ts, catalog/search-catalog.ts, infra/monitoring/error-reporter.ts | express-lite | registerCatalogRoutes |
| infra/http/fines-routes.ts | tier 3 | fines/collect-fine.ts, fines/waive-small-fine.ts, infra/http/respond.ts, services/payment-service.ts | express-lite | FineUseCases, registerFineRoutes |
| infra/http/lending-routes.ts | tier 3 | infra/http/respond.ts, lending/checkout-book.ts, lending/place-hold.ts, lending/renew-loan.ts, lending/return-book.ts | express-lite | LendingUseCases, registerLendingRoutes |
| infra/http/portal-routes.ts | tier 3 | infra/http/respond.ts, infra/http/sessions.ts, lending/loan-history.port.ts, lending/loan-store.port.ts, members/member-directory.port.ts | express-lite | PortalReaders, registerPortalRoutes |
| infra/http/respond.ts | tier 3 | infra/monitoring/error-reporter.ts | express-lite | Respond, createResponder |
| infra/http/sessions.ts | tier 3 | none | express-lite | Role, Session, SessionStore, requireRole, sessionOf |
| infra/logging/logger.ts | tier 3 | none | none | log |
| infra/memory/in-memory-hold-queue.ts | tier 3 | lending/hold-queue.ts, lending/hold.ts | none | InMemoryHoldQueue |
| infra/monitoring/error-reporter.ts | tier 3 | none | monitor-sdk | ErrorReporter, MonitorErrorReporter |
| infra/payments/stripe-fine-payments.ts | tier 3 | fines/fine-payments.port.ts | stripe-sdk | StripeFinePayments |
| infra/postal/file-postal-queue.ts | tier 3 | infra/logging/logger.ts, notifications/postal-queue.port.ts | node:fs | FilePostalQueue |
| infra/postgres/postgres-catalog-reader.ts | tier 3 | catalog/book.ts, catalog/catalog-reader.port.ts | pg-orm | PostgresCatalogReader |
| infra/postgres/postgres-fine-ledger.ts | tier 3 | fines/fine-ledger.port.ts, fines/fine.ts | pg-orm | PostgresFineLedger |
| infra/postgres/postgres-loan-history.ts | tier 3 | lending/loan-history.port.ts | pg-orm | PostgresLoanHistory |
| infra/postgres/postgres-loan-store.ts | tier 3 | lending/loan-store.port.ts, lending/loan.ts | pg-orm | PostgresLoanStore |
| infra/postgres/postgres-member-directory.ts | tier 3 | members/member-directory.port.ts, members/member.ts | pg-orm | PostgresMemberDirectory |
| infra/postgres/postgres-report-queries.ts | tier 3 | reporting/report-queries.port.ts | pg-orm | PostgresReportQueries |
| infra/postgres/postgres-session-store.ts | tier 3 | infra/http/sessions.ts | node:crypto, pg-orm | PostgresSessionStore |
| infra/sms/sms-gateway.port.ts | tier 3 | none | none | SmsGateway |
| infra/sms/twilio-sms-gateway.ts | tier 3 | infra/sms/sms-gateway.port.ts | sms-sdk | TwilioSmsGateway |
| lending/checkout-book.ts | tier 1 | catalog/catalog-reader.port.ts, lending/loan.ts | pg-orm | CheckoutBook |
| lending/hold-queue.ts | tier 1 | lending/hold.ts | none | HoldQueue |
| lending/hold.ts | tier 1 | lending/hold-queue.ts | none | Hold |
| lending/loan-history.port.ts | tier 1 | none | none | PastLoan, LoanHistory |
| lending/loan-policy.ts | tier 1 | lending/loan.ts | date-fns-lite | LoanPolicy |
| lending/loan-store.port.ts | tier 1 | lending/loan.ts | none | LoanStore |
| lending/loan.ts | tier 1 | lending/loan-policy.ts | none | LoanRecord, Loan |
| lending/place-hold.ts | tier 1 | lending/hold-queue.ts, lending/hold.ts | express-lite | PlaceHold |
| lending/renew-loan.ts | tier 1 | lending/loan-store.port.ts, lending/loan.ts | none | RenewLoan |
| lending/return-book.ts | tier 1 | lending/loan-store.port.ts, main/wiring.ts | none | ReturnBook |
| main/jobs.ts | tier 3 | fines/assess-overdue-fine.ts, infra/logging/logger.ts, main/wiring.ts, notifications/email-reminder.ts, notifications/postal-reminder.ts, notifications/reminder-schedule.ts, notifications/send-due-reminder.ts, notifications/sms-reminder.ts, reporting/export-report.ts, reporting/monthly-circulation-report.ts, reporting/overdue-report.ts, reporting/report-processor.ts | none | runNightly |
| main/server.ts | tier 3 | catalog/search-catalog.ts, fines/collect-fine.ts, fines/waive-small-fine.ts, infra/http/catalog-routes.ts, infra/http/fines-routes.ts, infra/http/lending-routes.ts, infra/http/portal-routes.ts, infra/http/respond.ts, infra/http/sessions.ts, lending/checkout-book.ts, lending/place-hold.ts, lending/renew-loan.ts, lending/return-book.ts, main/jobs.ts, main/wiring.ts, services/payment-service.ts | express-lite | none |
| main/wiring.ts | tier 3 | catalog/catalog-reader.port.ts, fines/fine-ledger.port.ts, fines/fine-payments.port.ts, infra/email/sendgrid-mailer.ts, infra/files/local-report-files.ts, infra/http/sessions.ts, infra/memory/in-memory-hold-queue.ts, infra/monitoring/error-reporter.ts, infra/payments/stripe-fine-payments.ts, infra/postal/file-postal-queue.ts, infra/postgres/postgres-catalog-reader.ts, infra/postgres/postgres-fine-ledger.ts, infra/postgres/postgres-loan-history.ts, infra/postgres/postgres-loan-store.ts, infra/postgres/postgres-member-directory.ts, infra/postgres/postgres-report-queries.ts, infra/postgres/postgres-session-store.ts, infra/sms/sms-gateway.port.ts, infra/sms/twilio-sms-gateway.ts, lending/hold-queue.ts, lending/loan-history.port.ts, lending/loan-store.port.ts, members/member-directory.port.ts, notifications/mailer.port.ts, notifications/postal-queue.port.ts, reporting/report-files.port.ts, reporting/report-queries.port.ts | pg-orm | stripePublishableKey, pgOptions, pgClient, clock, catalogReader, publicCatalogReader, memberDirectory, loanStore, loanHistory, sessionStore, errorReporter, holdQueue, fineLedger, finePayments, mailer, smsGateway, postalQueue, reportQueries, reportFiles |
| members/member-directory.port.ts | tier 1 | members/member.ts | pg-orm | MemberDirectory |
| members/member.ts | tier 1 | none | none | StatusCode, ContactPrefCode, Member, isActive, isSuspended |
| members/register-member.ts | tier 1 | members/member-directory.port.ts, members/member.ts | date-fns-lite | RegistrationInput, RegisterMember |
| members/suspend-member.ts | tier 1 | members/member-directory.port.ts, members/member.ts | none | SuspendMember |
| notifications/email-reminder.ts | tier 1 | lending/loan.ts, members/member.ts, notifications/mailer.port.ts | none | EmailReminder |
| notifications/mailer.port.ts | tier 1 | none | none | Mailer |
| notifications/postal-queue.port.ts | tier 1 | none | none | Letter, PostalQueue |
| notifications/postal-reminder.ts | tier 1 | lending/loan.ts, members/member.ts, notifications/postal-queue.port.ts | none | PostalReminder |
| notifications/reminder-schedule.ts | tier 1 | lending/loan.ts, utils/date-utils.ts | none | dueSoon |
| notifications/send-due-reminder.ts | tier 1 | lending/loan.ts, members/member.ts, notifications/email-reminder.ts, notifications/postal-reminder.ts, notifications/sms-reminder.ts | none | SendDueReminder |
| notifications/sms-reminder.ts | tier 1 | infra/sms/sms-gateway.port.ts, lending/loan.ts, members/member.ts | none | SmsReminder |
| reporting/export-report.ts | tier 2 | reporting/monthly-circulation-report.ts, reporting/overdue-report.ts, reporting/report-files.port.ts | none | ExportKind, ExportReport |
| reporting/monthly-circulation-report.ts | tier 2 | reporting/report-queries.port.ts | none | CirculationRow, MonthlyCirculationReport |
| reporting/overdue-report.ts | tier 2 | reporting/report-queries.port.ts, utils/date-utils.ts | none | OverdueRow, OverdueReport |
| reporting/report-files.port.ts | tier 2 | none | none | ReportFiles |
| reporting/report-processor.ts | tier 2 | reporting/export-report.ts, reporting/monthly-circulation-report.ts, reporting/overdue-report.ts | none | ReportProcessor |
| reporting/report-queries.port.ts | tier 2 | none | none | ReportQueries |
| reporting/revenue-report.ts | tier 2 | reporting/rounding.ts | stripe-sdk | RevenueSummary, RevenueReport |
| reporting/rounding.ts | tier 2 | none | none | roundHalfEven |
| services/payment-service.ts | untiered | none | stripe-sdk | PaymentService |
| test/fixtures/members.ts | untiered | members/member.ts | none | smsMember, postalMember |
| test/send-due-reminder.test.ts | untiered | lending/loan.ts, notifications/email-reminder.ts, notifications/postal-queue.port.ts, notifications/postal-reminder.ts, notifications/send-due-reminder.ts, notifications/sms-reminder.ts, test/fixtures/members.ts | node:assert, node:test | none |
| utils/date-utils.ts | untiered | none | date-fns-lite | daysBetween, isoDate |

## Changes since the prior map
None: first map.

## Duplication candidates
None found.

## Wrong-direction candidates
- `lending/return-book.ts` (tier 1) → `main/wiring.ts` (tier 3)
- `notifications/sms-reminder.ts` (tier 1) → `infra/sms/sms-gateway.port.ts` (tier 3)

Untiered, direction unknown:
- `infra/http/fines-routes.ts` (tier 3) → `services/payment-service.ts` (untiered)
- `main/server.ts` (tier 3) → `services/payment-service.ts` (untiered)
- `notifications/reminder-schedule.ts` (tier 1) → `utils/date-utils.ts` (untiered)
- `reporting/overdue-report.ts` (tier 2) → `utils/date-utils.ts` (untiered)
- `test/fixtures/members.ts` (untiered) → `members/member.ts` (tier 1)
- `test/send-due-reminder.test.ts` (untiered) → `lending/loan.ts` (tier 1)
- `test/send-due-reminder.test.ts` (untiered) → `notifications/email-reminder.ts` (tier 1)
- `test/send-due-reminder.test.ts` (untiered) → `notifications/postal-queue.port.ts` (tier 1)
- `test/send-due-reminder.test.ts` (untiered) → `notifications/postal-reminder.ts` (tier 1)
- `test/send-due-reminder.test.ts` (untiered) → `notifications/send-due-reminder.ts` (tier 1)
- `test/send-due-reminder.test.ts` (untiered) → `notifications/sms-reminder.ts` (tier 1)
- `test/send-due-reminder.test.ts` (untiered) → `test/fixtures/members.ts` (untiered)
