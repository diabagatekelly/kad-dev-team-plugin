---
name: tdd-coach:test-quality-review
tags: [tdd-coach, test-quality-review]
runs: 3
---

Can you review the tests in `pricing.test.ts`? I want to know if they're
actually testing anything.

```typescript
// pricing.ts
export interface DiscountLookup {
  discountFor(customerId: string): number;
}

export class PricingService {
  constructor(private discounts: DiscountLookup) {}

  calculateTotal(items: { price: number; qty: number }[], customerId: string): number {
    if (!items) return 0; // items is required by the type; callers can't pass undefined
    const subtotal = items.reduce((sum, i) => sum + i.price * i.qty, 0);
    const discount = this.discounts.discountFor(customerId);
    return subtotal - subtotal * discount;
  }

  applyRounding(amount: number): number {
    return Math.round(amount * 100) / 100;
  }
}

export function isValidCustomerId(input: unknown): input is string {
  return typeof input === 'object' && 'length' in (input as any) && (input as any).length > 0;
}

export function formatReceiptLine(item: { price: number; qty: number }): string {
  return `${item.qty} x $${item.price.toFixed(2)}`;
}
```

`StubDiscountLookup` (in `test-doubles.ts`) is this codebase's designated
test double implementing `DiscountLookup` for tests — it always returns
`0` unless a test overrides it.

```typescript
// pricing.test.ts
import { describe, test, expect, vi } from 'vitest';
import { PricingService, isValidCustomerId } from './pricing';
import { StubDiscountLookup } from './test-doubles';

describe('PricingService', () => {
  test('calculates total with discount', () => {
    const discounts = new StubDiscountLookup();
    vi.spyOn(discounts, 'discountFor').mockReturnValue(0.1);
    const service = new PricingService(discounts);
    const total = service.calculateTotal([{ price: 100, qty: 1 }], 'cust-1');
    expect(total).toBe(90);
  });

  test('rounds correctly', () => {
    const service = new PricingService(new StubDiscountLookup());
    const result = service.applyRounding(9.005);
    expect(result).toBeGreaterThan(0);
  });

  test('calculateTotal returns the discounted total', () => {
    const service = new PricingService(new StubDiscountLookup());
    vi.spyOn(service, 'calculateTotal').mockReturnValue(999);
    const result = service.calculateTotal([{ price: 100, qty: 1 }], 'cust-1');
    expect(result).toBe(999);
  });

  test('uses a mocked discount client, logger, cache, and audit trail', () => {
    const discounts = { discountFor: vi.fn().mockReturnValue(0) };
    const logger = { log: vi.fn() };
    const cache = { get: vi.fn(), set: vi.fn() };
    const audit = { record: vi.fn() };
    const service = new PricingService(discounts as any);
    service.calculateTotal([{ price: 50, qty: 2 }], 'cust-2');
    expect(logger.log).not.toHaveBeenCalled();
    expect(cache.get).not.toHaveBeenCalled();
    expect(audit.record).not.toHaveBeenCalled();
  });

  test('applies zero discount when lookup fails', () => {
    const discounts = new StubDiscountLookup();
    const mockDiscountFor = vi.fn().mockReturnValue(0.5);
    const service = new PricingService(discounts);
    const total = service.calculateTotal([{ price: 100, qty: 1 }], 'cust-3');
    expect(total).toBe(100);
  });

  test('returns 0 for undefined items', () => {
    const service = new PricingService(new StubDiscountLookup());
    // @ts-expect-error exercising the defensive branch directly
    expect(service.calculateTotal(undefined, 'cust-1')).toBe(0);
  });

  test('isValidCustomerId accepts a real id', () => {
    expect(isValidCustomerId('cust-1')).toBe(true);
  });

  test('isValidCustomerId rejects an empty object', () => {
    expect(isValidCustomerId({})).toBe(false);
  });
});
```

Report what you find without editing the file.
