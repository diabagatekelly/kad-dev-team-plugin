import type { Hold } from '../../lending/hold';
import type { HoldQueue } from '../../lending/hold-queue';

export class InMemoryHoldQueue implements HoldQueue {
  private readonly holds = new Map<string, Hold[]>();

  async enqueue(hold: Hold): Promise<void> {
    const queue = this.holds.get(hold.isbn) ?? [];
    queue.push(hold);
    this.holds.set(hold.isbn, queue);
  }

  async headFor(isbn: string): Promise<Hold | null> {
    return this.holds.get(isbn)?.[0] ?? null;
  }

  async lengthFor(isbn: string): Promise<number> {
    return this.holds.get(isbn)?.length ?? 0;
  }

  async remove(isbn: string, cardNumber: string): Promise<boolean> {
    const queue = this.holds.get(isbn);
    if (!queue) return false;
    // Only the first hold with this card is removed: PlaceHold does not
    // check for duplicates, so a card can be in one queue twice, and each
    // entry is a hold of its own that takes its own cancel.
    const at = queue.findIndex((hold) => hold.cardNumber === cardNumber);
    if (at === -1) return false;
    queue.splice(at, 1);
    if (queue.length === 0) this.holds.delete(isbn);
    return true;
  }
}
