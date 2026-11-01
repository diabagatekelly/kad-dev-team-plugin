import assert from 'node:assert/strict';
import { test } from 'node:test';
import { InMemoryHoldQueue } from '../infra/memory/in-memory-hold-queue';
import { CancelHold } from '../lending/cancel-hold';
import { Hold } from '../lending/hold';

const isbn = '9780140449136';

async function queueWith(...cards: string[]): Promise<InMemoryHoldQueue> {
  const queue = new InMemoryHoldQueue();
  let position = 1;
  for (const card of cards) {
    await queue.enqueue(new Hold(isbn, card, position++, new Date('2026-03-01T10:00:00.000Z')));
  }
  return queue;
}

test('a second cancel of the same hold through the real queue is a rejection', async () => {
  const queue = await queueWith('1001');
  const cancel = new CancelHold(queue);
  assert.deepEqual(await cancel.run(isbn, '1001'), { status: 'cancelled' });
  const again = await cancel.run(isbn, '1001');
  assert.equal(again.status, 'rejected');
  assert.equal(await queue.lengthFor(isbn), 0);
});

test('a second cancel of the same hold is a rejection, not an error', async () => {
  const queue = await queueWith('1001');
  const cancel = new CancelHold(queue);
  await cancel.run(isbn, '1001');
  await assert.doesNotReject(() => cancel.run(isbn, '1001'));
  assert.equal((await cancel.run(isbn, '1001')).status, 'rejected');
});
