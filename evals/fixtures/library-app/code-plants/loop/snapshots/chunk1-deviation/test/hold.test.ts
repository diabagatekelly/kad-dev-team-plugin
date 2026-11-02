import assert from 'node:assert/strict';
import { test } from 'node:test';
import { Hold } from '../lending/hold';

test('a hold is held by the card that placed it and by no other', () => {
  const hold = new Hold('9780140449136', '1234', 1, new Date('2026-01-01T00:00:00Z'));
  assert.equal(hold.isHeldBy('1234'), true);
  assert.equal(hold.isHeldBy('9999'), false);
});
