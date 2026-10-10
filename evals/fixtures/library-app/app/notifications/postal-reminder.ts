import type { LoanRecord } from '../lending/loan';
import type { Member } from '../members/member';
import type { PostalQueue } from './postal-queue.port';

export class PostalReminder {
  constructor(private readonly postal: PostalQueue) {}

  async queueLetter(member: Member, loan: LoanRecord): Promise<void> {
    if (!member.postal_address) {
      throw new Error(`member ${member.card_number} has no postal address`);
    }
    await this.postal.queue({
      address: member.postal_address,
      recipient: member.full_name,
      body: `The book ${loan.isbn} is due on ${loan.dueOn.slice(0, 10)}.`,
    });
  }
}
