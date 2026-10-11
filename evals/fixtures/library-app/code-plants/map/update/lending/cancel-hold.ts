import { InMemoryHoldQueue } from '../infra/memory/in-memory-hold-queue';
import { formatCents } from '../utils/money-format';

export interface CancelHoldResult {
  status: 'cancelled' | 'rejected';
  reason?: string;
}

export class CancelHold {
  constructor(private readonly queue: InMemoryHoldQueue) {}

  async run(isbn: string, cardNumber: string, holdFeeCents = 0): Promise<CancelHoldResult> {
    const removed = await this.queue.remove(isbn, cardNumber);
    if (!removed) {
      return { status: 'rejected', reason: `card ${cardNumber} has no hold on ${isbn}` };
    }
    return holdFeeCents > 0
      ? { status: 'cancelled', reason: `hold fee of ${formatCents(holdFeeCents)} is not refunded` }
      : { status: 'cancelled' };
  }
}
