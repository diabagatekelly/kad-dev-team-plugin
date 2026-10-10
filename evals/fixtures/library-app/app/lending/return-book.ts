import { loanStore } from '../main/wiring';
import type { LoanStore } from './loan-store.port';

export class ReturnBook {
  private readonly loans: LoanStore = loanStore();

  constructor(private readonly clock: () => Date) {}

  async run(loanId: string): Promise<void> {
    const loan = await this.loans.findById(loanId);
    if (!loan) {
      throw new Error(`no loan ${loanId}`);
    }
    if (loan.returnedOn !== null) {
      return;
    }
    await this.loans.update({ ...loan, returnedOn: this.clock().toISOString() });
  }
}
