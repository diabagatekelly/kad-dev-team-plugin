# Cold read: run3

Every file under `src/` and `test/` was read in full. Protocol note: I read `README.md` past its run instructions (one `sed -n 1,80p`) before stopping, so I have seen its "does / does not" section. No other file outside `src/`, `test/` and the manifests was opened. The git log was not read. All probes live in `<probe dir>/`. Each imports the worktree by absolute path and uses only the repo's own fakes or local servers. After all runs, `git status --short` in the worktree was empty.

## Checks run

`pnpm` is not on PATH on this machine, so each command ran as `corepack pnpm ...`. Corepack resolved pnpm 10.34.9, the version the manifest pins. Node v24.22.2.

| Command | Exit |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` | 0 |
| `corepack pnpm run typecheck` (`tsc --noEmit`) | 0 |
| `corepack pnpm run lint` (`eslint .`) | 0 |
| `corepack pnpm run format:check` (`prettier --check .`) | 0 |
| `corepack pnpm test` (`node --test "test/*.test.ts"`) | 0: 184 tests, 184 pass, 0 fail, 0 skipped, about 11 s |

## Findings

### A retrieval Plaid refuses can never recover: the page says "Connect again", reconnecting is turned down and revoked, and Try again repeats the refusal

**Severity:** High
**Location:** src/web/render-page.ts:78 (with src/ledger/institution-connections.ts:22-28 and src/ledger/try-again.ts:11)
**Category:** correctness
**Status:** confirmed by execution

**What's happening:** When the first sync is refused (for example `ITEM_LOGIN_REQUIRED`), the connection stays stored as "not retrieved yet". The card then tells the owner to "Connect Chime again, or try another bank." Following that advice cannot work:
- The pre-login check answers `alreadyConnected: true`.
- A fresh login that completes anyway is handed to `addUnlessConnected`, answered 409 "Chime is already connected", and its new access token is revoked.
- Try again reuses the stored, broken access token, so it gets the same refusal.

There is no disconnect and no Plaid update-mode path, so the institution is stuck until the ledger file is deleted. Probe `p1-refusal-deadend.ts` (fake Plaid with `refuseSyncWith: "ITEM_LOGIN_REQUIRED"`) printed:
```
1st login: 200
page says: Plaid refused to give Chime&#39;s transactions. Connect Chime again, or try another bank. Reference op-d5d57055.
check before relogin: {"alreadyConnected":true,"message":"Chime is already connected"}
relogin: 409 {"error":"Chime is already connected"} revoked: ["access-chime:relogin"]
try again: 202
after try again: {"institutionId":"chime","name":"Chime","state":"not retrieved yet","stop":{"reason":"refusal","reference":"op-0fc0d906"}}
sync tokens used: ["access-chime"]
```
`test/seam-operation-log.test.ts` encodes this behaviour as expected: after a refused retrieval, a second Chime login gets 409.
**Why it matters:** A routine Plaid refusal (an expired bank login is the common one) permanently stops that bank from ever showing transactions. The only advice on screen leads straight into the duplicate guard and burns a Plaid login each time.
**Suggested fix:** Let a login replace a stored connection that was never retrieved (or whose last stop was a refusal): save the new one and revoke the old token, not the new one. Alternatively, offer Plaid update mode for the stored item and change the wording to match.

### An exchange that went through at Plaid but whose answer was lost leaves a live Plaid item the app never revokes or names

**Severity:** Medium
**Location:** src/ledger/connect-institution.ts:44-50
**Category:** reliability
**Status:** confirmed by execution (against a local fake; whether real Plaid refuses a second exchange of the same token is the code's own assumption)

**What's happening:** `exchangeWithRetries` retries an exchange that timed out or answered 5xx. If the first attempt actually spent the public token, the retry is refused. The outcome is then "not completed" with no `itemToRemove`, because the access token and item id were never received. The log line records that refusal as `expected: true`. The person is told "Connect again", which creates a second item. Probe `p2-orphan-exchange.ts` uses a local fake whose exchange succeeds server-side but answers after the 100 ms client timeout. It printed:
```
outcome: not completed itemToRemove: undefined
access tokens Plaid issued: [ 'access-1' ] revoked: [] stored connections: 0
log records: [{"reference":"op-probe","step":"exchange","outcome":"not completed","expected":true,"errorType":"INVALID_INPUT","errorCode":"INVALID_PUBLIC_TOKEN","status":400}]
```
**Why it matters:** This orphans a remote resource that nothing in the app can find or remove. It is logged as an expected outcome, so it does not stand out in the log either.
**Suggested fix:** Treat "refused after an unanswered attempt" as unexpected and say on screen and in the log that a Plaid item may have been left behind (the Plaid dashboard can list items). Consider not retrying an exchange after a timeout at all, since a timeout is exactly the case where the token may already be spent.

### Ctrl-C during a connect orphans the Plaid item with no log line

**Severity:** Medium
**Location:** src/start.ts:24
**Category:** reliability
**Status:** confirmed by execution

**What's happening:** Only SIGTERM is handled, and that path does drain the in-flight request. SIGINT, which is what Ctrl-C under `pnpm start` sends, kills the process at once. Between the exchange and the save, the app holds a live access token while it looks up the accounts. With the retry waits and 30 s timeouts that window can last minutes. Probe `p6-signal.ts` ran `test/support/test-main.ts` against the fake Plaid with `failAccountsGet: 2` and sent each signal once `/accounts/get` had been reached:
```
SIGINT exit: null/SIGINT response: fetch failed: UND_ERR_SOCKET item/remove calls: 0 exchanged: 1
SIGTERM exit: 0/null response: 200 item/remove calls: 0 exchanged: 1
```
On SIGINT the item was exchanged, nothing was stored or revoked, and nothing was written to the log.
**Why it matters:** The usual way to stop a local dev server leaves an unrecorded, unrevocable Plaid item, and the owner gets no message about it.
**Suggested fix:** Register the same graceful close for SIGINT. Also write a "pending" operation record carrying the `itemId` right after the exchange, so an interrupted connect leaves something to act on.

### The first retrieval stores only this month but saves the cursor past everything it dropped, and at a month boundary it drops the month being shown

**Severity:** Medium
**Location:** src/ledger/retrieve-first-transactions.ts:26-29
**Category:** data integrity
**Status:** confirmed by execution

**What's happening:** `saveRetrieval` saves `nextCursor`, the end of the item's whole history, but keeps only the transactions where `isInMonth(t, currentMonth(clock))` is true. The month is read after the fetch returns. Everything else that was fetched is discarded, and a sync from the stored cursor will never return it again. The connection is marked "retrieved", so Try again answers "nothing to retry". In probe `p3-cursor.ts` a retrieval started on 2026-11-30 and saved after midnight. It kept only the 2026-12-01 transaction and dropped the 2026-11-30 one:
```
stored transactions: [ 'dec-1' ] status: retrieved cursor: cursor-boa-1
a later sync from the stored cursor returns: []
```
The same mechanism means that from next month on, the earlier months' history is unrecoverable through the stored cursor.
**Why it matters:** Transactions Plaid delivered are silently and permanently lost. Neither the app nor any later sync from the saved cursor can get them back.
**Suggested fix:** Store every transaction the sync returns and filter by month only when building the view. If storage really must be limited, do not advance the stored cursor past transactions that were not kept.

### A ledger folder that cannot be read at start is taken as "no ledger", and new keys are minted over the stored data

**Severity:** Low
**Location:** src/compose.ts:57-61, 74-83
**Category:** data integrity
**Status:** confirmed by execution

**What's happening:** `exists()` maps every `stat` error to `false`, including EACCES. When the ledger's keys are missing and its folder is unreadable at start, the app creates a new `token-key` and `database-key`, then crashes on `readFile`. This breaks the rule that a key is only made "while nothing is encrypted with it". Probe `p7-stat.ts` (stored ledger file, both keys absent, folder `chmod 000`) printed:
```
start failed: EACCES: permission denied, open '.../data/ledger.enc'
Keychain items now: [ 's/token-key', 's/database-key' ]
```
Once the folder is readable again, the app fails authentication on start instead of showing the locked-ledger page. Because `create` refuses an existing item, putting the original keys back means deleting the new ones first.
**Why it matters:** It is a narrow path, but it silently changes the owner's Keychain and turns a recoverable "restore the missing key" state into a crash.
**Suggested fix:** Treat only ENOENT as absent and rethrow any other `stat` error.

### A port already in use crashes the process with an unhandled 'error' event

**Severity:** Low
**Location:** src/web/server.ts:297
**Category:** reliability
**Status:** confirmed by execution

**What's happening:** `server.listen(port, "127.0.0.1", resolve)` has no `'error'` listener, so `EADDRINUSE` is thrown as an unhandled event. It is not a rejection of `startServer`, so a caller's `try/catch` cannot handle it. Probe `p5-port.ts` wraps `startServer` in a try/catch on an occupied port and printed `process exit code 1` followed by `throw er; // Unhandled 'error' event ... Error: listen EADDRINUSE: address already in use 127.0.0.1:52403`. The catch block never ran.
**Why it matters:** Starting a second copy of the app, or running with port 3000 taken, dies with a stack trace instead of a message.
**Suggested fix:** Reject the startup promise from a one-time `'error'` listener on the server, and print a plain message in `start`.

### The "not in the project or an iCloud folder" guard is case-sensitive and lets a "..name" folder through

**Severity:** Low
**Location:** src/store/local-ledger-store.ts:25-38
**Category:** security
**Status:** confirmed by execution

**What's happening:** `isInside` compares paths byte for byte and treats any relative path that starts with `..` as outside. Probe `p4-location.ts` with home `/Users/someone` accepted `/Users/someone/documents/ledger.enc` and `/Users/someone/DESKTOP/ledger.enc`. On macOS's default case-insensitive volume these are the iCloud-synced Documents and Desktop folders; this machine resolves both `~/documents` and `~/Documents`. It also accepted `<project>/..ledger/ledger.enc`, which is inside the project folder. Symlinks are not resolved either. Production passes a fixed path, so today this is only reachable through `createApp`'s configuration.
**Why it matters:** The guard exists to keep the encrypted ledger out of synced or committed folders, and it can be bypassed by spelling the path differently.
**Suggested fix:** Compare `realpath` results case-folded on macOS, and test `from === ".." || from.startsWith(".." + sep)` instead of `startsWith("..")`.

## Counts

Critical 0, High 1, Medium 3, Low 3
