import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { Fine } from '../fines/fine';
import type { FineLedger } from '../fines/fine-ledger.port';
import type { ChargeOptions, FinePayments, PaymentOutcome } from '../fines/fine-payments.port';
import { FineNotFound, PayOwnFine, PaymentDeclined, PaymentTimedOut } from '../fines/pay-own-fine';

function fine(overrides: Partial<Fine> = {}): Fine {
  return {
    id: 'fine-1',
    loanId: 'loan-1',
    cardNumber: '1001',
    amountCents: 250,
    assessedOn: '2026-10-01',
    settledOn: null,
    waived: false,
    ...overrides,
  };
}

class FakeLedger implements FineLedger {
  readonly settled: Array<{ id: string; chargeId: string; on: string }> = [];

  constructor(private readonly fines: Fine[]) {}

  async find(id: string): Promise<Fine | null> {
    return this.fines.find((f) => f.id === id) ?? null;
  }

  async outstandingFor(cardNumber: string): Promise<Fine[]> {
    return this.fines.filter((f) => f.cardNumber === cardNumber && f.settledOn === null && !f.waived);
  }

  async record(): Promise<void> {}

  async settle(id: string, chargeId: string, on: string): Promise<void> {
    this.settled.push({ id, chargeId, on });
  }

  async waive(): Promise<void> {}
}

class FakePayments implements FinePayments {
  readonly calls: Array<{ amountCents: number; options?: ChargeOptions }> = [];

  constructor(private readonly outcome: PaymentOutcome | 'hang') {}

  charge(_token: string, amountCents: number, _description: string, options?: ChargeOptions): Promise<PaymentOutcome> {
    this.calls.push({ amountCents, options });
    if (this.outcome === 'hang') {
      return new Promise(() => {});
    }
    return Promise.resolve(this.outcome);
  }
}

const clock = () => new Date('2026-10-18T10:00:00Z');

test('pays an outstanding fine and settles it with the charge id', async () => {
  const ledger = new FakeLedger([fine()]);
  const payments = new FakePayments({ ok: true, chargeId: 'ch_1' });
  await new PayOwnFine(ledger, payments, clock).run('1001', 'fine-1', 'tok_visa');
  assert.deepEqual(ledger.settled, [{ id: 'fine-1', chargeId: 'ch_1', on: '2026-10-18' }]);
  assert.deepEqual(payments.calls, [{ amountCents: 250, options: { idempotencyKey: 'fine-1' } }]);
});

test('refuses a fine that belongs to another member without charging', async () => {
  const ledger = new FakeLedger([fine({ cardNumber: '2002' })]);
  const payments = new FakePayments({ ok: true, chargeId: 'ch_1' });
  await assert.rejects(new PayOwnFine(ledger, payments, clock).run('1001', 'fine-1', 'tok_visa'), FineNotFound);
  assert.equal(payments.calls.length, 0);
  assert.equal(ledger.settled.length, 0);
});

test('does nothing for a fine that is already settled', async () => {
  const ledger = new FakeLedger([fine({ settledOn: '2026-10-02' })]);
  const payments = new FakePayments({ ok: true, chargeId: 'ch_1' });
  await new PayOwnFine(ledger, payments, clock).run('1001', 'fine-1', 'tok_visa');
  assert.equal(payments.calls.length, 0);
  assert.equal(ledger.settled.length, 0);
});

test('reports a decline to the member and leaves the fine outstanding', async () => {
  const ledger = new FakeLedger([fine()]);
  const payments = new FakePayments({ ok: false, stripeCode: 'insufficient_funds' });
  await assert.rejects(new PayOwnFine(ledger, payments, clock).run('1001', 'fine-1', 'tok_visa'), PaymentDeclined);
  assert.equal(ledger.settled.length, 0);
});

test('gives up when the provider does not answer in time', async () => {
  const ledger = new FakeLedger([fine()]);
  const payments = new FakePayments('hang');
  await assert.rejects(new PayOwnFine(ledger, payments, clock, 10).run('1001', 'fine-1', 'tok_visa'), PaymentTimedOut);
  assert.equal(ledger.settled.length, 0);
});
