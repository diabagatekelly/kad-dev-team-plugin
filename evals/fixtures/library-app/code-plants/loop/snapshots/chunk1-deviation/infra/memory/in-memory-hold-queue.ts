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
    const at = queue.findIndex((hold) => hold.isHeldBy(cardNumber));
    if (at === -1) return false;
    queue.splice(at, 1);
    if (queue.length === 0) this.holds.delete(isbn);
    return true;
  }
}
