// The desk screen's states, each driven on made-up data: `setup` writes
// the page the app serves for each state into a temporary folder, beside
// the app's own stylesheet, and a state opens its page.
import { cpSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const TITLE = 'The Salt Road Atlas';
const NOTICES = {
  'hold-cancelled': { status: 'cancelled', heading: 'Hold cancelled', body: 'The member is no longer in the queue for this title.' },
  'hold-not-cancelled': { status: 'rejected', heading: 'Hold not cancelled', body: 'card ending 1001 has no hold on this title' },
  'queue-failure': { status: 'failed', heading: 'Hold not cancelled', body: 'hold queue unavailable' },
};

export async function setup() {
  const { deskScreen } = await import('../main/desk-screen.ts');
  const dir = mkdtempSync(join(tmpdir(), 'desk-screens-'));
  cpSync(new URL('../main/desk.css', import.meta.url), join(dir, 'desk.css'));
  for (const [name, notice] of Object.entries(NOTICES)) writeFileSync(join(dir, `${name}.html`), deskScreen(TITLE, notice));
  return { dir };
}

export async function teardown(context) {
  if (context) rmSync(context.dir, { recursive: true, force: true });
}

const open = (name) => async (page, context) => {
  await page.goto(pathToFileURL(join(context.dir, `${name}.html`)).href);
};

export const states = {
  'hold-cancelled': open('hold-cancelled'),
  'hold-not-cancelled': open('hold-not-cancelled'),
  'queue-failure': open('queue-failure'),
};
