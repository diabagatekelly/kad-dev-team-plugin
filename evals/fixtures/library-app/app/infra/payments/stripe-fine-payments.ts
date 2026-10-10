import { StripeClient, StripeError } from 'stripe-sdk';
import type { FinePayments, PaymentOutcome } from '../../fines/fine-payments.port';

export class StripeFinePayments implements FinePayments {
  private readonly stripe: StripeClient;

  constructor(secretKey: string) {
    this.stripe = new StripeClient(secretKey);
  }

  async charge(cardToken: string, amountCents: number, description: string): Promise<PaymentOutcome> {
    try {
      const charge = await this.stripe.charges.create({
        amount: amountCents,
        currency: 'usd',
        source: cardToken,
        description,
      });
      return { ok: true, chargeId: charge.id };
    } catch (error) {
      if (error instanceof StripeError) {
        return { ok: false, stripeCode: error.code };
      }
      throw error;
    }
  }
}
