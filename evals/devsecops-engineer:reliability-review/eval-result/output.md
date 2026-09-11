Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/reliability-review/SKILL.md

## Finding: Provider call has no timeout

**Location:** `infra/bankClient.ts` — `fetchTransactions`, the `fetch(...)` call
**Category:** Missing timeout
**Severity:** High

**When this bites:** The provider accepts the connection but stops responding — doesn't error, doesn't close the connection, just never replies.

**What's happening:** The `fetch` call has no timeout, `AbortController`, or deadline of any kind. A slow provider doesn't fail this call — it just never returns.

**Why it matters:** This is the failure mode nothing here is built to notice. The retry loop above assumes `fetchTransactions` eventually resolves one way or the other; if the provider just hangs, this call — and the account's whole sync attempt — hangs with it, holding whatever resources it holds for however long that takes.

**Suggested fix:** Add a timeout to the fetch (an `AbortController` with a deadline appropriate to how long a legitimate call should take), and let the resulting abort be treated as a failure like any other.

## Finding: Retry logic retries a failure that retrying can't fix

**Location:** `domain/syncTransactions.ts` — the retry loop in `syncTransactionsForAccount`
**Category:** Resilience pattern mismatch (retry applied to a non-transient failure)
**Severity:** High

**When this bites:** Whenever a user has revoked the connection's authorization — the prompt states this returns 401 from the provider and can't be fixed by retrying.

**What's happening:** The loop catches every error `fetchTransactions` can throw, with no distinction by type, and retries all of them identically up to 5 times with a fixed 2-second sleep between attempts.

**Why it matters:** Retrying a 401 is not resilience, it's amplification: five doomed calls and roughly 8 seconds of delay per affected account, every single night, for a failure that will never resolve on its own. At any real number of revoked connections, this also means the job spends real time hammering the provider with authentication failures it already knows are permanent.

**Suggested fix:** Distinguish transient failures (network errors, 5xx, timeouts) from permanent ones (401, and likely other 4xx) before deciding to retry. A permanent failure should fail immediately, not consume the retry budget.

## Finding: Retry/backoff logic lives in the domain function, not the adapter

**Location:** `domain/syncTransactions.ts` — the retry loop is inside `syncTransactionsForAccount`, which calls `bankClient.fetchTransactions`
**Category:** Resilience logic in the wrong layer
**Severity:** Medium

**What's happening:** `syncTransactionsForAccount` is a use case — it decides what to do with a synced result — but it also owns the retry count, the backoff delay, and the decision to keep calling the provider again. `bankClient`, the adapter that actually talks to the provider, has none of this.

**Why it matters:** The use case shouldn't need to know that its dependency retries, any more than it should know what URL the provider uses. This is the same boundary `software-architect` draws between business logic and infrastructure — resilience mechanics belong with the thing whose job is talking to the flaky dependency, not the thing deciding what a successful sync means.

**Suggested fix:** Move the retry loop (with the fix for the finding above) into `bankClient.fetchTransactions` itself, so the adapter either returns transactions or throws a single, already-final error. `syncTransactionsForAccount` should have nothing between the call and its result.

## Finding: A failed sync is indistinguishable from a successful one

**Location:** `domain/syncTransactions.ts` — `if (!transactions) { return; }` in `syncTransactionsForAccount`
**Category:** Swallowed failure treated as normal completion
**Severity:** Critical

**When this bites:** Every time an account exhausts its retries — whether from the timeout gap above, the retry-on-401 gap above, or a genuinely transient outage lasting longer than the retry budget.

**What's happening:** After retries are exhausted, the function logs at `debug` level (a level nobody is described as reading) and returns exactly as it would if the sync had simply nothing new to save. `syncAllAccounts` moves on to the next account with no idea anything went wrong.

**Why it matters:** This has converted a failure into wrong behavior. The system now proceeds as though every account synced, when some silently didn't — which is strictly worse than an unhandled exception, because an unhandled exception would at least be visible. Fixing only the log level wouldn't fix this: the real problem is that `syncAllAccounts` and whoever looks at the results afterward have no signal at all that this account's data is now stale.

**Suggested fix:** `syncTransactionsForAccount` needs to communicate failure to its caller — return a result that distinguishes "saved new transactions," "nothing new," and "failed to sync," and have `syncAllAccounts` collect and surface the failures rather than silently continuing past them.

## Finding: No way to tell apart why an account didn't get fresh data

**Location:** `domain/syncTransactions.ts` — `syncTransactionsForAccount` and `syncAllAccounts` together
**Category:** Undiagnosable failure mode
**Severity:** High

**What's happening:** Once this job finishes a run, there's no way to determine, for any given account, which of these actually happened: (a) new transactions were saved, (b) the provider had nothing new, (c) the connection's authorization was revoked (permanent), or (d) a transient failure exhausted the retry budget. All four currently look identical from the outside — a `debug`-level line that nobody is positioned to read, then silence.

**Why it matters:** This is a diagnosability gap, not a missing-metric gap: nothing here would let a person answer "is this job actually working, and if not, for which accounts and why" without reading the debug logs line by line after the fact.

**Suggested fix:** Once the finding above gives `syncTransactionsForAccount` a way to report its outcome, have `syncAllAccounts` track and expose per-account results in those four categories, so a single query can answer which accounts are stale and why.

If nothing rises above what's listed here, there's nothing else to report — the job has exactly one dependency, and every finding above traces back to how failure from that one dependency is handled.
</content>
