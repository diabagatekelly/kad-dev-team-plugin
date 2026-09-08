---
name: software-architect:technology-bootstrap
tags: [software-architect, technology-bootstrap]
runs: 3
---

The repository is empty. No language, no test runner, no package manager,
no directories — nothing has been created yet.

Slice 1 has been cut, designed, and has its runtime-safety criteria filled.
Everything below already exists as agreed artifacts.

# Slice 1 (scope-map-001 step 1): Connect one checking account and see its transactions

## Thin path
You choose one of your checking accounts, connect it through a
bank-aggregation vendor, and see that account's recent transactions listed
in the app.

## Acceptance criteria (abridged)
- Given I choose an account and the connection succeeds, that account shows
  as connected and I can tell which one it is.
- Given a connected account, when I open the transaction list, I see its
  transactions with date, description and amount.
- Given the connection fails, no account shows as connected and I am told.

Transactions are shown for the current session only. Nothing in this slice
requires them to still be there after a restart — re-pulling on next use is
acceptable and expected.

# Design: Slice 1

## Structure
**Strategic:** Account, Transaction, ConnectionOutcome.
**Tactical:** a bank-connection adapter (the sole importer of the vendor
SDK), an account/transaction store implementing a strategic-owned
persistence interface, and a transaction list view.

## Boundaries
- **Bank connection boundary** — strategic side owns the interface; the
  adapter is the only thing importing the vendor SDK.
- **Persistence boundary** — strategic side owns the interface for storing
  and retrieving Account/Transaction records; the store adapter implements
  it. Storage technology is deliberately not chosen in this design.

# Security criteria for slice 1 (abridged)
- No bank username or password is ever received or stored — the vendor's
  flow means they never enter the system.
- The vendor access token never appears in logs, error responses, or any
  stack trace, and is not written to any persistent store in this slice.

---

Work out what has to be set up before the first failing test for this slice
can be written.

## Scripted answers

- If asked who is building and maintaining this: "Just me. Solo side
  project, and I'd rather not maintain a lot of tooling."
- If asked about language or runtime preference: "I'm most fluent in
  TypeScript and I'd like to stay there — the UI is going to be a web app
  anyway."
- If asked about a test runner, or presented with a recommendation for one:
  "Whatever you'd recommend as the standard choice for that ecosystem —
  I don't have a preference, go with it."
- If asked about a package manager, or about pinning/lockfile posture:
  "I want whatever means I don't have to remember a flag to stay safe.
  Pick the one where that's the default."
- If asked about anything else at all — hosting, CI, a database, a
  deployment target, an auth provider: "I haven't thought about that yet
  and don't want to decide it now."
