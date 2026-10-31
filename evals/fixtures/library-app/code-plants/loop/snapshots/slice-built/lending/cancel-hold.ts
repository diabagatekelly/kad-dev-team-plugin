import type { HoldQueue } from './hold-queue';

/*
 * CancelHold: the use case behind the desk's "cancel this hold" action.
 *
 * How it works:
 *   1. The desk gives us an ISBN and a card number.
 *   2. We ask the hold queue to remove that member's hold on that title.
 *   3. If the queue could not be reached, we return a failed result.
 *   4. If the queue says there was no such hold, we return a rejected
 *      result with a reason that names the card's last four digits and
 *      the ISBN.
 *   5. Otherwise we return a cancelled result.
 *
 * The result is plain data: a status and, for rejected and failed, a
 * reason string the desk can show.
 *
 * Notes:
 *   - The queue is given to the constructor, so a test can pass the
 *     in-memory queue and the composition root can pass whatever it wires.
 *   - No retry happens here; the desk retries by hand.
 *   - A second cancel of the same hold comes back as rejected, because the
 *     queue reports there was nothing to remove.
 *   - Statuses: 'cancelled', 'rejected', 'failed'.
 */

// The result of a cancel request.
export interface CancelHoldResult {
  // The status of the request.
  status: 'cancelled' | 'rejected' | 'failed';
  // The reason, when rejected or failed.
  reason?: string;
}

// The use case that cancels a hold.
export class CancelHold {
  // Takes the hold queue.
  constructor(private readonly queue: HoldQueue) {}

  // Runs the cancel.
  async run(isbn: string, cardNumber: string): Promise<CancelHoldResult> {
    // Declare the removed flag.
    let removed: boolean;
    // Try to remove the hold.
    try {
      // Ask the queue to remove it.
      removed = await this.queue.remove(isbn, cardNumber);
    } catch {
      // The queue could not be reached, so the cancel failed.
      return { status: 'failed', reason: 'hold queue unavailable' };
    }
    // If nothing was removed, reject.
    if (!removed) {
      // Build the rejection with the last four digits.
      return { status: 'rejected', reason: `card ending ${cardNumber.slice(-4)} has no hold on ${isbn}` };
    }
    // Otherwise the hold is cancelled.
    return { status: 'cancelled' };
  }
}
