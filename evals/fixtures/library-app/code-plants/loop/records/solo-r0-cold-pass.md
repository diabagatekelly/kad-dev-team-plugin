# Cold read: branch slice-001-cancel-hold at `@HEAD@`

## Checks run

- `npm ci`: exit 0.
- `npm test`: exit 0; 15 run, 15 passed, 0 failed, 0 skipped; 4.1 s.
- `npm run typecheck`: exit 0.
- `npm run lint`: exit 0.

## Pairs probed

- `CancelHold` beside `PlaceHold`: a hold placed and cancelled, then placed again; the probe printed `placed, cancelled, placed`.
- Two cards sharing a prefix on one title: `probes/prefix-cards.mjs` printed `1001 cancelled, 10017 still queued`.

## Findings

No findings.

## To verify

- The desk notice's dismiss script may be attached twice when the notice is rendered a second time; confirming it needs the page in a browser, which this read did not start.
