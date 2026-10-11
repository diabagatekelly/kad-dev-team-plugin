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
