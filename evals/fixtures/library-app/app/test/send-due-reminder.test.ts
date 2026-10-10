import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { LoanRecord } from '../lending/loan';
import type { Letter } from '../notifications/postal-queue.port';
import { EmailReminder } from '../notifications/email-reminder';
import { PostalReminder } from '../notifications/postal-reminder';
import { SendDueReminder } from '../notifications/send-due-reminder';
import { SmsReminder } from '../notifications/sms-reminder';
import { postalMember, smsMember } from './fixtures/members';

const loan: LoanRecord = {
  id: 'loan-1',
  isbn: '9780140449136',
  cardNumber: smsMember.card_number,
  checkedOutOn: '2026-03-01T10:00:00.000Z',
  dueOn: '2026-03-22T10:00:00.000Z',
  returnedOn: null,
  renewals: 0,
};

function reminders() {
  const texts: Array<{ phone: string; body: string }> = [];
  const letters: Letter[] = [];
  const remind = new SendDueReminder(
    new EmailReminder({ send: async () => {} }),
    new SmsReminder({ sendText: async (phone, body) => void texts.push({ phone, body }) }),
    new PostalReminder({ queue: async (letter) => void letters.push(letter) }),
  );
  return { remind, texts, letters };
}

test('texts a member who prefers SMS', async () => {
  const { remind, texts, letters } = reminders();
  await remind.run(smsMember, loan);
  assert.deepEqual(texts, [{ phone: smsMember.phone, body: 'Library: 9780140449136 is due 2026-03-22.' }]);
  assert.equal(letters.length, 0);
});

test('queues a letter for a member who prefers post', async () => {
  const { remind, texts, letters } = reminders();
  await remind.run(postalMember, { ...loan, cardNumber: postalMember.card_number });
  assert.equal(texts.length, 0);
  assert.deepEqual(letters, [
    { address: postalMember.postal_address, recipient: postalMember.full_name, body: 'The book 9780140449136 is due on 2026-03-22.' },
  ]);
});
