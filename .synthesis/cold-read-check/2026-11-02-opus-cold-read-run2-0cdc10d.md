# Cold read, run 2

Tree: `<worktree>` (detached worktree). I read every file under `src/` in full. Under `test/`, I read the adapter, store, vault, use-case, stage-log, route and cross-site test files in full. For the large screen-script suites (`plaid-connect.test.ts`, `live-status.test.ts`, `connect-failure-screen.test.tsx`, `transactions-screen.test.tsx`, `history-status-screen.test.tsx`) and the `test/repo/*` files, I read the harness setup and every test name, not each assertion body.

Probes are under `.../scratchpad/cold/probe-run2/` (`a.probe.ts`, `b.probe.ts`). They run against the worktree's real modules, the Miniflare D1 database and a fake Plaid `fetch`, through a vitest config that lives outside the tree. I changed no file in the tree, and `git status --short` stays empty.

Probe command, run from the worktree: `corepack pnpm exec vitest run --config <probe-run2>/vitest.config.mts --reporter=verbose`

## Checks run

| Command | Exit |
|---|---|
| `pnpm install --frozen-lockfile` | 127: `pnpm` is not on PATH, so I ran it through corepack as the manifest's `packageManager` field implies |
| `corepack pnpm install --frozen-lockfile` | 0 |
| `corepack pnpm typecheck` (`tsc --noEmit`) | 0 |
| lint | not run: the manifest has no lint script |
| format check | not run: the manifest has no format script |
| `corepack pnpm test` (`vitest run`) | 0: 31 files and 619 tests passed |

## Findings

### A second completed connection is exchanged, kept and reported as success, but never recorded, which orphans a live Plaid Item and its access token

**Severity:** High
**Location:** src/connect-an-account/connect-an-account.ts:114
**Category:** data integrity
**Status:** confirmed by execution

**What's happening:** `complete()` checks only whether a record already exists (`status() === "connected"`). It never checks that the caller holds the claim, and nothing serializes two completions. In the flow the page offers, window A is still in Plaid's window, and the owner presses Start over in window B (`startOver` releases A's claim and B claims). Both approve, and both `POST /connect/complete` arrive together. Both pass the status check, both exchange at Plaid, and `vault.keep` stores both access tokens. `record()` keeps the first record (`INSERT OR IGNORE`) and also deletes the claim.

Probe P1 drives the real `PlaidBankFeed`, `BankAccessVault` and `ConnectionRecordsStore` against a fake Plaid that issues a fresh item per exchange. It prints `P1 outcomes [{"kind":"connected"},{"kind":"connected"}]`, then `connection_records [{"reference":"item-1"}]`, then `bank_access refs ["item-1","item-2"]`. Probe P1b shows that `complete()` with no claim held at all also exchanges and records: it prints `{"kind":"connected"} connected`.

There is a related gap. When a record already exists, `complete()` returns `already-connected` without exchanging (the existing test "offers no second connection when Bank of America is connected" pins this). The Item Plaid made for that approval is then never exchanged, so the app has no access token to remove it with.

**Why it matters:** Each orphan is a live Plaid Item that uses up one of the ten Trial connections. The app has no `/item/remove` anywhere, so it cannot clean the orphans up. The losing window is told the connection was saved, and an unreferenced live bank access token stays in `bank_access` with nothing to show it is there.

**Suggested fix:** Have `complete` take the attempt id and refuse unless that attempt holds the claim, with the check and the record write in one guarded statement. Remove any Item whose exchange loses the race, or that arrives after a record exists, instead of keeping its token, and add a test with two concurrent completions.

### A failure after the token exchange leaves a live Item and a stored token with no record and no way to recover

**Severity:** Medium
**Location:** src/plaid-bank-feed/plaid-bank-feed.ts:97 (and connect-an-account.ts:126)
**Category:** reliability
**Status:** confirmed by execution

**What's happening:** `completeConnection` exchanges the public token and writes it to the vault. `complete()` then writes the connection record as a separate step. If that write fails (probe P2 makes `ConnectionRecordsStore.record` reject once with "D1 blip"), the request is a 500. The page maps a 500 to `SAVE_OTHER`, which has `again: false`, so it drops the connect result and offers only Start over. Even a manual retry with the same public token is refused, because Plaid accepts each public token only once.

P2 prints `first: Error: D1 blip | retry: rejected | status: connecting | vault: ["item-1"] | records: []`. The token for item-1 sits in the vault with no record pointing at it. Start over then makes a second Item.

The exchange's own retry has the same shape, but I have not confirmed it (verify against Plaid's sandbox). If an attempt times out after Plaid has done the exchange, the retry would be `INVALID_PUBLIC_TOKEN`, classified `rejected`, and the Item would be orphaned in the same way.

**Why it matters:** A transient database fault spends a Trial connection, and the app keeps a token it can neither use nor remove. Recovery is possible in principle, because the vault holds the item id and token, but no code path uses them.

**Suggested fix:** Record the connection from the vault's item id when the record write fails, or retry the record write before giving up. Treat a vault row with no record as recoverable on the next `complete` or Start over (record it, or remove the Item) instead of discarding it.

### A history step's ledger batch may exceed D1's per-invocation query limit on the free plan

**Severity:** Medium
**Location:** src/ledger-store/ledger-store.ts:29
**Category:** reliability
**Status:** verify

