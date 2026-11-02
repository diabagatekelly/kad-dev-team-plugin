# Cold read: run1

Project root: `/private/tmp/claude-501/-Users-kellydiabagate-Documents-portfolio-kad-dev-team-plugin/1feb7624-a2f5-4db1-9405-d0396ed402a4/scratchpad/cold/run1`
Probes: `/private/tmp/claude-501/-Users-kellydiabagate-Documents-portfolio-kad-dev-team-plugin/1feb7624-a2f5-4db1-9405-d0396ed402a4/scratchpad/cold/probe-run1/` (`p1-second-connect.ts`, `p2-secret-at-complete.ts`, `p3-empty-pull.ts`, `p4-location-case.ts`, each run with `node <file>` on Node v24.22.2). No file in the tree was changed (`git status --short` is empty after the probes).

## Checks run

`pnpm` is not on PATH in this shell, so every command ran through `corepack pnpm`, which resolved the manifest's pinned pnpm 10.34.7.

| Command | Exit |
|---|---|
| `corepack pnpm install --frozen-lockfile` | 0 |
| `corepack pnpm typecheck` (`tsc --noEmit`) | 0 |
| `corepack pnpm test` (`vitest run --coverage`): 20 files, 372 tests passed. Coverage: 99.13% statements, 98.18% branches, 97.46% functions, 99.66% lines (thresholds 95) | 0 |
| lint | not run: the manifest has no lint script |
| format check | not run: the manifest has no format script |

## Findings

### The server accepts a second connection, tells the owner it succeeded, then never uses it

**Severity:** High
**Location:** src/account-connection/account-connection.ts:63 (also :71; src/sqlite-store/sqlite-ledger.ts:35)
**Category:** data integrity
**Status:** confirmed by execution

**What's happening:** Neither `start()` nor `complete()` checks whether an account is already connected. The only guard is in the browser: `TransactionsScreen` hides Connect once its own overview shows an account. Picture two tabs, or one tab left open from before the connect. Both show "No accounts connected", and each runs a bank login. The server then completes both, and Plaid creates two Items. `connected_accounts` gets two rows, and the second tab is told "Bank B connected". But `connectedAccount()` returns `ORDER BY rowid LIMIT 1`, so the overview, the pull and every later read use only the first account. Probe `p1-second-connect.ts` (real SQLite ledger and attempt log, a fake bank feed that counts Items): `tab B {"kind":"connected","account":{"displayName":"Bank B",...}}`, `plaid items created 2`, both `conn-1` and `conn-2` rows present, and `ledger.connectedAccount()` returns `{ connectionId: 'conn-1', displayName: 'Bank A' }`.
**Why it matters:** The app's own copy treats each Plaid connection as a limited lifetime slot. Here one is spent on an Item that nothing will ever read, its sealed token sits in `bank_connections`, and the owner was told it worked. No test covers a second completion with a different token.
**Suggested fix:** Refuse `start` and `complete` on the server, with a new `already-connected` outcome, when `ledger.connectedAccount()` is non-null. Check again inside `complete` before calling the bank feed, and add a use-case test for it.

### A secret-store failure after a successful bank login is reported as "Nothing was connected"

**Severity:** Medium
**Location:** src/plaid-bank-feed/plaid-bank-feed.ts:113 (also src/account-connection/account-connection.ts:40)
**Category:** correctness
**Status:** confirmed by execution

**What's happening:** `completeConnection` runs only after Plaid Link's `onSuccess`, which is the moment the code's own comments (plaid-bank-feed.ts:114, plaid-bank-feed.test.ts:247) say Plaid creates the connection and spends a slot. But it calls `requireSecrets()` first. If a secret is missing, invalid or unreadable at that point, the failure is thrown without `connectionMayExist`. `completeOnce` then reports it with `providerCompleted = false`. Probe `p2-secret-at-complete.ts` uses a secret source that answers for `/connect/start` and then throws on the key read. It gives `complete {"kind":"unexpected","errorRef":"err-1","connectionMayExist":false}`, an Activity row with no `connectionMayExist`, and the owner is shown "Something unexpected went wrong. Nothing was connected." The `missing-secret` case reaches the same outcome, and account-connection.test.ts ("reports a failure before the provider created anything as not connected") asserts it as correct.
**Why it matters:** This is the exact case the "Connection may not be finished / don't connect again" warning exists for. The owner is told nothing happened and invited to retry, which spends another slot while the first Item is orphaned.
**Suggested fix:** Treat every failure inside `completeConnection` as `connectionMayExist: true`, including `requireSecrets`, or pass `providerCompleted: true` from `completeOnce`, since the browser only calls complete after Link succeeded. Then correct the test that asserts the opposite.

