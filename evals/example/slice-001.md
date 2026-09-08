# Slice 1 (scope-map-001 step 1): Connect one institution and see its transactions

## Slice set for this unit

Provisional — building slice 1 is expected to change what's below it.

1. **Connect one named institution and see its transactions** ← this slice
2. Put authentication in front of the app and make it reachable off the
   local machine
3. Refresh transactions repeatedly without re-connecting
4. Recover a connection that breaks or expires
5. Connect a second institution

## Thin path

Running on the user's own machine, the user completes an in-app connect
flow for one institution they name, and then sees **either that
institution's transactions or an honest statement of why they aren't there
yet**. Nothing is categorized, no budget exists, and the app is not
reachable from anywhere else.

**Revised after a devsecops finding — see "Scope change" below.** The thin
path deliberately no longer promises that transactions appear. It promises
that the user is never lied to about why they haven't.

**The local-only condition is what makes this slice legal, not an
afterthought.** requirements-001 found that the hosted-anywhere constraint
forces access control into step 1. That finding was resolved by narrowing
this slice so the constraint doesn't apply yet — the app isn't exposed, so
"who is allowed to see this" has no one to exclude. The user then made that
narrowing explicit rather than open-ended by fixing authentication as slice
2, immediately after this one. If this slice ever becomes network-reachable,
the narrowing is void and the access-control work comes back into it.

## Acceptance criteria

**Primary path**
> **Given** the app is running with no institution connected,
> **When** the user completes the connect flow for the institution they
> named,
> **Then** transactions retrieved from that institution appear in a list,
> each showing its date, amount, and description.

**Rejected credentials**
> **Given** the user is in the connect flow,
> **When** the institution rejects what they submitted,
> **Then** the app states that the connection was not established and lets
> the user attempt it again, and no transaction list is shown.

**Not ready yet**
> **Given** a connection succeeded but the provider has not finished
> preparing the institution's transaction history,
> **When** the user views the list,
> **Then** the app states that the transactions are still being prepared
> and can be checked again shortly — and does not state that none were
> found.

**Genuinely nothing to retrieve**
> **Given** the provider has finished preparing and the institution
> genuinely had no transactions for the period,
> **When** the user views the list,
> **Then** the app states that no transactions were found, in terms
> distinguishable from the still-preparing state above.

These two were one criterion before. Splitting them is the whole substance
of the scope change: the original asserted that an empty result meant an
empty account, which is false against the chosen provider.

**Connecting the same institution twice**
> **Given** an institution is already connected and its transactions are
> listed,
> **When** the user completes the connect flow for that same institution
> again,
> **Then** the listed transactions are the full set returned by the newest
> retrieval, not that set added to the previous one.

*Named decision behind that last one:* this slice replaces the whole
retrieved set rather than merging into it. Merging would require deciding
what makes two transactions "the same" — a matching key nobody has chosen —
and full replacement makes duplicates structurally impossible without
choosing one. That key is genuinely needed by slice 3, where incremental
refresh makes merging unavoidable. It's deferred there deliberately, not
overlooked.

**Security — FILLED.** See security-requirements-001, which replaced this
placeholder with eleven criteria, including the testable statement of the
local-only boundary this slice's narrowing depends on.

**Accessibility — PLACEHOLDER, not authored here**
> Owned by `accessibility-engineer`, which does not exist in this roster
> yet. This slice ships a connect flow and a transaction list — both real
> UI a person operates. The placeholder stays visible until that persona
> can write it rather than being dropped because no one owns it today.

## Explicitly deferred

- **Internet exposure and authentication** → slice 2, by the user's
  explicit ordering: confirm a bank connection is possible at all, then put
  auth in front of it. Safe to defer only while this slice stays local.
- **Repeat or scheduled refresh, and the transaction matching key it
  needs** → slice 3. This slice connects and retrieves once on demand.
- **Recovering a broken or expired connection** → slice 4. Essential errors
  (rejected credentials, nothing returned) ship here; expiry is a
  later tier.
- **Any categorization of what's retrieved** → scope-map step 3. These
  transactions arrive uncategorized, which is why the list shows raw date,
  amount, and description.
- **Every other institution** → slice 5 and beyond, and per
  requirements-001 possibly never for institutions with no free route.

## Scope change — the not-ready finding

**Finding, from `devsecops-engineer:reliability-requirements`:** Plaid
prepares transaction history asynchronously after a connection succeeds,
and returns an empty result until it's done. The original criteria treated
an empty result as proof the account had no transactions. That is false
against this provider, and the app would have confidently told the user
"no transactions found" when the truth was "not yet."

**Resolution — option 2, narrowing.** Worked in the ranked order:

1. **A new slice ahead — unavailable.** The missing capability is "know
   whether the data is ready," which has no independent user value. Nothing
   to demo.
2. **Narrow the current slice — chosen.** Slice 1 no longer promises that
   transactions appear. It promises the user is never lied to about why
   they haven't. Three distinguishable outcomes replace two. This is
   genuinely thinner: it removes an assertion the slice cannot guarantee,
   rather than adding behavior.
3. **Grow to receive webhooks — rejected.** Plaid's recommended readiness
   mechanism is webhooks, which need a publicly reachable endpoint. That
   would drag slice 2's hosting and authentication into slice 1 and void
   the narrowing that let this slice ship with no access control at all.

**What this did and didn't invalidate.** requirements-001 does **not** need
superseding — its confirmed scope is that retrieved transactions become
visible to the user, and that still holds; only the slice's claim about
*when* changed. The scope map is untouched, no step boundary moved. Repaired
downstream: this slice's criteria, user-story-001, and
reliability-requirements-001's empty-result criterion.

## Still open

- ~~**Whether readiness is detectable without a webhook**~~ **Confirmed by
  `software-architect`; the resolution holds.** Plaid exposes
  `item.status.transactions.last_successful_update`, documented as the
  signal to use instead of guessing from empty arrays. No webhook, so no
  publicly reachable endpoint, so the local-only condition stands. See
  Decision 6 in design-001.
- **Accessibility criteria** — still an unfilled placeholder, still unowned
  by any persona in this roster. Unchanged by this scope change.
