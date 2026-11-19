# Cold read: branch slice-001-cancel-hold at `@HEAD@`

## Checks run

- `npm ci`: exit 0.
- `npm test`: exit 0; 15 run, 15 passed, 0 failed, 0 skipped; 4.1 s.
- `npm run typecheck`: exit 0.
- `npm run lint`: exit 0.

## Pairs probed

- `CancelHold` beside `PlaceHold`: a hold placed and cancelled, then placed again; the probe printed `placed, cancelled, placed`.
- The rejection reason beside the card numbers `PlaceHold` accepts: `probes/short-card.mjs` printed the whole card number for a three-character card.

## Findings

### A rejection for a short card number prints the whole number

**Severity:** Medium
**Location:** lending/cancel-hold.ts:55
**Category:** cold: new beside older
**Status:** confirmed by execution

**What's happening:** `PlaceHold` accepts a card number of any length. Cancelling for card `417` with no hold returns a rejection whose reason reads `card ending 417 has no hold on 9780141439518`: the reason is built to show the last four characters only, and for a card of three it shows all of it. `probes/short-card.mjs` printed that line.

**Why it matters:** the reason is shown to the desk and written to the log; it was built not to carry a whole card number.

**Suggested fix:** mask to a fixed shape whatever the length.

## To verify

- The desk notice's dismiss script may be attached twice when the notice is rendered a second time; confirming it needs the page in a browser, which this read did not start.
