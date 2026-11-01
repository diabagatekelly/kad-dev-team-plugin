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

test("cancels a member's hold through the real in-memory queue", async () => {
  const queue = await queueWith([isbn, '1001'], [isbn, '2002']);
  const result = await new CancelHold(queue).run(isbn, '1001');
  assert.deepEqual(result, { status: 'cancelled' });
  assert.equal((await queue.headFor(isbn))?.cardNumber, '2002');
  assert.equal(await queue.lengthFor(isbn), 1);
});

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

test('cancelling after the queue recovers removes the hold through the real in-memory queue', async () => {
  const queue = await queueWith([isbn, '1001']);
  let down = true;
  const flaky: HoldQueue = {
    enqueue: (hold) => queue.enqueue(hold),
    headFor: (title) => queue.headFor(title),
    lengthFor: (title) => queue.lengthFor(title),
    remove: async (title, card) => {
      if (down) throw new Error('queue unavailable');
      return queue.remove(title, card);
    },
  };
  const cancel = new CancelHold(flaky);
  assert.equal((await cancel.run(isbn, '1001')).status, 'failed');
  assert.equal(await queue.lengthFor(isbn), 1);
  down = false;
  assert.deepEqual(await cancel.run(isbn, '1001'), { status: 'cancelled' });
  assert.equal(await queue.lengthFor(isbn), 0);
});

test('a queue that cannot be reached fails the cancel and leaves the queue as it was', async () => {
  const down: HoldQueue = {
    enqueue: async () => {},
    headFor: async () => null,
    lengthFor: async () => 1,
    remove: async () => {
      throw new Error('queue unavailable');
    },
  };
  const result = await new CancelHold(down).run(isbn, '1001');
  assert.deepEqual(result, { status: 'failed', reason: 'hold queue unavailable' });
  assert.equal(await down.lengthFor(isbn), 1);
});
