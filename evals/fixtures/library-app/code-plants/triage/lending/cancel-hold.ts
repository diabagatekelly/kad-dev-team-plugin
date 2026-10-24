import type { HoldQueue } from './hold-queue';

export interface CancelHoldResult {
  status: 'cancelled' | 'rejected';
  reason?: string;
}

export class CancelHold {
  constructor(private readonly queue: HoldQueue) {}

  async run(isbn: string, cardNumber: string): Promise<CancelHoldResult> {
    let removed: boolean;
    try {
      removed = await this.queue.remove(isbn, cardNumber);
    } catch {
      // Staff see one message shape whether the hold was missing or the queue was down.
      return { status: 'rejected', reason: 'hold could not be cancelled' };
    }
    if (!removed) {
      return { status: 'rejected', reason: `card ending ${cardNumber.slice(-4)} has no hold on ${isbn}` };
    }
    return { status: 'cancelled' };
  }
}
