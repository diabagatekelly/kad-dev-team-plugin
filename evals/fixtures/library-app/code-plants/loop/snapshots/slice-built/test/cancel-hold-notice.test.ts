import assert from 'node:assert/strict';
import { test } from 'node:test';
import { cancelNotice } from '../lending/cancel-hold-notice';

test('a cancelled result gets a cancelled notice', () => {
  const notice = cancelNotice({ status: 'cancelled' });
  assert.equal(notice.heading, 'Hold cancelled');
  assert.match(notice.markup, /notice--cancelled/);
});

test('a rejected result carries its reason into the notice', () => {
  const notice = cancelNotice({ status: 'rejected', reason: 'card ending 4444 has no hold on 9780140449136' });
  assert.equal(notice.heading, 'Hold not cancelled');
  assert.match(notice.body, /card ending 4444/);
});
