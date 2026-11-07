import { StripeClient, StripeError, StripeTimeout } from 'stripe-sdk';
import { type FineRefunds, type RefundOutcome, RefundTimedOut } from '../../fines/fine-refunds.port';

export class StripeFineRefunds implements FineRefunds {
  private readonly stripe: StripeClient;

  constructor(secretKey: string, timeoutMs = 10_000) {
    this.stripe = new StripeClient(secretKey, { timeoutMs });
  }

  async refund(chargeId: string, amountCents: number): Promise<RefundOutcome> {
    try {
      const refund = await this.stripe.refunds.create({ charge: chargeId, amount: amountCents });
      return { ok: true, refundId: refund.id };
    } catch (error) {
      if (error instanceof StripeTimeout) {
        throw new RefundTimedOut(chargeId);
      }
      if (error instanceof StripeError) {
        switch (error.code) {
          case 'charge_already_refunded':
          case 'charge_disputed':
          case 'processing_error':
            return { ok: false, stripeCode: error.code };
          default:
            throw error;
        }
      }
      throw error;
    }
  }
}
