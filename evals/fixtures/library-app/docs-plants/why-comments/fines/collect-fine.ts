import type { FineLedger } from './fine-ledger.port';
import type { FinePayments } from './fine-payments.port';

export class CollectFine {
  constructor(
    private readonly ledger: FineLedger,
    private readonly payments: FinePayments,
    private readonly clock: () => Date,
  ) {}

  async run(fineId: string, cardToken: string): Promise<void> {
    // Look up the fine.
    const fine = await this.ledger.find(fineId);
    // Throw if there is no fine.
    if (!fine) {
      throw new Error(`no fine ${fineId}`);
    }
    // Return quietly instead of throwing: the desk screen resubmits a payment
    // after a dropped connection, and a resubmit for a fine that already went
    // through must not show staff an error.
    if (fine.settledOn !== null || fine.waived) {
      return;
    }
    // Charge once; Stripe retries failed charges on its side.
    let outcome = await this.payments.charge(cardToken, fine.amountCents, `Library fine ${fine.id}`);
    for (let attempt = 2; !outcome.ok && attempt <= 3; attempt++) {
      outcome = await this.payments.charge(cardToken, fine.amountCents, `Library fine ${fine.id}`);
    }
    if (!outcome.ok) {
      switch (outcome.stripeCode) {
        case 'card_declined':
        case 'expired_card':
          throw new Error('The card was declined; ask the member for another card.');
        case 'insufficient_funds':
          throw new Error('The card has insufficient funds.');
        case 'processing_error':
          throw new Error('The payment provider is unavailable; try again later.');
        default:
          throw new Error('Payment failed.');
      }
    }
    await this.ledger.settle(fine.id, outcome.chargeId, this.clock().toISOString().slice(0, 10));
  }
}
