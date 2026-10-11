---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

This is how we collect a fine today. What happens when Stripe or the database misbehaves here?

```typescript
async run(fineId: string, cardToken: string): Promise<void> {
  const fine = await this.ledger.find(fineId);
  if (!fine || fine.settledOn !== null) return;
  const outcome = await this.payments.charge(cardToken, fine.amountCents, `Library fine ${fine.id}`);
  if (!outcome.ok) throw new Error('Payment failed.');
  await this.ledger.settle(fine.id, outcome.chargeId, this.clock().toISOString().slice(0, 10));
}
```
