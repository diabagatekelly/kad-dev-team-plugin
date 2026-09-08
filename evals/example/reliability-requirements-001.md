# Reliability requirements: Slice 1 — Connect one institution and see its transactions

Counterpart to security-requirements-001, same slice, same moment.
Everything here is scaled to what this actually is: a single-user tool on
the user's own machine, with no deadline behind it.

## What's at stake

Stated by the user, not assumed.

- **An hour of unavailability costs nothing.** They try again later. This is
  the answer that keeps the rest of this document short — enterprise
  availability criteria here would produce criteria nobody implements.
- **Detection is the user, next time they open it** — but they want the app
  to say clearly what went wrong, rather than showing an empty list they'd
  misread as "no transactions this month." Detection is manual by design; the
  *clarity* is the requirement.
- **Latency bound: about two minutes.** The user is willing to wait. The
  requirement that matters isn't speed — it's that a bound exists at all,
  because an unbounded hang is the failure mode that looks like nothing
  happening.

**No availability target is being committed to.** There is no second party
to be accountable to, no deadline, and no cost to downtime. Inventing a
number here would be ceremony.

## Failure modes

This slice depends on exactly one external thing: the data provider.

| Mode | Intended behavior | Why |
|---|---|---|
| **Provider is slow** | Give up at the latency bound and say retrieval timed out. | The most commonly missed mode. Without a bound it never fails, it just never finishes — and the user sits looking at a screen that appears to be working. |
| **Provider is down or returns an error** | **Fail loudly.** State that retrieval failed and that the provider was unreachable, distinct from other failures. | Costs nothing to surface; hiding it teaches the user to distrust the app instead of the provider. |
| **Provider returns partial data** | **Fail loudly.** Show no transactions and say the retrieval was incomplete. (Decision 1) | A partial list is visually indistinguishable from a complete one, and this app exists so the user can trust the numbers. |
| **Provider rejects the credentials** | **Expected failure, not a fault.** Say the institution rejected the connection and let the user try again. | Already a functional criterion in slice-001. It's normal operation, not a bug, and must not be reported as one. |
| **Connect flow interrupted partway** | Leave nothing behind; the user starts over cleanly. | Already covered by a security criterion — no partial token state survives. Same behavior, two reasons. |
| **The same retrieval happens twice** | Harmless. The newest result replaces the previous set. | Slice-001's connect-twice criterion already decided this, which is why no duplicate-detection rule is needed here. |

**Not a failure mode for this slice:** provider rate limiting. Plausible on
a free tier, but with one user, no automatic retries (Decision 2), and
manual invocation, there is nothing generating the request volume that
would trigger it. It becomes real at slice 3, when refresh runs on its own.

## What must be observable

Driven by one question, not by coverage: **is this slice working, and if
not, where did it fail?**

For a single-user local tool, "observable" means the user can tell these
apart without opening a debugger:

