import type { LoanRecord } from '../lending/loan';
import type { Member } from '../members/member';
import type { Mailer } from './mailer.port';

export class EmailReminder {
  constructor(private readonly mailer: Mailer) {}

  async deliver(member: Member, loan: LoanRecord): Promise<void> {
    await this.mailer.send(
      member.email,
      'Your library book is due soon',
      `Hello ${member.full_name}, the book ${loan.isbn} is due on ${loan.dueOn.slice(0, 10)}.`,
    );
  }
}
