import assert from 'node:assert/strict';
import { test } from 'node:test';
import { daysLeft } from '../lending/days-left';
import { Loan, type LoanRecord } from '../lending/loan';

const record: LoanRecord = {
  id: 'loan-1',
  isbn: '9780393356687',
  cardNumber: 'C-1001',
  checkedOutOn: '2026-10-01',
  dueOn: '2026-10-22',
  returnedOn: null,
  renewals: 0,
};

test('counts the days until the due date', () => {
  assert.deepEqual(daysLeft(new Loan(record), new Date('2026-10-19')), { kind: 'due-in', days: 3 });
});

test('an overdue loan says overdue rather than a negative count', () => {
  assert.deepEqual(daysLeft(new Loan(record), new Date('2026-10-25')), { kind: 'overdue' });
});

test('a returned loan has no countdown', () => {
  assert.equal(daysLeft(new Loan({ ...record, returnedOn: '2026-10-20' }), new Date('2026-10-21')), null);
});
