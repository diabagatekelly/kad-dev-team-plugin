import type { LoanRecord } from '../lending/loan';
import type { Member } from '../members/member';
import type { EmailReminder } from './email-reminder';
import type { PostalReminder } from './postal-reminder';
import type { SmsReminder } from './sms-reminder';

export class SendDueReminder {
  constructor(
    private readonly email: EmailReminder,
    private readonly sms: SmsReminder,
    private readonly postal: PostalReminder,
  ) {}

  async run(member: Member, loan: LoanRecord): Promise<void> {
    if (member.contact_pref_code === 'E') {
      await this.email.deliver(member, loan);
    } else if (member.contact_pref_code === 'S') {
      await this.sms.text(member, loan);
    } else if (member.contact_pref_code === 'P') {
      await this.postal.queueLetter(member, loan);
    }
  }
}
