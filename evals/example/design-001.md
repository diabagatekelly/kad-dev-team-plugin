# Design: Slice 1 (scope-map-001 step 1) — Connect one account via live bank sync and view its recent transactions

## Importance ordering assumed
Strategic (business logic, kept independent, highest importance): the
Account and Transaction domain concepts, the no-duplicate-transactions
rule, the connection-outcome concept (succeeded / failed-with-reason), and
the 30-day recent-history policy — a defect in any of these produces wrong
or duplicated financial data shown to the user, the exact harm this system
exists to prevent. Tactical (infrastructure, swappable, lower importance):
the Plaid adapter and whatever persists Account/Transaction records —
swapping either wouldn't change what the business does.

## Structure
**Strategic**
- Account — a connected financial account. Modeled as one of possibly many,
  even though this slice only ever creates one.
- Transaction — a single transaction belonging to an Account, carrying the
  vendor's own transaction identifier as its matching key.
- TransactionSync — the policy that requests an Account's transactions from
  the last 30 days and drops any transaction whose vendor ID has already
  been seen for that Account.
- ConnectionOutcome — whether a bank connection attempt succeeded (yielding
  a connected Account) or failed (carrying a reason), independent of
  whatever error shape Plaid itself uses.

**Tactical**
- Plaid account connector — the sole importer of the Plaid SDK; implements
  the strategic side's connection interface, translating Plaid's
  transaction and error shapes into plain Transaction data and
  ConnectionOutcome values.
- Account/transaction store — persists Account and Transaction records
  between syncs so the dedup policy has something to compare against;
  implements a strategic-owned persistence interface. Storage technology
  itself is an open question (see below).
- Transaction list view — renders whatever the strategic side hands it;
  framework-specific, no business logic.

## Boundaries and interfaces
- **Bank connection boundary** — strategic side owns the interface for
  requesting a connection and an account's recent transactions; the Plaid
  adapter is the only thing that implements it and the only thing that
  imports the Plaid SDK. Plaid's own transaction and error shapes never
  reach strategic code or the UI directly — they're translated to plain
  Transaction data and a ConnectionOutcome at the boundary.
- **Persistence boundary** — strategic side owns the interface for storing
  and retrieving Account/Transaction records; the store adapter implements
  it. Only plain Account/Transaction data crosses in either direction.
- **Dedup rule** — enforced strategic-side, inside TransactionSync, by
  comparing incoming transactions' vendor IDs against ones already
  persisted for that Account.
- **Connection failure** — crosses the bank-connection boundary as an
  explicit ConnectionOutcome, never as a raw Plaid error.

## Third-party isolation
- **Plaid** — high lock-in (vendor SDK, auth flow, vendor-specific data
  shapes), isolated behind the bank connection adapter above; it's the only
  place that imports Plaid.
- **Whatever persistence technology gets chosen** — also tiered as Invasive
  Species once picked, isolated behind the store adapter above. Not decided
  in this design (see Open questions).

## Decisions
1. **Bank-aggregation vendor: Plaid**, over SimpleFIN. Approved by user.
   Architectural, costly to reverse, non-obvious — clears the ADR bar;
   handed off to `docs-writer` for an ADR immediately after this design.
2. **Duplicate-transaction rule enforced strategic-side** (domain compares
   vendor transaction IDs against previously-persisted ones), over trusting
   Plaid's own behavior. Approved by user.
3. **Connection failure crosses as an explicit domain ConnectionOutcome**,
   over bubbling Plaid's raw error to the UI. Approved by user.
4. **Account modeled as one-of-possibly-many**, not inherently singular,
   even though this slice only ever creates one — avoids a remodel when
   multi-account support lands later. Approved by user.

## Existing violations touched
None — this is the first slice in the codebase; there's no existing code to
check against these rules yet.

## Open questions
- Which storage technology/hosting model persists Account and Transaction
  data — depends on a deployment/hosting decision nothing has made yet
  (problem.md's "what does very secure mean concretely" is still open too,
  and the two are related). Whoever sets up the composition root resolves
  this next.
- Concrete security requirements for handling Plaid credentials/tokens and
  stored transaction data — for `security-engineer` once that persona
  exists, per slice-001's own "Still open."
- Concrete accessibility requirements for the connection flow and
  transaction list UI — for `accessibility-engineer` once that persona
  exists, per slice-001's own "Still open."
- The names above (Account, Transaction, TransactionSync, ConnectionOutcome)
  are illustrative, not final — `tdd-coach` can adjust as implementation
  reveals better names, as long as the structure and boundaries hold.
