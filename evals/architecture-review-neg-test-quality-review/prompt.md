---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Can you check whether these tests are actually verifying real behavior, or
just mocking everything away?

```typescript
describe('applyLoyaltyDiscount', () => {
  it('applies the discount', () => {
    const calc = { applyLoyaltyDiscount: jest.fn().mockReturnValue({ discountCents: 500 }) };
    const result = calc.applyLoyaltyDiscount(someOrder);
    expect(calc.applyLoyaltyDiscount).toHaveBeenCalled();
  });
});
```
