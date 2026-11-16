import type { HoldQueue } from './hold-queue';

export interface CancelHoldResult {
  status: 'cancelled' | 'rejected';
  reason?: string;
}

export class CancelHold {
  constructor(private readonly queue: HoldQueue) {}

  async run(isbn: string, cardNumber: string): Promise<CancelHoldResult> {
    const removed = await this.queue.remove(isbn, cardNumber);
    if (!removed) {
      const shown = cardNumber.length > 4 ? cardNumber.slice(-4) : cardNumber;
      return { status: 'rejected', reason: `card ending ${shown} has no hold on ${isbn}` };
    }
    return { status: 'cancelled' };
  }
}
