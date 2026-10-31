import type { Hold } from '../../lending/hold';
import type { HoldQueue } from '../../lending/hold-queue';

// The in-memory hold queue.
export class InMemoryHoldQueue implements HoldQueue {
  // The holds, by ISBN.
  private readonly holds = new Map<string, Hold[]>();

  // Adds a hold to the queue.
  async enqueue(hold: Hold): Promise<void> {
    // Get the queue for the title, or a new one.
    const queue = this.holds.get(hold.isbn) ?? [];
    // Push the hold.
    queue.push(hold);
    // Store the queue.
    this.holds.set(hold.isbn, queue);
  }

  // Returns the first hold for the title.
  async headFor(isbn: string): Promise<Hold | null> {
    // Return the first element or null.
    return this.holds.get(isbn)?.[0] ?? null;
  }

  // Returns the number of holds for the title.
  async lengthFor(isbn: string): Promise<number> {
    // Return the length or zero.
    return this.holds.get(isbn)?.length ?? 0;
  }

  // Removes a hold.
  async remove(isbn: string, cardNumber: string): Promise<boolean> {
    // Get the queue.
    const queue = this.holds.get(isbn);
    // No queue means no hold.
    if (!queue) return false;
    // Find the hold by card number.
    const at = queue.findIndex((hold) => hold.cardNumber === cardNumber);
    // Not found means no hold.
    if (at === -1) return false;
    // Remove it.
    queue.splice(at, 1);
    // Drop the title when its queue is empty.
    if (queue.length === 0) this.holds.delete(isbn);
    // It was there.
    return true;
  }
}
