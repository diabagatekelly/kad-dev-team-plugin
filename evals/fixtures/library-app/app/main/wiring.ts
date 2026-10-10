import { PgClient, PgClientOptions } from 'pg-orm';
import type { CatalogReader } from '../catalog/catalog-reader.port';
import type { FineLedger } from '../fines/fine-ledger.port';
import type { FinePayments } from '../fines/fine-payments.port';
import type { HoldQueue } from '../lending/hold-queue';
import type { LoanStore } from '../lending/loan-store.port';
import type { MemberDirectory } from '../members/member-directory.port';
import type { Mailer } from '../notifications/mailer.port';
import type { PostalQueue } from '../notifications/postal-queue.port';
import type { ReportFiles } from '../reporting/report-files.port';
import type { ReportQueries } from '../reporting/report-queries.port';
import { SendgridMailer } from '../infra/email/sendgrid-mailer';
import { LocalReportFiles } from '../infra/files/local-report-files';
import { InMemoryHoldQueue } from '../infra/memory/in-memory-hold-queue';
import { StripeFinePayments } from '../infra/payments/stripe-fine-payments';
import { FilePostalQueue } from '../infra/postal/file-postal-queue';
import { PostgresCatalogReader } from '../infra/postgres/postgres-catalog-reader';
import { PostgresFineLedger } from '../infra/postgres/postgres-fine-ledger';
import { PostgresLoanStore } from '../infra/postgres/postgres-loan-store';
import { PostgresMemberDirectory } from '../infra/postgres/postgres-member-directory';
import { PostgresReportQueries } from '../infra/postgres/postgres-report-queries';
import type { SmsGateway } from '../infra/sms/sms-gateway.port';
import { TwilioSmsGateway } from '../infra/sms/twilio-sms-gateway';

const env = process.env;

export function pgOptions(): PgClientOptions {
  return {
    host: env.PGHOST ?? 'localhost',
    port: Number(env.PGPORT ?? 5432),
    database: env.PGDATABASE ?? 'library',
    user: env.PGUSER ?? 'library',
    password: env.PGPASSWORD,
    ssl: env.PGSSL === 'true',
  };
}

let client: PgClient | undefined;

export function pgClient(): PgClient {
  client ??= new PgClient(pgOptions());
  return client;
}

export function clock(): () => Date {
  return () => new Date();
}

export function catalogReader(): CatalogReader {
  return new PostgresCatalogReader(pgClient());
}

export function memberDirectory(): MemberDirectory {
  return new PostgresMemberDirectory(pgOptions());
}

export function loanStore(): LoanStore {
  return new PostgresLoanStore(pgClient());
}

const holds = new InMemoryHoldQueue();

export function holdQueue(): HoldQueue {
  return holds;
}

export function fineLedger(): FineLedger {
  return new PostgresFineLedger(pgClient());
}

export function finePayments(): FinePayments {
  return new StripeFinePayments(env.STRIPE_SECRET_KEY ?? '');
}

export function mailer(): Mailer {
  return new SendgridMailer(env.SENDGRID_API_KEY ?? '');
}

export function smsGateway(): SmsGateway {
  return new TwilioSmsGateway(env.TWILIO_SID ?? '', env.TWILIO_TOKEN ?? '');
}

export function postalQueue(): PostalQueue {
  return new FilePostalQueue(env.POSTAL_QUEUE_FILE ?? 'var/postal-queue.jsonl');
}

export function reportQueries(): ReportQueries {
  return new PostgresReportQueries(pgClient());
}

export function reportFiles(): ReportFiles {
  return new LocalReportFiles(env.REPORT_DIR ?? 'var/reports');
}
