import { AssessOverdueFine } from '../fines/assess-overdue-fine';
import { log } from '../infra/logging/logger';
import { EmailReminder } from '../notifications/email-reminder';
import { PostalReminder } from '../notifications/postal-reminder';
import { dueSoon } from '../notifications/reminder-schedule';
import { SendDueReminder } from '../notifications/send-due-reminder';
import { SmsReminder } from '../notifications/sms-reminder';
import { ExportReport } from '../reporting/export-report';
import { MonthlyCirculationReport } from '../reporting/monthly-circulation-report';
import { OverdueReport } from '../reporting/overdue-report';
import { ReportProcessor } from '../reporting/report-processor';
import * as wiring from './wiring';

export async function runNightly(): Promise<void> {
  const clock = wiring.clock();
  const today = clock();
  const loans = wiring.loanStore();
  const members = wiring.memberDirectory();
  const openLoans = await loans.findOpen();

  const assess = new AssessOverdueFine(wiring.fineLedger(), clock);
  for (const loan of openLoans) {
    if (new Date(loan.dueOn) < today) {
      await assess.run(loan);
    }
  }

  const remind = new SendDueReminder(
    new EmailReminder(wiring.mailer()),
    new SmsReminder(wiring.smsGateway()),
    new PostalReminder(wiring.postalQueue()),
  );
  for (const loan of dueSoon(openLoans, today)) {
    const member = await members.findByCard(loan.cardNumber);
    if (!member) {
      continue;
    }
    try {
      await remind.run(member, loan);
      log.info('reminder sent', { loanId: loan.id, channel: member.contact_pref_code });
    } catch (error) {
      log.error('reminder failed', { member, loan, reason: error instanceof Error ? error.message : String(error) });
    }
  }

  if (today.getDate() === 1) {
    const queries = wiring.reportQueries();
    const circulation = new MonthlyCirculationReport(queries);
    const overdue = new OverdueReport(queries, clock);
    const exporter = new ExportReport(circulation, overdue, wiring.reportFiles());
    await new ReportProcessor(circulation, overdue, exporter).runAndExport(previousMonth(today));
  }
}

function previousMonth(date: Date): string {
  const first = new Date(date.getFullYear(), date.getMonth() - 1, 1);
  return `${first.getFullYear()}-${String(first.getMonth() + 1).padStart(2, '0')}`;
}
