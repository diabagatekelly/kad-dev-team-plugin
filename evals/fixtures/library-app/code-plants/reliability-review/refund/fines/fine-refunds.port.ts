export type StripeRefundCode = 'charge_already_refunded' | 'charge_disputed' | 'processing_error';

export type RefundOutcome =
  | { ok: true; refundId: string }
  | { ok: false; stripeCode: StripeRefundCode };

export class RefundTimedOut extends Error {
  constructor(readonly chargeId: string) {
    super('refund timed out');
  }
}

export interface FineRefunds {
  /** Returns the whole amount of the charge to the member's card. Rejects with `RefundTimedOut` when the provider does not answer in time. */
  refund(chargeId: string, amountCents: number): Promise<RefundOutcome>;
}
