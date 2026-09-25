Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/.claude/worktrees/agent-a82f481ca094c6e7c/skills/map-update/SKILL.md

This dry run does not write the map file. The regenerated map and diff are produced below as the deliverable, per the eval's instruction to skip the actual file write.

---

# Architecture map — updated 2026-09-24

## Modules
| Path | Tier | Internal edges (imports) | External packages | Public exports |
|---|---|---|---|---|
| domain/assign-refund.use-case.ts | tier 1 | infra/mongo-refund-store.ts | none | AssignRefundUseCase |
| domain/credit-ledger.ts | tier 1 | domain/order-directory.ts | none | CreditLedger |
| domain/order-directory.ts | tier 1 | none | none | OrderDirectory, findOrderById |
| domain/refund-ledger.ts | tier 1 | domain/order-directory.ts | none | RefundLedger |
| infra/mongo-order-directory.ts | tier 3 | domain/order-directory.ts | mongodb | MongoOrderDirectory |
| infra/mongo-refund-store.ts | tier 3 | none | mongodb | MongoRefundStore |
| util/currency-format.ts | untiered | none | none | formatCurrency |

Tier provenance: `domain/order-directory.ts` (tier 1) and `infra/mongo-order-directory.ts` (tier 3) carried forward unchanged from the prior map. `domain/refund-ledger.ts`, `domain/credit-ledger.ts`, `domain/assign-refund.use-case.ts` (tier 1) and `infra/mongo-refund-store.ts` (tier 3) are newly tiered from this slice's design doc's stated importance ordering. `util/currency-format.ts` is not named in the prior map or this slice's design doc — recorded as **untiered**, not inferred.

## Changes since the prior map

**New modules:** `domain/assign-refund.use-case.ts`, `domain/credit-ledger.ts`, `domain/refund-ledger.ts`, `infra/mongo-refund-store.ts`, `util/currency-format.ts`.

**Removed modules:** none.

**New internal edges:**
- `domain/assign-refund.use-case.ts` → `infra/mongo-refund-store.ts`
- `domain/credit-ledger.ts` → `domain/order-directory.ts`
- `domain/refund-ledger.ts` → `domain/order-directory.ts`

**Removed internal edges:** none. (The prior edge `infra/mongo-order-directory.ts` → `domain/order-directory.ts` is unchanged.)

**New external-package references:**
- `infra/mongo-refund-store.ts` → `mongodb`

**Removed external-package references:** none.

**New exports, per module:**
- `domain/assign-refund.use-case.ts`: `AssignRefundUseCase`
- `domain/credit-ledger.ts`: `CreditLedger`
- `domain/refund-ledger.ts`: `RefundLedger`
- `infra/mongo-refund-store.ts`: `MongoRefundStore`
- `util/currency-format.ts`: `formatCurrency`

**Removed exports:** none. `domain/order-directory.ts` (`OrderDirectory`, `findOrderById`) and `infra/mongo-order-directory.ts` (`MongoOrderDirectory`) are unchanged from the prior map.

## Duplication candidates

One pair flagged:

- `domain/refund-ledger.ts` (`RefundLedger`) and `domain/credit-ledger.ts` (`CreditLedger`). Shared: both import only `domain/order-directory.ts`; both export a single class with an identical constructor shape (`constructor(private orders: OrderDirectory)`); both expose one method matching the pattern `record*(orderId: string, amount: number): void` (`recordRefund` / `recordCredit`) and one matching `list*ByOrder(orderId: string): X[]` (`listRefundsByOrder` / `listCreditsByOrder`). No opinion is offered on whether this is a real duplication or two independently-evolving concerns that happen to share a shape today — that call belongs to whoever owns it downstream.

No other module pair in the current map shows substantially overlapping exports or import targets.

## Wrong-direction candidates

One new edge flagged:

- `domain/assign-refund.use-case.ts` (tier 1) → `infra/mongo-refund-store.ts` (tier 3). This is a new edge (see above) where the importing module's recorded tier (1) is more important than the imported module's tier (3). Flagged purely against the tiers already on record from this slice's design doc; whether it's a violation worth acting on is not this report's call.

All other new internal edges (`domain/credit-ledger.ts` → `domain/order-directory.ts`, `domain/refund-ledger.ts` → `domain/order-directory.ts`) run between two tier-1 modules — same tier, not flagged. No new edge involves an untiered module on either side, so no untiered-direction-unknown cases arose this run.

---

Note on invocation mode: this was run as a "real" update (per the task framing — diffed against the actual prior persisted map, intended to become the next baseline). Per the dry-run constraint on this eval, no file was written; the markdown above is the complete artifact that a real run would have persisted.
