import assert from 'node:assert/strict';
import { test } from 'node:test';
import { InMemoryHoldQueue } from '../infra/memory/in-memory-hold-queue';
import { CancelHold } from '../lending/cancel-hold';
import { Hold } from '../lending/hold';
import type { HoldQueue } from '../lending/hold-queue';

const isbn = '9780140449136';
const other = '9780262033848';

async function queueWith(...holds: Array<[string, string]>): Promise<InMemoryHoldQueue> {
  const queue = new InMemoryHoldQueue();
  let position = 1;
  for (const [title, card] of holds) {
    await queue.enqueue(new Hold(title, card, position++, new Date('2026-03-01T10:00:00.000Z')));
  }
  return queue;
}

test("cancels the member's hold and says cancelled", async () => {
  const queue = await queueWith([isbn, '1001']);
  const result = await new CancelHold(queue).run(isbn, '1001');
  assert.deepEqual(result, { status: 'cancelled' });
  assert.equal(await queue.lengthFor(isbn), 0);
});

test('rejects a cancel when the member has no hold on the title', async () => {
  const queue = await queueWith([isbn, '1001']);
  const result = await new CancelHold(queue).run(isbn, '2002');
  assert.equal(result.status, 'rejected');
  assert.match(result.reason ?? '', /no hold/);
  assert.equal(await queue.lengthFor(isbn), 1);
});

test("removes only that member's hold on that title", async () => {
  const queue = await queueWith([isbn, '1001'], [isbn, '2002'], [other, '1001']);
  await new CancelHold(queue).run(isbn, '1001');
  assert.equal((await queue.headFor(isbn))?.cardNumber, '2002');
  assert.equal(await queue.lengthFor(other), 1);
});

test('the rejection reason shows only the last four digits of the card', async () => {
  const queue = await queueWith();
  const result = await new CancelHold(queue).run(isbn, '4111222233334444');
  assert.match(result.reason ?? '', /card ending 4444/);
  assert.doesNotMatch(result.reason ?? '', /4111/);
});

test('a second cancel of the same hold is a rejection, not an error', async () => {
  const queue = await queueWith([isbn, '1001']);
  const cancel = new CancelHold(queue);
  await cancel.run(isbn, '1001');
  const again = await cancel.run(isbn, '1001');
  assert.equal(again.status, 'rejected');
});

test('a queue that cannot be reached is a rejection', async () => {
  const down: HoldQueue = {
    enqueue: async () => {},
    headFor: async () => null,
    lengthFor: async () => 0,
    remove: async () => {
      throw new Error('queue unavailable');
    },
  };
  const result = await new CancelHold(down).run(isbn, '1001');
  assert.deepEqual(result, { status: 'rejected', reason: 'hold could not be cancelled' });
});
