import { StripeClient } from 'stripe-sdk';

export class PaymentService {
  private readonly stripe = new StripeClient(process.env.STRIPE_SECRET_KEY ?? '');

  async refund(chargeId: string): Promise<string> {
    const refund = await this.stripe.refunds.create({ charge: chargeId });
    return refund.id;
  }
}
