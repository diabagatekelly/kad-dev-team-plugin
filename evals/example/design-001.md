# Design: Slice 1 — Connect one institution and see its transactions

## Importance ordering assumed

Stated explicitly rather than left to the usual defaults, because this
slice inverts one of them.

1. **The bank credential never entering the system.** Ranked above
   functional correctness. A defect that displays a wrong transaction is
   embarrassing; a defect that puts the user's bank login inside this
   system is unrecoverable — the user changes their bank password and the
   trust is still gone.
2. **Which transactions belong to which connection.** Domain correctness.
   Everything later in this problem — categorization, budgets, transfer
   amounts — is derived from this being right.
3. **Retrieval and display logic.** Wrong here is visible and fixable.
4. **The data provider's client, the HTTP layer, the UI framework, the
   in-memory store.** Swappable. Changing any of them changes nothing about
   what this system does.

Strategic vs. tactical, applied: if the data provider were swapped
tomorrow, items 1–3 should not change. That's the test the structure below
has to pass.

## Structure

**Strategic**

- **Account Connection** — a link the user has established to one
  institution. Owns the fact that a connection exists, which institution it
  is for, and that it can yield transactions. This is what transactions
  belong to; there is no user or owner concept in this slice (Decision 4).
- **Transaction** — a single retrieved transaction: date, amount,
  description, and the account it came from (Decision 3). Plain data.
- **Connecting an Institution** — the behavior of establishing a connection
  and replacing any previous one for that same institution.
- **Retrieving Transactions** — the behavior of asking a connection for its
  transactions.

**Tactical**

- **Institution Transactions adapter** — the single place that talks to the
  chosen data provider and the only thing that imports its client.
  Translates the provider's payload into `Transaction` values.
- **Connection storage, in memory** — holds the live connection and its
  retrieved transactions for the lifetime of the process (Decision 2).
- **Web interface and wiring** — the connect screen, the transaction list,
  and the composition root that constructs the adapter and hands back the
  interface type. Conventional technical naming is fine here; it holds no
  business logic.

Name check: strip the technical suffix from each and a business concept
survives — connection, transaction, institution. Nothing here is a
`Handler`, `Manager`, or `Utils` with nothing left underneath.

## Boundaries and interfaces

**Institution transactions boundary** — the important one.

- The interface is **owned by the strategic side**, named for what the
  business needs (transactions from an institution), not for what the
  provider offers. The adapter implements it. Strategic code never
  references the provider's client.
- What crosses: `Transaction` values and a connection identifier. Plain
  data only. The provider's response objects, its SDK types, HTTP
  responses, and its error types do not cross — they are translated at the
  adapter in both directions, including failures.
