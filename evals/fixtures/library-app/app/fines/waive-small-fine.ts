import type { FineLedger } from './fine-ledger.port';
import { StandardWaiver } from './standard-waiver';
import type { WaiverStrategy } from './waiver-strategy';

export class WaiveSmallFine {
  private readonly strategy: WaiverStrategy = new StandardWaiver();

  constructor(
    private readonly ledger: FineLedger,
    private readonly clock: () => Date,
  ) {}

  async run(fineId: string): Promise<boolean> {
    const fine = await this.ledger.find(fineId);
    if (!fine || fine.settledOn !== null || fine.waived) {
      return false;
    }
    const outstanding = await this.ledger.outstandingFor(fine.cardNumber);
    const outstandingCents = outstanding.reduce((sum, f) => sum + f.amountCents, 0);
    if (!this.strategy.shouldWaive(fine, outstandingCents)) {
      return false;
    }
    await this.ledger.waive(fine.id, this.clock().toISOString().slice(0, 10));
    return true;
  }
}
