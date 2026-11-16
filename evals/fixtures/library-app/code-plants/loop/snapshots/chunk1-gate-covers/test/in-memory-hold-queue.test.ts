import assert from 'node:assert/strict';
import { test } from 'node:test';
import { InMemoryHoldQueue } from '../infra/memory/in-memory-hold-queue';
import { Hold } from '../lending/hold';

const isbn = '9780140449136';
const placedOn = new Date('2026-03-01T10:00:00.000Z');

test("in-memory queue removes one member's hold and says whether it was there", async () => {
  const queue = new InMemoryHoldQueue();
  await queue.enqueue(new Hold(isbn, '1001', 1, placedOn));
  await queue.enqueue(new Hold(isbn, '2002', 2, placedOn));
  assert.equal(await queue.remove(isbn, '1001'), true);
  assert.equal(await queue.remove(isbn, '1001'), false);
  assert.equal(await queue.lengthFor(isbn), 1);
  assert.equal((await queue.headFor(isbn))?.cardNumber, '2002');
});

test('a title nobody holds has no head, no length and nothing to remove', async () => {
  const queue = new InMemoryHoldQueue();
  assert.equal(await queue.headFor('9780000000000'), null);
  assert.equal(await queue.lengthFor('9780000000000'), 0);
  assert.equal(await queue.remove('9780000000000', '1001'), false);
});

test('an ISBN written with hyphens or spaces names the same title', async () => {
  const queue = new InMemoryHoldQueue();
  await queue.enqueue(new Hold('978-0-14-044913-6', '1001', 1, placedOn));
  assert.equal(await queue.lengthFor(isbn), 1);
  assert.equal((await queue.headFor('978 0140449136'))?.cardNumber, '1001');
  assert.equal(await queue.remove('978-0140449136', '1001'), true);
  assert.equal(await queue.lengthFor(isbn), 0);
});
