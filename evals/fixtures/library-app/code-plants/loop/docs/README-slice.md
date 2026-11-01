# library-lending

A lending service for a community library: catalog, members, loans,
fines, reminders and reporting. This branch adds the first slice of hold
cancelling: desk staff cancel one member's hold on one title.

## Prerequisites

- Node.js 24 (`node --version`), which ships the test runner this project
  uses.
- npm, which comes with Node.
- No external account is needed for this slice: holds live in memory.

## Clone to running

1. `git clone <this repository> library-lending && cd library-lending`
2. `npm test` runs the suite; the app itself (`npm start`) needs the
   Postgres, email, SMS and payment packages this slice does not touch,
   and no route serves hold cancelling yet (that is slice 2).

## Tests and checks

- `npm test`: the suite, in place, with Node's test runner.
- `npm run typecheck`: TypeScript.
- `npm run lint`: ESLint.

CI runs the same three on every pull request.

## Where things live

- Holds are kept in memory by the running process; nothing is written to
  disk for this slice.
- Logs go to standard output.
- No local secrets file is needed for this slice.

## What this slice does and does not

- Cancels one member's hold on one title and says so.
- Turns down a cancel for a hold the member does not have, with a reason.
- Reports a queue that cannot be reached as a failure, with nothing
  half-removed.
- Not yet: the staff HTTP route, member self-service cancelling, telling
  the next member they moved up.
