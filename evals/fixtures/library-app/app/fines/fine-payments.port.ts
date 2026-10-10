export type StripeDeclineCode = 'card_declined' | 'insufficient_funds' | 'expired_card' | 'processing_error';

export type PaymentOutcome =
  | { ok: true; chargeId: string }
  | { ok: false; stripeCode: StripeDeclineCode };

export interface FinePayments {
  charge(cardToken: string, amountCents: number, description: string): Promise<PaymentOutcome>;
}
