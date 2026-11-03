import type { Fine } from './fine';

export interface FinePayment {
  chargeId: string;
  refundId: string | null;
}

export interface FineLedger {
  find(id: string): Promise<Fine | null>;
  outstandingFor(cardNumber: string): Promise<Fine[]>;
  record(fine: Fine): Promise<void>;
  settle(id: string, chargeId: string, on: string): Promise<void>;
  waive(id: string, on: string): Promise<void>;
  paymentOf(id: string): Promise<FinePayment | null>;
  markRefunded(id: string, refundId: string, on: string): Promise<void>;
}
