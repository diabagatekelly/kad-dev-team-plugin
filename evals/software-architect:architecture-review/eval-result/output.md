Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-review/SKILL.md

## Finding: Types file depends on a tactical library, contaminating every strategic caller

**Location:** `domain/gateways.types.ts`
**Category:** Dependency Rule (backward-direction violation)
**Severity:** High

**What's happening:** `gateways.types.ts` imports `MongoClientOptions` from
`mongodb` and exposes it as a field (`connectionOptions`) on the
`AccountGateway` interface. Checked forward, `link-account.use-case.ts`
looks clean — it only imports `AccountGateway` from the types file,
nothing Mongo-specific. Checked backward, the types file itself depends on
a tactical library. Every strategic file that imports `AccountGateway` —
currently just the one use case, but anything else that depends on this
interface — inherits the same contamination without ever importing Mongo
directly.

**Why it matters:** The violation is invisible if you only check what each
use case imports; it lives one level removed, in the shared interface
itself. Swapping the database later means touching every file that
references `AccountGateway`'s `connectionOptions` field, not just the
adapter — the interface has stopped being a clean seam.

**Suggested fix:** `connectionOptions` shouldn't live on the domain-facing
interface at all — connection configuration is a tactical concern the
adapter needs, not something the strategic side should see. Move it to the
concrete implementation (constructed at the composition root) and keep
`AccountGateway` limited to domain-shaped types only.

## Finding: Payment methods called directly by concrete SDK, no shared interface, despite three concrete implementations existing now

**Location:** `domain/pay-invoice.use-case.ts`
**Category:** Missing abstraction (under-engineering) + Invasive Species
**Severity:** High

**What's happening:** `PayInvoiceUseCase` branches across three concrete
payment SDKs (Stripe, PayPal, Square) inline, instantiating each directly
in business logic.

**Why it matters:** This isn't a hypothetical future need — three concrete
implementations already exist today, which is exactly the threshold this
skill treats as "needed now." Business logic is directly coupled to three
high-lock-in third-party libraries at once; every new provider means
another branch here, and swapping or testing any one provider means
touching this use case's core logic.

**Suggested fix:** Extract a payment-provider-shaped interface owned by
the strategic side, with one adapter per provider (Stripe, PayPal, Square)
as the only place each SDK is imported. The use case depends on the
interface and picks an implementation via a composition root, not an
inline conditional on three concrete classes.

## Finding: Top-level structure organized by technical role, not business concept

**Location:** the `controllers/`, `services/`, `models/`, `repositories/`
directory grouping
**Category:** Screaming Architecture
**Severity:** Medium

**What's happening:** The codebase's top-level directories are named for
technical layers rather than what the business is about — someone
scanning `src/` sees "controllers, services, models, repositories" before
they see "transaction" or "account" anywhere.

**Why it matters:** Finding everything related to one business concept
(e.g. transactions) means hunting across four directories instead of one;
the structure screams "MVC," not what this system actually does.

**Suggested fix:** Reorganize by business concept — a directory per domain
concept (e.g. transaction, account) containing that concept's model, use
case(s), and repository together, rather than grouping all models
together, all repositories together, etc.

## Not a violation: the factory call in `LinkAccountUseCase`

`getAccountGateway()` returns a concrete Mongo-backed implementation typed
as `AccountGateway`, and nothing outside `infra/factory` ever imports the
concrete class directly — that's composition-root wiring, not a
Dependency Rule violation, even though a factory call can look identical
to a strategic-depends-on-tactical import at a glance. (The actual issue
nearby is the interface itself, covered above — not this call site.)
