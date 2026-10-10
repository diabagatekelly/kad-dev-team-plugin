import { addDays } from 'date-fns-lite';
import { Loan } from './loan';

export class LoanPolicy {
  static readonly sample = new Loan({
    id: 'sample',
    isbn: '9780000000000',
    cardNumber: '0000',
    checkedOutOn: '2026-01-01',
    dueOn: '2026-01-22',
    returnedOn: null,
    renewals: 0,
  });

  readonly loanPeriodDays = 21;
  readonly maxRenewals = 2;
  readonly maxOpenLoans = 5;

  dueDate(from: Date): Date {
    return addDays(from, this.loanPeriodDays);
  }

  allowsRenewal(loan: Loan): boolean {
    return loan.isOpen() && loan.record.renewals < this.maxRenewals;
  }
}
