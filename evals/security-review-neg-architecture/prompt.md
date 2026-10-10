---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Is this use case structured well? I'm not sure the ORM belongs in here, and
I'd like to know whether the dependencies point the right way.

```typescript
import { OrmRepository, PgClient } from 'pg-orm';
import { LoanRow } from '../infra/postgres/loan-row';

export class RenewLoan {
  private readonly loans: OrmRepository<LoanRow>;

  constructor(client: PgClient) {
    this.loans = new OrmRepository<LoanRow>(client, 'loans');
  }

  async run(loanId: string): Promise<LoanRow> {
    const row = await this.loans.findOne({ id: loanId });
    if (!row || row.renewals >= 2) throw new Error('cannot renew');
    row.renewals += 1;
    await row.save();
    return row;
  }
}
```
