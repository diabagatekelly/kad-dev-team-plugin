import { test } from 'node:test';
import assert from 'node:assert/strict';
import { deskScreen } from '../main/desk-screen';

test('the desk screen carries the notice with its status class', () => {
  const html = deskScreen('The Salt Road', { status: 'rejected', heading: 'Hold not cancelled', body: 'card ending 1001 has no hold on this title' });
  assert.match(html, /<section class="notice notice--rejected" role="status">/);
  assert.match(html, /<h2>Hold not cancelled<\/h2>/);
});

test('the desk screen escapes the title and the notice text', () => {
  const html = deskScreen('Fish & <Chips>', { status: 'cancelled', heading: 'Hold cancelled', body: 'a "quoted" body' });
  assert.match(html, /Holds desk: Fish &amp; &lt;Chips&gt;/);
  assert.match(html, /a &quot;quoted&quot; body/);
});
