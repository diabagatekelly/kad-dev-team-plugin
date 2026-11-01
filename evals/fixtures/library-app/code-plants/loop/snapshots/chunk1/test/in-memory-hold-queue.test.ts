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
