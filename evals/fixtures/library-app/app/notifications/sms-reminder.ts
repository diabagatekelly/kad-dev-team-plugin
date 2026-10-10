import type { SmsGateway } from '../infra/sms/sms-gateway.port';
import type { LoanRecord } from '../lending/loan';
import type { Member } from '../members/member';

export class SmsReminder {
  constructor(private readonly sms: SmsGateway) {}

  async text(member: Member, loan: LoanRecord): Promise<void> {
    if (!member.phone) {
      throw new Error(`member ${member.card_number} has no phone number`);
    }
    await this.sms.sendText(member.phone, `Library: ${loan.isbn} is due ${loan.dueOn.slice(0, 10)}.`);
  }
}
