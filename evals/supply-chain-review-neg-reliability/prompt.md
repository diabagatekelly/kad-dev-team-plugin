---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Our fine-payment call sometimes fails when the payment provider has a blip.
Is this retry a good idea?

```typescript
async function chargeWithRetry(card: string, cents: number): Promise<Charge> {
  for (let attempt = 1; ; attempt++) {
    try {
      return await stripe.charges.create({ amount: cents, currency: 'usd', source: card });
    } catch (error) {
      if (attempt === 5) throw error;
    }
  }
}
```
