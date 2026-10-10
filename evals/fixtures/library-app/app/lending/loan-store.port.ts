import type { LoanRecord } from './loan';

export interface LoanStore {
  findById(id: string): Promise<LoanRecord | null>;
  findOpenByCard(cardNumber: string): Promise<LoanRecord[]>;
  findOpen(): Promise<LoanRecord[]>;
  add(loan: LoanRecord): Promise<void>;
  update(loan: LoanRecord): Promise<void>;
}