### A first pull that records zero transactions locks Pull in the UI forever, though the server would allow another

**Severity:** Medium
**Location:** src/web/TransactionsScreen.tsx:112
**Category:** correctness
**Status:** confirmed by execution

**What's happening:** The server decides "already pulled" from the ledger: `hasTransactions(connectionId)`. The browser decides it from `view.transactions.length > 0 || view.lastPull !== null`, and `lastPull` is the last *successful* pull attempt even when it recorded 0. A new account whose complete history is still all pending gives `pulled` with `count: 0`. From then on the Pull button is `aria-disabled`, `pull()` returns early, and the note says "Pulling new transactions is coming next", even though the server would fetch again. Probe `p3-empty-pull.ts`: pull 1 gives `{ kind: 'pulled', count: 0, earliestDate: null }`. The overview then has `"transactions":[]` and `"lastPull":{...,"count":0}`, which makes the UI flag `true` (locked). A second `pull()` on the same server gives `{ kind: 'pulled', count: 1 }`.
**Why it matters:** The owner sees an empty ledger with no way to retry from the app, while the server would have brought the history in on a second try.
**Suggested fix:** Have the overview carry the server's own "already pulled" fact (`hasTransactions`) and gate the button on that, or gate on `transactions.length > 0` / `pulledHere.count > 0` rather than on `lastPull !== null`.

### The "not inside the project folder" check is case-sensitive on macOS and WSL drives, where the file system is not

**Severity:** Low
**Location:** src/sqlite-store/database-location.ts:64
**Category:** security
**Status:** confirmed by execution

**What's happening:** `ignoreCase` is true only for `win32`, but the default macOS volume (APFS) is case-insensitive, and so are `/mnt/c` drives under WSL. Node's `realpathSync` does not normalise case. As a result, `FLOW_MONEY_DB_PATH` spelled with different case lands inside the project folder without being refused. Probe `p4-location-case.ts` on this Mac: the exact-case path inside the worktree is refused ("Refusing to keep the database at …"). The same path with `run1` changed to `RUN1` exists and has the same inode, and `resolveDatabasePath` returns it.
**Why it matters:** The guard exists to keep the financial database out of the project tree, where it could be copied or committed. It can be bypassed by an ordinary typo in case. `.gitignore` covers `*.sqlite`, which limits the damage.
**Suggested fix:** Compare case-insensitively on `darwin` too, and on `/mnt/<drive>` paths under Linux, or compare `realpathSync.native` results, which return the canonical case on macOS.

### The database file is created world-readable

**Severity:** Low
**Location:** src/sqlite-store/database.ts:56 (folder: src/server/main.ts:27)
**Category:** security
**Status:** confirmed by execution

**What's happening:** `openDatabase` lets SQLite create the file with the process umask, and `mkdirSync(..., { recursive: true })` creates the data folder the same way. With the usual umask 022 the file is mode 0644 and the folder 0755. Probe `p4-location-case.ts`: `db file mode 644 umask 22`. On Linux/WSL the default location is `~/.local/share/flow-money/`, so any other local account that can traverse the home folder can read the full transaction history and account names. The access tokens are sealed; nothing else in the file is.
**Why it matters:** The full transaction history and account names can be read by other local accounts. On a shared machine that is a disclosure.
**Suggested fix:** Create the folder with `mode: 0o700` and create or `chmod` the database file to `0o600` before opening it (on POSIX).

### A bank login that returns no account or no token is never recorded, but the message sends the owner to Activity

**Severity:** Low
**Location:** src/web/ConnectControl.tsx:36
**Category:** reliability
**Status:** confirmed by execution

**What's happening:** When Link's `onSuccess` gives no public token or no selected account, `complete` shows `no-account-selected` ("Connection may not be finished … See Activity for what happened") and calls nothing on the server. No attempt is recorded, so Activity has no row for it. The suite's passing test "says the connection may not be finished, without calling the app, when the bank login names no account" confirms the call is never made (`api.called('completeConnect')` is `[]`, and no `reportAbandoned` call is made either).
**Why it matters:** This is a case where Plaid may have created an Item. The one lasting record the owner is told to check before connecting again does not have it.
**Suggested fix:** Report it to the server, for example via the abandoned endpoint with a distinct reason, or a small `/api/connect/incomplete` that records `connectionMayExist: true`, before showing the message.

## Counts

Critical 0, High 1, Medium 2, Low 3
