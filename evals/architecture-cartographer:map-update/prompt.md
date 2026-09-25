---
name: architecture-cartographer:map-update
tags: [architecture-cartographer, map-update]
runs: 3
---

Run `map-update` for real, against the working tree below, diffing
against the prior persisted map.

**Prior map:**

```markdown
# Architecture map — updated 2026-08-01

## Modules
| Path | Tier | Internal edges (imports) | External packages | Public exports |
|---|---|---|---|---|
| domain/order-directory.ts | tier 1 | none | none | OrderDirectory, findOrderById |
| infra/mongo-order-directory.ts | tier 3 | domain/order-directory.ts | mongodb | MongoOrderDirectory |
```

**This slice's design doc states:** "Importance ordering assumed:
`OrderDirectory`, `RefundLedger`, `CreditLedger`, and `AssignRefundUseCase`
are strategic (tier 1). `MongoOrderDirectory` and `MongoRefundStore` are
tactical (tier 3)."

**The current working tree's source files:**

```typescript
// domain/order-directory.ts
export interface OrderDirectory {
  findOrderById(id: string): Promise<Order>;
}
export function findOrderById(id: string): Promise<Order> { /* ... */ }
```

```typescript
// domain/refund-ledger.ts
import { OrderDirectory } from './order-directory';

export class RefundLedger {
  constructor(private orders: OrderDirectory) {}
  recordRefund(orderId: string, amount: number): void { /* ... */ }
  listRefundsByOrder(orderId: string): Refund[] { /* ... */ }
}
```

```typescript
// domain/credit-ledger.ts
import { OrderDirectory } from './order-directory';

export class CreditLedger {
  constructor(private orders: OrderDirectory) {}
  recordCredit(orderId: string, amount: number): void { /* ... */ }
  listCreditsByOrder(orderId: string): Credit[] { /* ... */ }
}
```

```typescript
// domain/assign-refund.use-case.ts
import { MongoRefundStore } from '../infra/mongo-refund-store';

export class AssignRefundUseCase {
  constructor(private store: MongoRefundStore) {}
  execute(orderId: string, amount: number): void { /* ... */ }
}
```

```typescript
// infra/mongo-order-directory.ts
import { OrderDirectory } from '../domain/order-directory';
import { MongoClient } from 'mongodb';

export class MongoOrderDirectory implements OrderDirectory { /* ... */ }
```

```typescript
// infra/mongo-refund-store.ts
import { MongoClient } from 'mongodb';

export class MongoRefundStore {
  constructor(private client: MongoClient) {}
  save(refundId: string, amount: number): Promise<void> { /* ... */ }
}
```

```typescript
// util/currency-format.ts
export function formatCurrency(amount: number): string { /* ... */ }
```

These seven files are the complete current working tree — nothing else
exists to scan.
