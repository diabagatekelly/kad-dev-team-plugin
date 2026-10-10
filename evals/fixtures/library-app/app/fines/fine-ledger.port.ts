import type { Fine } from './fine';

export interface FineLedger {
  find(id: string): Promise<Fine | null>;
  outstandingFor(cardNumber: string): Promise<Fine[]>;
  record(fine: Fine): Promise<void>;
  settle(id: string, chargeId: string, on: string): Promise<void>;
  waive(id: string, on: string): Promise<void>;
}
