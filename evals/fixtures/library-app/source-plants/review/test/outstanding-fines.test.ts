import assert from 'node:assert/strict';
import { test } from 'node:test';
import { isOutstanding } from '../fines/fine';
import { deskFees } from './fixtures/desk-fees';

test('a fee the desk has not settled is outstanding', () => {
  assert.equal(isOutstanding(deskFees[0]), true);
});

test('a fee settled at the desk is not outstanding', () => {
  assert.equal(isOutstanding(deskFees[1]), false);
});

test('a waived fee is not outstanding', () => {
  assert.equal(isOutstanding({ ...deskFees[0], waived: true }), false);
});