- The provider rejected the credentials (their problem to fix).
- The provider was unreachable or timed out (nobody's fault, retry later).
- Retrieval succeeded but was incomplete (retry, don't trust what you saw).
- The institution genuinely has no transactions in the period (nothing
  wrong at all).
- Something in the app itself broke (a bug, and it must not be disguised as
  one of the four above).

That list *is* the observability requirement. No metrics, no telemetry, no
alerting — none of it is justified by a tool with one user, manual
invocation, and no cost to downtime. Note also that adding telemetry would
create a new exit route for the financial data that security-requirements-001
currently keeps inside the process.

## Acceptance criteria

Alongside slice-001's functional criteria and security-requirements-001's.

**A slow provider eventually fails rather than hanging**
> **Given** the provider accepts the request but does not respond,
> **When** roughly two minutes have passed,
> **Then** the attempt ends and the app states that retrieval timed out,
> rather than continuing to appear busy.

**An unreachable provider is reported as such**
> **Given** the provider is unreachable or returns an error,
> **When** the user attempts to connect or retrieve,
> **Then** the app states that the provider could not be reached, in terms
> distinguishable from the institution rejecting the credentials.

**Partial retrieval shows nothing**
> **Given** retrieval completes but the app cannot confirm it received the
> complete set,
> **When** the result is presented,
> **Then** no transactions are displayed and the app states the retrieval
> was incomplete.

**No automatic retry**
> **Given** any retrieval failure,
> **When** it occurs,
> **Then** the app does not reattempt on its own, and the user can retry
> deliberately.

**An empty result is not an error — and "not ready" is not "empty"**
> **Given** the provider has finished preparing and the institution
> genuinely returned no transactions for the period,
> **When** the result is presented,
> **Then** the app states that none were found, distinguishable from every
> failure message above *and* from the still-preparing state.

> **Given** the provider has not finished preparing the history,
> **When** the result is presented,
> **Then** the app states that transactions are still being prepared, and
> does not report an empty account.

Amended after the finding below was resolved. The original single criterion
asserted that an empty result meant an empty account — which is false
against the chosen provider, and would have produced exactly the silent-
wrongness this document exists to prevent.

**Bugs are not disguised as expected failures**
> **Given** an unexpected fault occurs inside the app,
> **When** it surfaces to the user,
> **Then** it is presented as an unexpected problem rather than as a
> provider or credential failure, and enough detail is recorded for the
> user to diagnose it later — subject to the secrets-in-logs criterion.

## Decisions

**1. Partial retrieval fails loudly rather than degrading.** *Approved as
recommended.* Show nothing; state the retrieval was incomplete. Rejected:
showing what arrived with an incomplete marker (a marker on a raw list is
weak protection, and the habit carries into later slices that compute
budget figures from this data, where it does real damage), and showing what
arrived unmarked (the exact failure of degrading so gracefully nobody
learns anything is wrong).

**2. No automatic retry.** *Approved as recommended.* The user retries
deliberately. Rejected: a bounded automatic retry (delays surfacing a
failure the user explicitly wants stated clearly, and spends a free-tier
quota nobody has measured), and silent retry until success (contradicts
wanting to be told).

Neither decision clears the ADR bar. Both are slice-local behavior choices
that a later slice can reverse cheaply — unlike the trust-boundary decision
in security-requirements-001, which is still owed to `docs-writer` along
with design Decision 1.

## Out of scope for this slice

- **Rate limiting and quota exhaustion** — real at slice 3, when refresh
  runs unattended and generates volume no one is watching.
- **Connection expiry and re-authorization** — slice 4.
- **Staleness of previously retrieved data** — meaningless here, since
  nothing persists (design Decision 2). Becomes a real question the moment
  slice 3 stores anything.
- **Monitoring, alerting, and telemetry** — not justified at this scale,
  and deliberately avoided rather than merely skipped, since each would add
  an exit route for financial data.

## Open questions

- ~~**What "the complete set" means**~~ **Resolved, criterion is
  implementable.** Plaid's `/transactions/sync` returns a `has_more` flag;
  when it is false, the caller has everything available. Completeness is
  determinable, so the fail-loudly-on-partial criterion stands as written.
- ~~**The two-minute bound is the user's stated tolerance**~~ **Resolved,
  and it turns out to be the wrong instrument for the real wait.** Request
  latency is not what makes a first connection slow — see the finding below,
  which is a different axis entirely.

  The bound is still worth having, and two verified details support keeping
  it generous rather than tightening it. Plaid documents that the first
  retrieval call after historical data becomes available can run **up to
  eight times** the latency of a normal one, and explicitly warns that
  hard-coded timeouts may need adjusting. Two minutes accommodates that; ten
  seconds would have produced false failures. Separately, the amount of
  history requested at connection time drives how long the still-preparing
  state lasts — requesting less shortens the wait, which is an
  `software-architect` parameter rather than a criterion here.

## Finding — routed to `product-slicer`, not resolved here

**Plaid does not have transactions ready at the moment a connection
succeeds.** Historical transaction data is prepared asynchronously after an
Item is linked. Until that finishes, `/transactions/sync` returns an
**empty transactions array** — and Plaid signals readiness through the
`INITIAL_UPDATE` and `HISTORICAL_UPDATE` webhooks, explicitly advising
callers to listen for webhooks rather than poll.

This collides with slice 1 in two places at once:

1. **Slice-001's primary criterion** says completing the connect flow means
   transactions appear in a list. On a fresh connection, they may not be
   there yet.
2. **Slice-001's "nothing to retrieve" criterion and this document's
   "an empty result is not an error" criterion** both assume an empty
   result means the institution genuinely had no transactions. With Plaid,
   an empty array on a fresh connection much more likely means *not ready
   yet*. As written, the app would confidently tell the user "no
   transactions found" when the true answer is "not yet."

That second point is the serious one: it is precisely the
degrade-so-gracefully-nobody-learns-anything-is-wrong failure this document
exists to prevent, arriving through a criterion written to prevent it.

**Why this can't be quietly patched at implementation time:** the
provider's own recommended mechanism is webhooks, which require a publicly
reachable endpoint. Slice 1 has none by design, and that absence is the
condition its no-authentication scope rests on.

**This is a scope decision and it belongs to `product-slicer`.** Whether
slice 1 changes shape, narrows, or absorbs a new behavior is not this
persona's call, not `software-architect`'s, and not something to resolve by
handing the user a menu. Reported and routed.

**Resolved by `product-slicer`: the slice was narrowed, not grown.** Slice 1
no longer promises transactions appear; it promises the user is never told
"none found" when the truth is "not ready." Growing the slice to receive
webhooks was considered and rejected, because a publicly reachable endpoint
would void the local-only condition this slice's entire no-authentication
scope rests on. See the scope-change section in slice-001.
