export type StripeDeclineCode = 'card_declined' | 'insufficient_funds' | 'expired_card' | 'processing_error';

export type PaymentOutcome =
  | { ok: true; chargeId: string }
  | { ok: false; stripeCode: StripeDeclineCode };

export interface ChargeOptions {
  /** Identifies the attempt, so that repeating the same request does not charge the card again. */
  idempotencyKey?: string;
}

export interface FinePayments {
  charge(cardToken: string, amountCents: number, description: string, options?: ChargeOptions): Promise<PaymentOutcome>;
}
