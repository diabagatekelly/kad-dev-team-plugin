import assert from 'node:assert/strict';
import { mock, test } from 'node:test';
import type { LoanRecord } from '../lending/loan';
import { AssessOverdueFine } from '../fines/assess-overdue-fine';
import type { Fine } from '../fines/fine';
import { isOutstanding } from '../fines/fine';
import { roundHalfUpCents } from '../fines/money';
import { FakeFineLedger } from './fakes/fake-fine-ledger';

const today = new Date('2026-04-20T09:00:00.000Z');
const clock = () => today;

function loanDue(dueOn: string): LoanRecord {
  return {
    id: 'loan-1',
    isbn: '9780140449136',
    cardNumber: 'card-1',
    checkedOutOn: '2026-03-01T09:00:00.000Z',
    dueOn,
    returnedOn: null,
    renewals: 0,
  };
}

const outstandingFine: Fine = {
  id: 'fine-1',
  loanId: 'loan-1',
  cardNumber: 'card-1',
  amountCents: 100,
  assessedOn: '2026-04-19',
  settledOn: null,
  waived: false,
};

test('charges 25 cents a day after the three-day grace period', async () => {
  const ledger = new FakeFineLedger();
  const fine = await new AssessOverdueFine(ledger, clock).run(loanDue('2026-04-13T09:00:00.000Z'));
  assert.equal(fine?.amountCents, 100);
  assert.deepEqual(ledger.recorded, [fine]);
});

test('does not charge inside the grace period', async () => {
  const ledger = new FakeFineLedger();
  const record = mock.fn();
  await new AssessOverdueFine(ledger, clock).run(loanDue('2026-04-18T09:00:00.000Z'));
  assert.equal(record.mock.callCount(), 0);
});

test('caps the fine at ten dollars', async () => {
  const ledger = new FakeFineLedger();
  const fine = await new AssessOverdueFine(ledger, clock).run(loanDue('2025-10-01T09:00:00.000Z'));
  assert.ok(fine !== null && fine.amountCents > 0);
});

test('does not assess a loan that already has an outstanding fine', async () => {
  const ledger = new FakeFineLedger();
  mock.method(ledger, 'outstandingFor', async () => [outstandingFine]);
  const fine = await new AssessOverdueFine(ledger, clock).run(loanDue('2026-04-13T09:00:00.000Z'));
  assert.equal(fine, null);
  assert.equal(ledger.recorded.length, 0);
});

test('looks up outstanding fines before recording a new one', async () => {
  const ledger = new FakeFineLedger();
  const calls: string[] = [];
  mock.method(ledger, 'outstandingFor', async () => {
    calls.push('outstandingFor');
    return [];
  });
  mock.method(ledger, 'record', async () => {
    calls.push('record');
  });
  await new AssessOverdueFine(ledger, clock).run(loanDue('2026-04-13T09:00:00.000Z'));
  assert.deepEqual(calls, ['outstandingFor', 'record']);
});

test('returns the assessed fine', async () => {
  const assess = new AssessOverdueFine(new FakeFineLedger(), clock);
  mock.method(assess, 'run', async () => outstandingFine);
  const fine = await assess.run(loanDue('2026-04-13T09:00:00.000Z'));
  assert.equal(fine, outstandingFine);
});

test('an unsettled, unwaived fine is outstanding', () => {
  assert.equal(isOutstanding(outstandingFine), true);
});

test('a settled fine is not outstanding', () => {
  assert.equal(isOutstanding({ ...outstandingFine, settledOn: '2026-04-20' }), false);
});

test('a waived fine is not outstanding', () => {
  assert.equal(isOutstanding({ ...outstandingFine, waived: true }), false);
});

test('rounds half a cent up', () => {
  assert.equal(roundHalfUpCents(12.5), 13);
  assert.equal(roundHalfUpCents(12.49), 12);
});
