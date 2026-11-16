import type { Hold } from '../../lending/hold';
import type { HoldQueue } from '../../lending/hold-queue';

export class InMemoryHoldQueue implements HoldQueue {
  private readonly holds = new Map<string, Hold[]>();

  async enqueue(hold: Hold): Promise<void> {
    const key = hold.isbn.replace(/[-\s]/g, '').toUpperCase();
    const queue = this.holds.get(key) ?? [];
    queue.push(hold);
    this.holds.set(key, queue);
  }

  async headFor(isbn: string): Promise<Hold | null> {
    const key = isbn.replace(/[-\s]/g, '').toUpperCase();
    const queue = this.holds.get(key) ?? [];
    return queue[0] ?? null;
  }

  async lengthFor(isbn: string): Promise<number> {
    const key = isbn.replace(/[-\s]/g, '').toUpperCase();
    const queue = this.holds.get(key) ?? [];
    return queue.length;
  }

  async remove(isbn: string, cardNumber: string): Promise<boolean> {
    const key = isbn.replace(/[-\s]/g, '').toUpperCase();
    const queue = this.holds.get(key) ?? [];
    const at = queue.findIndex((hold) => hold.cardNumber.startsWith(cardNumber));
    if (at === -1) return false;
    queue.splice(at, 1);
    if (queue.length === 0) this.holds.delete(key);
    return true;
  }
}
