// The screen-change check's capture: every state `states.mjs` drives is
// opened in headless Chromium and saved as `<out>/<state>.png`, for
// `tools/screen_check.py compare` to hold against the committed baselines.
// Copied into the project by kad-dev-team's `ci-pipeline`; the states
// file beside it is the project's own.
//
//   node screens/capture.mjs --out <dir>      capture every state
//   node screens/capture.mjs --list           the state names, one a line
//
// `states.mjs` exports:
//   states    an object, one quoted key per state, the key being the
//             state's name (its mockup's file stem):
//               'hold-cancelled': async (page, context) => { ... }
//             The function drives the built app to that state on made-up
//             data and returns when the screen is settled.
//   setup     optional: async () => context (start the app on made-up
//             data in a temporary folder; what it returns is handed to
//             every state and to teardown)
//   teardown  optional: async (context) => {}
//
// Every state gets a fresh page of the same size, with animations off, so
// two runs of one commit give the same pixels. A state that throws is
// named in `<out>/capture-errors.json`, the others are still captured,
// and the exit code is 1: the comparison then reports it as MISSING.
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const VIEWPORT = { width: 1280, height: 720 };

const args = process.argv.slice(2);
const flag = (name) => {
  const at = args.indexOf(name);
  return at === -1 ? undefined : args[at + 1];
};

const { states, setup, teardown } = await import('./states.mjs');
const names = Object.keys(states).sort();

if (args.includes('--list')) {
  for (const name of names) console.log(name);
  process.exit(0);
}

const out = flag('--out');
if (!out) {
  console.error('usage: node screens/capture.mjs --out <dir> | --list');
  process.exit(2);
}
const captures = resolve(out);
mkdirSync(captures, { recursive: true });

const { chromium } = await import('playwright');
const browser = await chromium.launch();
const errors = {};
let context;
try {
  context = setup ? await setup() : undefined;
  for (const name of names) {
    const page = await browser.newPage({
      viewport: VIEWPORT,
      deviceScaleFactor: 1,
      reducedMotion: 'reduce',
      colorScheme: 'light',
      locale: 'en-US',
      timezoneId: 'UTC',
    });
    try {
      await states[name](page, context);
      await page.screenshot({ path: join(captures, `${name}.png`), fullPage: true, animations: 'disabled', caret: 'hide' });
      console.log(`captured ${name}`);
    } catch (error) {
      errors[name] = String(error && error.message ? error.message : error).split('\n')[0];
      console.error(`FAILED ${name}: ${errors[name]}`);
    } finally {
      await page.close();
    }
  }
} finally {
  if (teardown) await teardown(context);
  await browser.close();
}

const failed = Object.keys(errors);
if (failed.length > 0) writeFileSync(join(captures, 'capture-errors.json'), JSON.stringify(errors, null, 2));
console.log(`capture: ${names.length - failed.length} of ${names.length} states`);
process.exit(failed.length > 0 ? 1 : 0);
