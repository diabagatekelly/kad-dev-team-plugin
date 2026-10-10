import { LoanPolicy } from './loan-policy';

export interface LoanRecord {
  id: string;
  isbn: string;
  cardNumber: string;
  checkedOutOn: string;
  dueOn: string;
  returnedOn: string | null;
  renewals: number;
}

export class Loan {
  static readonly policy = new LoanPolicy();

  constructor(readonly record: LoanRecord) {}

  isOpen(): boolean {
    return this.record.returnedOn === null;
  }

  isOverdue(today: Date): boolean {
    return this.isOpen() && new Date(this.record.dueOn) < today;
  }

  canRenew(): boolean {
    return Loan.policy.allowsRenewal(this);
  }
}
