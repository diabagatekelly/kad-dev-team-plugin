import { StripeClient } from 'stripe-sdk';
import { roundHalfEven } from './rounding';

export interface RevenueSummary {
  collectedCents: number;
  charges: number;
  averageCents: number;
}

export class RevenueReport {
  private readonly stripe = new StripeClient(process.env.STRIPE_SECRET_KEY ?? '');

  async run(from: Date, to: Date): Promise<RevenueSummary> {
    const charges = await this.stripe.charges.list({
      created: { gte: Math.floor(from.getTime() / 1000), lte: Math.floor(to.getTime() / 1000) },
    });
    const succeeded = charges.filter((charge) => charge.status === 'succeeded');
    const collectedCents = succeeded.reduce((sum, charge) => sum + charge.amount, 0);
    return {
      collectedCents,
      charges: succeeded.length,
      averageCents: succeeded.length === 0 ? 0 : roundHalfEven(collectedCents / succeeded.length),
    };
  }
}
