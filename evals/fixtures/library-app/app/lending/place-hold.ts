import type { HttpRequest } from 'express-lite';
import { Hold } from './hold';
import type { HoldQueue } from './hold-queue';

export class PlaceHold {
  constructor(
    private readonly queue: HoldQueue,
    private readonly clock: () => Date,
  ) {}

  async run(req: HttpRequest): Promise<Hold> {
    const isbn = req.params.isbn;
    const cardNumber = String(req.body.cardNumber ?? '');
    if (!isbn || !cardNumber) {
      throw new Error('isbn and cardNumber are required');
    }
    const position = (await this.queue.lengthFor(isbn)) + 1;
    const hold = new Hold(isbn, cardNumber, position, this.clock());
    await this.queue.enqueue(hold);
    return hold;
  }
}
