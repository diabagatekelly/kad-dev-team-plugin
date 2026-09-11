Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-review/SKILL.md

## Finding: `AccountGateway` interface is itself contaminated with a tactical type

**Location:** `domain/gateways.types.ts`
**Category:** Dependency Rule (backward check)
**Severity:** High

**What's happening:** `AccountGateway` imports `MongoClientOptions` from `mongodb` and exposes it as a field (`connectionOptions`) on the interface itself. The forward check on `link-account.use-case.ts` looks clean — it only imports `AccountGateway`, never `mongodb` directly — but the backward check on what the interface *itself* depends on catches what the forward check misses: the types file is the actual violation site, not any of its callers.

**Why it matters:** Every strategic file that imports `AccountGateway` inherits a dependency on Mongo's shape without ever importing Mongo, because the contamination rides along inside the interface. Swapping the persistence technology means touching every consumer of this interface, not just the adapter — the exact coupling the boundary was supposed to prevent. Fixing it at each caller instead of at the source would mean fixing it repeatedly.

**Suggested fix:** Remove `connectionOptions` from `AccountGateway` entirely. Connection configuration is an adapter concern — it belongs inside whatever constructs the concrete Mongo-backed implementation in `infra/factory`, not on the strategic-owned interface.

## Finding: no shared abstraction for payment providers, three SDKs imported directly in business logic

**Location:** `domain/pay-invoice.use-case.ts`
**Category:** Missing abstraction (under-engineering) + Invasive Species
**Severity:** High

**What's happening:** `PayInvoiceUseCase` branches inline across three concrete payment SDKs (Stripe, PayPal, Square), each imported and instantiated directly inside business logic based on a string flag.

**Why it matters:** This isn't a hypothetical future need — three concrete implementations already exist today, which is exactly the missing-abstraction case, not premature abstraction. Each SDK is also a high-lock-in third-party dependency (Invasive Species) used directly rather than isolated behind an adapter, so a change to any one vendor's API, or adding a fourth provider, means editing business logic rather than adding one adapter. The `if/else` on a string is also standing in for a decision the type system could be making instead.

**Suggested fix:** Introduce a payment-provider-shaped interface (e.g. something like `PaymentGateway` with a `charge` operation) owned by the strategic side, with one adapter per provider (Stripe, PayPal, Square) as the sole importer of each SDK. `PayInvoiceUseCase` depends only on the interface and a provider selection, the same shape `AccountGateway`/`infra/factory` already uses correctly elsewhere in this codebase.

## Finding: top-level directories are named by technical role, not business concept

**Location:** `src/controllers/`, `src/services/`, `src/models/`, `src/repositories/`
**Category:** Screaming Architecture
**Severity:** Low

**What's happening:** The top-level grouping is entirely technical role — controller, service, model, repository — with no grouping by what the system actually does (accounts, transactions, invoices/payments).

**Why it matters:** Opening the directory tree tells a reader what layers exist, not what the system is for. As it grows, related business logic for one concept (e.g. everything about an account) ends up scattered across four parallel technical directories instead of living together, making a single business change touch four unrelated places to find all of it.

**Suggested fix:** Reorganize by business concept first (e.g. `accounts/`, `transactions/`, `invoices/`), with technical role as a secondary grouping inside each, if needed at all.

## Checked and correct — not a finding

`LinkAccountUseCase` obtains its gateway via `getAccountGateway()` in `../infra/factory`. This looks like it could be a strategic-depends-on-tactical violation at a glance, but it isn't: the use case never imports or references the concrete Mongo-backed class, only the `AccountGateway` interface type, and `getAccountGateway()` returns that concrete implementation typed as the interface. That's composition-root wiring — the one place allowed to know both the interface and the concrete construction — not a Dependency Rule violation.
</content>
