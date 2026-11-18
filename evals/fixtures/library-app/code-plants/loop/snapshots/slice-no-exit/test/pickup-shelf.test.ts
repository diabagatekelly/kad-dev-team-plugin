import assert from 'node:assert/strict';
import { test } from 'node:test';
import { InMemoryHoldQueue } from '../infra/memory/in-memory-hold-queue';
import { InMemoryPickupShelf } from '../infra/memory/in-memory-pickup-shelf';
import { CancelHold } from '../lending/cancel-hold';
import { CollectHold } from '../lending/collect-hold';
import { Hold } from '../lending/hold';

const isbn = '9780140449136';
const placedOn = new Date('2026-03-01T10:00:00.000Z');

async function readyHold(): Promise<{ queue: InMemoryHoldQueue; shelf: InMemoryPickupShelf }> {
  const queue = new InMemoryHoldQueue();
  await queue.enqueue(new Hold(isbn, '1001', 1, placedOn));
  await queue.enqueue(new Hold(isbn, '2002', 2, placedOn));
  const shelf = new InMemoryPickupShelf();
  shelf.setAside(isbn, '1001');
  return { queue, shelf };
}

test('cancelling a hold with a copy set aside releases the copy and removes the hold', async () => {
  const { queue, shelf } = await readyHold();
  const result = await new CancelHold(queue, shelf).run(isbn, '1001');
  assert.deepEqual(result, { status: 'cancelled' });
  assert.equal(await shelf.release(isbn, '1001'), 'nothing-set-aside');
  assert.equal((await queue.headFor(isbn))?.cardNumber, '2002');
});

test('a shelf that does not release the copy turns the cancel down and keeps the hold', async () => {
  const { queue, shelf } = await readyHold();
  shelf.reportNotFound(isbn, '1001');
  const result = await new CancelHold(queue, shelf).run(isbn, '1001');
  assert.equal(result.status, 'rejected');
  assert.match(result.reason ?? '', /nothing was changed/);
  assert.equal(await queue.lengthFor(isbn), 2);
  assert.equal((await queue.headFor(isbn))?.cardNumber, '1001');
});

test('the member next in the queue collects the copy set aside and leaves the queue', async () => {
  const { queue, shelf } = await readyHold();
  const result = await new CollectHold(queue, shelf).run(isbn, '1001');
  assert.deepEqual(result, { status: 'collected' });
  assert.equal((await queue.headFor(isbn))?.cardNumber, '2002');
});

test('a member who is not next cannot collect', async () => {
  const { queue, shelf } = await readyHold();
  const result = await new CollectHold(queue, shelf).run(isbn, '2002');
  assert.equal(result.status, 'rejected');
  assert.equal(await queue.lengthFor(isbn), 2);
});
