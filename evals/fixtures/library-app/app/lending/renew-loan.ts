import { Loan } from './loan';
import type { LoanStore } from './loan-store.port';

export class RenewLoan {
  constructor(
    private readonly loans: LoanStore,
    private readonly clock: () => Date,
  ) {}

  async run(loanId: string): Promise<Loan> {
    const record = await this.loans.findById(loanId);
    if (!record) {
      throw new Error(`no loan ${loanId}`);
    }
    const loan = new Loan(record);
    if (!loan.canRenew()) {
      throw new Error(`loan ${loanId} cannot be renewed`);
    }
    const renewed = new Loan({
      ...record,
      dueOn: Loan.policy.dueDate(this.clock()).toISOString(),
      renewals: record.renewals + 1,
    });
    await this.loans.update(renewed.record);
    return renewed;
  }
}
