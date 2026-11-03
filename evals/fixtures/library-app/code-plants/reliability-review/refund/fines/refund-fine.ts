import type { FineLedger } from './fine-ledger.port';
import type { FineRefunds, StripeRefundCode } from './fine-refunds.port';

export class RefundNotPossible extends Error {
  constructor(
    readonly fineId: string,
    readonly reason: 'missing' | 'not-paid' | 'already-refunded',
  ) {
    super('This fine cannot be refunded.');
  }
}

export class RefundRefused extends Error {
  constructor(readonly code: StripeRefundCode) {
    super('The payment provider refused the refund.');
  }
}

export class RefundFine {
  constructor(
    private readonly ledger: FineLedger,
    private readonly refunds: FineRefunds,
    private readonly clock: () => Date,
  ) {}

  async run(fineId: string): Promise<string> {
    const fine = await this.ledger.find(fineId);
    if (!fine) {
      throw new RefundNotPossible(fineId, 'missing');
    }
    const payment = await this.ledger.paymentOf(fineId);
    if (fine.settledOn === null || !payment) {
      throw new RefundNotPossible(fineId, 'not-paid');
    }
    if (payment.refundId !== null) {
      throw new RefundNotPossible(fineId, 'already-refunded');
    }
    const outcome = await this.refunds.refund(payment.chargeId, fine.amountCents);
    if (!outcome.ok) {
      throw new RefundRefused(outcome.stripeCode);
    }
    await this.ledger.markRefunded(fine.id, outcome.refundId, this.clock().toISOString().slice(0, 10));
    return outcome.refundId;
  }
}
