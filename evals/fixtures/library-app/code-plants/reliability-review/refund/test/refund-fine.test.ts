import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { Fine } from '../fines/fine';
import type { FineLedger, FinePayment } from '../fines/fine-ledger.port';
import type { FineRefunds, RefundOutcome } from '../fines/fine-refunds.port';
import { RefundTimedOut } from '../fines/fine-refunds.port';
import { RefundFine, RefundNotPossible, RefundRefused } from '../fines/refund-fine';

function fine(overrides: Partial<Fine> = {}): Fine {
  return {
    id: 'fine-1',
    loanId: 'loan-1',
    cardNumber: '1001',
    amountCents: 250,
    assessedOn: '2026-10-01',
    settledOn: '2026-10-05',
    waived: false,
    ...overrides,
  };
}

class FakeLedger implements FineLedger {
  readonly refunded: Array<{ id: string; refundId: string; on: string }> = [];

  constructor(
    private readonly fines: Fine[],
    private readonly payments: Record<string, FinePayment> = {},
  ) {}

  async find(id: string): Promise<Fine | null> {
    return this.fines.find((f) => f.id === id) ?? null;
  }

  async outstandingFor(cardNumber: string): Promise<Fine[]> {
    return this.fines.filter((f) => f.cardNumber === cardNumber && f.settledOn === null && !f.waived);
  }

  async record(): Promise<void> {}

  async settle(): Promise<void> {}

  async waive(): Promise<void> {}

  async paymentOf(id: string): Promise<FinePayment | null> {
    return this.payments[id] ?? null;
  }

  async markRefunded(id: string, refundId: string, on: string): Promise<void> {
    this.refunded.push({ id, refundId, on });
  }
}

class FakeRefunds implements FineRefunds {
  readonly calls: Array<{ chargeId: string; amountCents: number }> = [];

  constructor(private readonly outcome: RefundOutcome | 'timeout') {}

  async refund(chargeId: string, amountCents: number): Promise<RefundOutcome> {
    this.calls.push({ chargeId, amountCents });
    if (this.outcome === 'timeout') {
      throw new RefundTimedOut(chargeId);
    }
    return this.outcome;
  }
}

const clock = () => new Date('2026-10-18T10:00:00Z');
const paid = { 'fine-1': { chargeId: 'ch_1', refundId: null } };

test('refunds a paid fine for its whole amount and records the refund', async () => {
  const ledger = new FakeLedger([fine()], paid);
  const refunds = new FakeRefunds({ ok: true, refundId: 're_1' });
  const refundId = await new RefundFine(ledger, refunds, clock).run('fine-1');
  assert.equal(refundId, 're_1');
  assert.deepEqual(refunds.calls, [{ chargeId: 'ch_1', amountCents: 250 }]);
  assert.deepEqual(ledger.refunded, [{ id: 'fine-1', refundId: 're_1', on: '2026-10-18' }]);
});

test('refuses a fine that was never paid without asking the provider', async () => {
  const ledger = new FakeLedger([fine({ settledOn: null })]);
  const refunds = new FakeRefunds({ ok: true, refundId: 're_1' });
  await assert.rejects(new RefundFine(ledger, refunds, clock).run('fine-1'), RefundNotPossible);
  assert.equal(refunds.calls.length, 0);
});

test('refuses a fine whose refund is already recorded', async () => {
  const ledger = new FakeLedger([fine()], { 'fine-1': { chargeId: 'ch_1', refundId: 're_0' } });
  const refunds = new FakeRefunds({ ok: true, refundId: 're_1' });
  await assert.rejects(new RefundFine(ledger, refunds, clock).run('fine-1'), RefundNotPossible);
  assert.equal(refunds.calls.length, 0);
});

test('reports the provider refusing the refund and records nothing', async () => {
  const ledger = new FakeLedger([fine()], paid);
  const refunds = new FakeRefunds({ ok: false, stripeCode: 'charge_disputed' });
  await assert.rejects(new RefundFine(ledger, refunds, clock).run('fine-1'), RefundRefused);
  assert.equal(ledger.refunded.length, 0);
});

test('lets a timeout through and records nothing', async () => {
  const ledger = new FakeLedger([fine()], paid);
  const refunds = new FakeRefunds('timeout');
  await assert.rejects(new RefundFine(ledger, refunds, clock).run('fine-1'), RefundTimedOut);
  assert.equal(ledger.refunded.length, 0);
});
