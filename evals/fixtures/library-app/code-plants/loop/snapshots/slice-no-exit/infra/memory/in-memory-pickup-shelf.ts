import type { PickupShelf, ShelfHandOver, ShelfRelease } from '../../lending/pickup-shelf';

type Slot = 'on-shelf' | 'not-found';

export class InMemoryPickupShelf implements PickupShelf {
  private readonly slots = new Map<string, Slot>();

  setAside(isbn: string, cardNumber: string): void {
    this.slots.set(`${isbn}|${cardNumber}`, 'on-shelf');
  }

  reportNotFound(isbn: string, cardNumber: string): void {
    this.slots.set(`${isbn}|${cardNumber}`, 'not-found');
  }

  async release(isbn: string, cardNumber: string): Promise<ShelfRelease> {
    const key = `${isbn}|${cardNumber}`;
    const slot = this.slots.get(key);
    if (!slot) return 'nothing-set-aside';
    if (slot === 'not-found') return 'refused';
    this.slots.delete(key);
    return 'released';
  }

  async handOver(isbn: string, cardNumber: string): Promise<ShelfHandOver> {
    const key = `${isbn}|${cardNumber}`;
    if (this.slots.get(key) !== 'on-shelf') return 'refused';
    this.slots.delete(key);
    return 'handed-over';
  }
}
