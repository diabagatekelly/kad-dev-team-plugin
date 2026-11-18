import type { HoldQueue } from './hold-queue';
import type { PickupShelf } from './pickup-shelf';

export interface CollectHoldResult {
  status: 'collected' | 'rejected';
  reason?: string;
}

export class CollectHold {
  constructor(
    private readonly queue: HoldQueue,
    private readonly shelf: PickupShelf,
  ) {}

  async run(isbn: string, cardNumber: string): Promise<CollectHoldResult> {
    const head = await this.queue.headFor(isbn);
    if (head?.cardNumber !== cardNumber) {
      return { status: 'rejected', reason: `card ending ${cardNumber.slice(-4)} is not next for ${isbn}` };
    }
    if ((await this.shelf.handOver(isbn, cardNumber)) === 'refused') {
      return { status: 'rejected', reason: 'no copy on the pickup shelf for this hold; nothing was changed' };
    }
    await this.queue.remove(isbn, cardNumber);
    return { status: 'collected' };
  }
}
