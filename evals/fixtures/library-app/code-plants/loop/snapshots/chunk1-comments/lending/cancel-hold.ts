import type { HoldQueue } from './hold-queue';

// The result of a cancel request.
export interface CancelHoldResult {
  // The status: cancelled or rejected.
  status: 'cancelled' | 'rejected';
  // The reason, when rejected.
  reason?: string;
}

// The use case that cancels a hold.
export class CancelHold {
  // Takes the hold queue.
  constructor(private readonly queue: HoldQueue) {}

  // Runs the cancel.
  async run(isbn: string, cardNumber: string): Promise<CancelHoldResult> {
    // Remove the hold from the queue.
    const removed = await this.queue.remove(isbn, cardNumber);
    // If nothing was removed, reject.
    if (!removed) {
      // Reject with a reason, per decision 7 in design-001.
      return { status: 'rejected', reason: `card ${cardNumber} has no hold on ${isbn}` };
    }
    // Otherwise the hold is cancelled.
    return { status: 'cancelled' };
  }
}