- The provider's error shapes become the slice's own outcomes ("the
  institution rejected the connection," "nothing was returned") at this
  edge. This is what lets the rejected-credentials criterion be written
  without naming a vendor.

**Connection storage boundary** — interface owned by the strategic side,
in-memory implementation behind it.

**Web interface boundary** — plain data crosses to the UI. The transaction
list renders `Transaction` values; it does not receive provider payloads.

None of these needed approval — they're the Dependency Rule and Good
Fences applied mechanically, with no real alternative being weighed.

## Third-party isolation

- **The data provider's client — isolated, single adapter as sole
  importer.** This is the clearest Invasive Species case in the slice: an
  external service, holding an auth relationship, with high lock-in. Two
  independent reasons, not one — the rule requires it, and the specific
  vendor is *known to be unverified*, so the axis of change is already
  visible rather than speculative.
- **The provider's embedded connect flow** — most aggregators ship their
  own hosted or embedded login widget, which is the entire point (it's what
  keeps the credential out of this system). It is third-party UI with a
  callback into the app. The callback is a trust boundary and is flagged
  below for `devsecops-engineer`, not resolved here.
- **HTTP client and web framework** — edge concerns, kept at the edge.
  Isolating them further would be ceremony.

## Technology at each boundary

| Boundary | Status |
|---|---|
| **Institution transactions** | **Forced by this slice, and now resolved: Plaid.** See Decision 5. The mechanism was settled first (Decision 1), the vendor after research closed the coverage question. The interface is what made it safe to settle those in that order. |
| **Connection storage** | **Not chosen — in-memory satisfies this slice.** Nothing needs to outlive a restart, because the connect-twice criterion replaces the whole retrieved set. Choosing a store now would mean guessing at access patterns no slice has demonstrated. |
| **Web interface / UI** | Not a boundary decision. Language, runtime, test runner, and package manager belong to `technology-bootstrap`, which hasn't run. |

## Decisions

**1. A third-party aggregator holds the bank credential.** *Approved as
recommended.* The app receives an access token and never the username or
password. Rejected: direct OFX connection to the bank (free where
supported, but the app would hold the credential — the exact asset
requirements-001 ranked highest), and automating the bank's website (free
and universally applicable, but holds full credentials, breaks on any site
change, and typically violates the bank's terms). Also rejected: deferring
behind a fake institution, which would leave the slice unable to answer the
question it was cut to answer.

Consulted `devsecops-engineer:security-requirements` inline on the secrets
question, as that is its call and not the architect's. Its guidance:
prefer a property asserting a sensitive class *never enters* over one
asserting it is handled carefully. That is what selected this option.

**Flagged ADR-worthy** at the time it was presented — architectural, costly
to reverse, and non-obvious. Deferred at the user's request, then
**written up as ADR-001**, merged with Decision 5 and with
security-requirements-001's trust-boundary risk acceptance, since the three
are one decision and its consequences.

**2. Slice 1 persists nothing.** *Approved as recommended.* Transactions
and the access token live only in memory; restarting means reconnecting.
Rejected: persisting from the start (front-loads slice 3's needs and puts
financial data and the highest-value secret at rest in the first slice),
and persisting the token only (same exposure for the part that matters
most).

**3. A transaction carries date, amount, description, and source account.**
*Approved as recommended.* Rejected: carrying the provider's full payload
(shapes the domain around whatever the vendor happens to send, for a
categorization approach nobody has specified), and adding the provider's
transaction ID (a field carried for a slice that doesn't exist, in a slice
deliberately designed to need no matching key).

**4. Transactions belong to the connection, not to a person.** *Approved as
recommended.* No user or owner concept exists in this slice, which
satisfies requirements-001's no-hardcoded-identity rule by not creating an
identity to hardcode. Slice 2 introduces a person and attaches connections
to them, with nothing to undo. Rejected: introducing an owner now
(inventing identity before anything can authenticate one), and attaching
nothing at all (the connect-twice criterion needs to know which set it's
replacing).

**5. Plaid sits behind the institution-transactions boundary.** *Approved as
recommended, after research.* Selected on coverage — the one criterion that
cannot be worked around. Plaid documents integrations for American Express
(Transactions, Balance, Assets) and Chime (one of two US institutions
supporting app-to-app authentication), plus every major bank named. Its
Trial plan gives ten production connections free with real data, which is
above personal scale.

Rejected: **Teller**, which was the better fit for slice 1 in isolation — a
JavaScript widget with no redirect URI at all, so the local-only condition
would have held with no ceremony. It lost on two concrete points: Chime and
Amex coverage is unconfirmed, and its authoritative institution list is
itself an mTLS-authenticated endpoint, so confirming coverage requires
provisioning a client certificate *before* knowing whether the provider
covers the accounts in question. Also rejected: **SimpleFIN**, on cost —
$15/year fails the zero-cost constraint, which the user reaffirmed rather
than reopened, despite it being the only candidate where read-only access
is structural rather than app-side discipline.

Cost accepted with Plaid: OAuth institutions in Production require an HTTPS
redirect URI. `https://localhost` is permitted, so **the local-only
condition survives** — but it needs a self-signed certificate, which Teller
would not have.

**6. Readiness is detected by an Item status check, not by inferring from
an empty result.** *Approved as recommended.* The institution-transactions
boundary exposes a distinct readiness question — "has the provider finished
preparing this connection's history?" — separate from "give me the
transactions." Verified against Plaid's documentation: `/transactions/sync`
returns empty arrays rather than an error when data isn't ready, while
`/item/get` exposes `item.status.transactions.last_successful_update`, which
Plaid names as the signal to use instead of guessing from empty arrays.

Rejected: `/transactions/get` with `PRODUCT_NOT_READY` as the signal (one
call instead of two and unambiguous, but it couples readiness detection to
the older retrieval endpoint, which slice 3 will want to leave for
incremental sync). Rejected: inferring readiness from an empty array, which
is the exact ambiguity the slice-001 scope change exists to remove.

**This decision is what makes the slice-001 narrowing implementable.** No
webhook, therefore no publicly reachable endpoint, therefore the local-only
condition holds.

## YAGNI, both directions

- **Rejected as premature:** persistence, an owner concept, the provider's
  transaction ID, and carrying the full provider payload. All four were
  available and all four were declined.
- **Required now, not deferred:** the institution-transactions interface.
  It is not speculative reuse — the Dependency Rule requires strategic code
  to depend on something other than the concrete provider, and removing it
  would break dependency direction rather than simplify anything. The
  provider being unverified makes this an already-visible axis of change,
  not a hypothetical one.

## Existing violations touched

None. No code exists yet.

## Open questions

- ~~**Which provider, and does any free option cover the user's
  institution?**~~ **Resolved — see Decision 5.** A free option covering the
  named institutions exists, so requirements-001 does not need superseding.
- ~~**Does the provider's connect flow require a publicly reachable
  callback?**~~ **Resolved, favorably.** Plaid permits `https://localhost`
  as a redirect URI in Production. The local-only condition holds and
  slice 1's no-authentication narrowing stands. Cost: a self-signed
  certificate for local HTTPS.
- **Plaid is migrating Bank of America connections throughout 2026**, with
  a `PENDING_DISCONNECT` webhook and roughly a one-week window before an
  Item disconnects. Webhooks require a publicly reachable endpoint. This
  does not touch slice 1, which connects on demand and holds nothing across
  restarts — but it means the hosting-and-authentication work in slice 2 has
  a real deadline behind it rather than being indefinitely deferrable, and
  it is directly relevant to slice 4 (recovering an expired connection).
- **Read-only is app-side discipline, not a provider guarantee.** Plaid
  enforces scope by which products are requested at link-token creation;
  Transfer is a separate product. security-requirements-001's read-only
  criterion is satisfiable, but by this application requesting only
  transactions — not by Plaid preventing anything. Recorded because the
  criterion as written could be misread as a property the provider
  enforces.
- **Security acceptance criteria** — `devsecops-engineer`. This design
  changed what they have to cover: the credential is now out of scope
  entirely, and the access token plus the provider callback are in.
- **Accessibility acceptance criteria** — unowned in this roster.
- **The starting stack** — `technology-bootstrap`, which has not run.
