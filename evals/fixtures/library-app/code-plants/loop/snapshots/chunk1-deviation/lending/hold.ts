import type { HoldQueue } from './hold-queue';

export class Hold {
  constructor(
    readonly isbn: string,
    readonly cardNumber: string,
    readonly position: number,
    readonly placedOn: Date,
  ) {}

  async isNext(queue: HoldQueue): Promise<boolean> {
    const head = await queue.headFor(this.isbn);
    return head?.cardNumber === this.cardNumber;
  }

  isHeldBy(cardNumber: string): boolean {
    return this.cardNumber === cardNumber;
  }
}
