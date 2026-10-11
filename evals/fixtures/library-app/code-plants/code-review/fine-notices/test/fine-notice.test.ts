import assert from 'node:assert/strict';
import { mock, test } from 'node:test';
import type { Fine } from '../fines/fine';
import * as notices from '../notifications/fine-notice';
import { postalMember, smsMember } from './fixtures/members';

const fine: Fine = {
  id: 'fine-1',
  loanId: 'loan-1',
  cardNumber: smsMember.card_number,
  amountCents: 125,
  assessedOn: '2026-04-19',
  settledOn: null,
  waived: false,
};

test('works', () => {
  assert.equal(notices.smsFineNotice([fine]), 'Library: 1 fine, $1.25 owed. Pay at the desk or in the portal.');
});

test('works', () => {
  const build = mock.fn(notices.build, () => 'notice');
  build(postalMember, [fine]);
  assert.equal(build.mock.callCount(), 1);
});
