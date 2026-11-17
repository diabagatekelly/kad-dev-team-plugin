import assert from 'node:assert/strict';
import { test } from 'node:test';
import { InMemoryHoldQueue } from '../infra/memory/in-memory-hold-queue';
import { CancelHold } from '../lending/cancel-hold';

test('a card number far longer than a library card is rejected before the queue is asked', async () => {
  const result = await new CancelHold(new InMemoryHoldQueue()).run('9780140449136', '1001'.repeat(10));
  assert.deepEqual(result, { status: 'rejected', reason: 'card number too long' });
});
