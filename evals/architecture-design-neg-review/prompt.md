---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

This is already in production. Does it respect our dependency rules?

```typescript
import { PgClient } from 'pg-orm';

export class RenewLoan {
  constructor(private readonly db: PgClient) {}

  async run(loanId: string): Promise<void> {
    await this.db.query('update loans set due = due + 14 where id = $1', [loanId]);
  }
}
```
