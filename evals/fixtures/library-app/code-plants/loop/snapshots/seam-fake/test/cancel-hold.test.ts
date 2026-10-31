import assert from 'node:assert/strict';
import { test } from 'node:test';
import { CancelHold } from '../lending/cancel-hold';
import type { Hold } from '../lending/hold';
import type { HoldQueue } from '../lending/hold-queue';

const isbn = '9780140449136';
const other = '9780262033848';
const now = () => new Date('2026-03-01T10:00:00.000Z');

class FakeHoldQueue implements HoldQueue {
  readonly removed: Array<[string, string]> = [];
  constructor(private readonly present: Array<[string, string]>) {}

  async enqueue(): Promise<void> {}

  async headFor(title: string): Promise<Hold | null> {
    const first = this.present.find(([t]) => t === title);
    return first ? ({ isbn: first[0], cardNumber: first[1], position: 1, placedOn: now() } as Hold) : null;
  }

  async lengthFor(title: string): Promise<number> {
    return this.present.filter(([t]) => t === title).length;
  }

  async remove(title: string, card: string): Promise<boolean> {
    const at = this.present.findIndex(([t, c]) => t === title && c === card);
    if (at === -1) return false;
    this.present.splice(at, 1);
    this.removed.push([title, card]);
    return true;
  }
}

test("cancels the member's hold and says cancelled", async () => {
  const queue = new FakeHoldQueue([[isbn, '1001']]);
  const result = await new CancelHold(queue).run(isbn, '1001');
  assert.deepEqual(result, { status: 'cancelled' });
  assert.deepEqual(queue.removed, [[isbn, '1001']]);
});

test('rejects a cancel when the member has no hold on the title', async () => {
  const queue = new FakeHoldQueue([[isbn, '1001']]);
  const result = await new CancelHold(queue).run(isbn, '2002');
  assert.equal(result.status, 'rejected');
  assert.match(result.reason ?? '', /no hold/);
  assert.equal(await queue.lengthFor(isbn), 1);
});

test("removes only that member's hold on that title", async () => {
  const queue = new FakeHoldQueue([[isbn, '1001'], [isbn, '2002'], [other, '1001']]);
  await new CancelHold(queue).run(isbn, '1001');
  assert.equal((await queue.headFor(isbn))?.cardNumber, '2002');
  assert.equal(await queue.lengthFor(other), 1);
});
