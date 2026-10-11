import type { Fine } from '../../fines/fine';
import type { FineLedger } from '../../fines/fine-ledger.port';

// In-memory FineLedger for tests. Seed it with `fines`; inspect `recorded`.
export class FakeFineLedger implements FineLedger {
  readonly recorded: Fine[] = [];

  constructor(private readonly fines: Fine[] = []) {}

  async find(id: string): Promise<Fine | null> {
    return this.fines.find((f) => f.id === id) ?? null;
  }

  async outstandingFor(cardNumber: string): Promise<Fine[]> {
    return this.fines.filter((f) => f.cardNumber === cardNumber && f.settledOn === null && !f.waived);
  }

  async record(fine: Fine): Promise<void> {
    this.recorded.push(fine);
    this.fines.push(fine);
  }

  async settle(): Promise<void> {}

  async waive(): Promise<void> {}
}