**What's happening:** `apply` sends one statement per saved transaction plus one per removed id in a single `db.batch`. A step can carry up to `STEP_SIZE = 100` updates. The step also makes about five other D1 calls (state, history, vault read, writeHistory, and beginHistory on the first step). The code comments target the free plan (its 10 ms CPU budget). If D1 counts each statement in a batch toward the free plan's queries-per-invocation limit (50, as I recall it), then any part with more than about 45 updates fails. That makes the step a 500, the page shows "unexpected", and history never loads past the first large page.

**Why it matters:** If the limit applies this way, the very first page of a normal account's 24-month history fails the pull, and the ledger is never filled.

**Suggested fix:** Check Cloudflare's D1 limits for how batch statements are counted. If they count individually, insert in one multi-row `INSERT ... VALUES (...),(...)` (and one `DELETE ... WHERE id IN (...)`), or lower `STEP_SIZE`. To confirm, run a step with 100 added transactions against a free-plan deployment, or against Miniflare with the limit configured.

### Every step that changes rows re-reads and re-renders the whole ledger

**Severity:** Medium
**Location:** src/app-routes/routes.tsx:168 (and src/screen/live-status.ts:226)
**Category:** reliability
**Status:** verify

**What's happening:** After each step with `rowsChanged`, the page calls `GET /history/rows`. That route runs `ledger.list()` (no limit) and renders every row to HTML. `GET /` does the same. Over a 24-month pull of N transactions in 100-row parts, the total work grows with N², and each request's cost grows with N. Under the free plan's 10 ms CPU limit, a few thousand rows probably push `/history/rows`, and later `/`, over the limit (Cloudflare error 1102). The page's `refreshRowsIfPossible` swallows that failure silently, so the list on screen stops updating while the pull continues. Once the ledger is large, the main page itself fails to load.

**Why it matters:** The app stops being able to show the data it has just saved, and nothing in the page says so.

**Suggested fix:** Return only rows added since the client's count or a cursor, or paginate the table, and bound `list()`. To confirm, seed about 3,000 transactions and time `/` and `/history/rows` against the CPU limit, either with `wrangler dev` CPU limits enabled or in a deployed free-plan Worker.

### A malformed connect-result body is a logged "unexpected" 500, and a missing token is sent to Plaid

**Severity:** Low
**Location:** src/app-routes/routes.tsx:155
**Category:** correctness
**Status:** confirmed by execution

**What's happening:** `/connect/complete` calls `c.req.json()` with no catch and no check that `publicToken` is a non-empty string. The other routes do have these checks (`attemptOf`, the cancel route). Probe P4 prints `malformed -> 500 | empty -> 502 {"error":"rejected"} | plaid bodies [{"client_id":"c","secret":"s"}]`, and the log gets `{"stage":"request","unexpected":true,"message":"SyntaxError: ..."}`. The `{}` body reached Plaid with no `public_token`.

**Why it matters:** A client error is reported as a server bug, and a request the app could refuse locally is sent to Plaid. The page itself always sends a well-formed body, so this matters only for direct callers.

**Suggested fix:** Parse the body the way `attemptOf` does, and answer 400 when `publicToken` is not a non-empty string.

### A cancel that reaches the app before its start does leaves a claim nobody can cancel

**Severity:** Low
**Location:** src/connect-an-account/connect-an-account.ts:107 (and src/screen/plaid-connect.ts:256)
**Category:** correctness
**Status:** confirmed by execution

**What's happening:** The page's Cancel aborts the start's `fetch` and immediately posts `/connect/cancel` for the same attempt. The aborted start may still reach the Worker, and if it arrives after the cancel, `releaseIfHeldBy` finds nothing to release and the late `begin` then takes the claim. Probe P5 runs `cancel("attempt-1")` then `begin("attempt-1")` and prints `status after cancel-then-begin: connecting`. The page has already told the owner "Connection cancelled. Nothing was saved." The next load shows the unfinished-attempt view, and only Start over clears it.

**Why it matters:** The owner sees a confusing state and a claim left behind. No data is lost.

**Suggested fix:** Have cancel record a tombstone for the attempt id, which `claim` refuses, or have `begin` refuse an attempt that has already been cancelled.

### The history write guard compares only the position, so a late step can overwrite a restarted run

**Severity:** Low
**Location:** src/ledger-store/connection-records-store.ts:99
**Category:** correctness
**Status:** confirmed by execution

**What's happening:** `writeHistory` takes effect when `position IS readPosition`. A temporary failure moves the position back to `runStart`, so a step that started from `runStart` before the run moved on matches the guard again. That is the classic ABA case. Probe P6 runs a slow step A from `null`, step B from `null` to `p1`, and step C failing at `p1`, which writes `position: null, failures: 1`. When A finishes, its write lands: `position: "late-A", failures: 0`. The run's failure count is reset by a step that read stale state.

**Why it matters:** The cap of five temporary failures can be defeated, and the position can jump to a cursor from an abandoned run. This is reachable only when two steps overlap, for example when the page times out a step (45 s) and retries while the first request is still running.

**Suggested fix:** Add a monotonically increasing version, or `last_step_at`, to the guard, and write `failures` relative to the stored value rather than the value the step read.

## Counts

Critical 0, High 1, Medium 3, Low 3
