---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Is this use case structured right? I'm not sure the business logic should
know this much about our database and payment provider.

```typescript
import { PgClient } from 'pg-orm';
import { StripeClient } from 'stripe-sdk';

export class CollectFine {
  constructor(private readonly db: PgClient, private readonly stripe: StripeClient) {}

  async run(fineId: string, cardToken: string): Promise<void> {
    const [fine] = await this.db.query<{ amount_cents: number }>('select amount_cents from fines where id = $1', [fineId]);
    const charge = await this.stripe.charges.create({ amount: fine.amount_cents, currency: 'usd', source: cardToken });
    await this.db.query('update fines set charge_id = $2 where id = $1', [fineId, charge.id]);
  }
}
```
