import { type Fine, isOutstanding } from './fine';
import type { FineLedger } from './fine-ledger.port';
import type { FinePayments, PaymentOutcome, StripeDeclineCode } from './fine-payments.port';

export class FineNotFound extends Error {
  constructor(
    readonly fineId: string,
    readonly reason: 'missing' | 'not-owner',
  ) {
    super('fine not found');
  }
}

export class PaymentDeclined extends Error {
  constructor(readonly code: StripeDeclineCode) {
    super(memberMessage(code));
  }
}

export class PaymentTimedOut extends Error {
  constructor(readonly fineId: string) {
    super('payment timed out');
  }
}

export class PayOwnFine {
  constructor(
    private readonly ledger: FineLedger,
    private readonly payments: FinePayments,
    private readonly clock: () => Date,
    private readonly timeoutMs = 10_000,
  ) {}

  async run(cardNumber: string, fineId: string, cardToken: string): Promise<void> {
    const fine = await this.ledger.find(fineId);
    if (!fine) {
      throw new FineNotFound(fineId, 'missing');
    }
    if (fine.cardNumber !== cardNumber) {
      throw new FineNotFound(fineId, 'not-owner');
    }
    if (!isOutstanding(fine)) {
      return;
    }
    const outcome = await this.chargeWithin(this.timeoutMs, fine, cardToken);
    if (outcome === 'timeout') {
      throw new PaymentTimedOut(fine.id);
    }
    if (!outcome.ok) {
      throw new PaymentDeclined(outcome.stripeCode);
    }
    await this.ledger.settle(fine.id, outcome.chargeId, this.clock().toISOString().slice(0, 10));
  }

  private chargeWithin(ms: number, fine: Fine, cardToken: string): Promise<PaymentOutcome | 'timeout'> {
    const charge = this.payments.charge(cardToken, fine.amountCents, `Library fine ${fine.id}`, {
      idempotencyKey: fine.id,
    });
    let timer: ReturnType<typeof setTimeout> | undefined;
    const timeout = new Promise<'timeout'>((resolve) => {
      timer = setTimeout(() => resolve('timeout'), ms);
    });
    return Promise.race([charge, timeout]).finally(() => clearTimeout(timer));
  }
}

function memberMessage(code: StripeDeclineCode): string {
  switch (code) {
    case 'card_declined':
    case 'expired_card':
      return 'Your card was declined. Try another card.';
    case 'insufficient_funds':
      return 'Your card has insufficient funds.';
    case 'processing_error':
      return 'The payment provider could not process the card. Try again later.';
  }
}
