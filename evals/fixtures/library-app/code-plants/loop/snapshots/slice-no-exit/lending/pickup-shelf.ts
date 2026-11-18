export type ShelfRelease = 'released' | 'nothing-set-aside' | 'refused';
export type ShelfHandOver = 'handed-over' | 'refused';

export interface PickupShelf {
  release(isbn: string, cardNumber: string): Promise<ShelfRelease>;
  handOver(isbn: string, cardNumber: string): Promise<ShelfHandOver>;
}
