---
name: devsecops-engineer:reliability-review
tags: [devsecops-engineer, reliability-review]
runs: 3
---

Review this code for reliability issues. It's a nightly job that syncs
transactions for every connected account:

```typescript
// domain/syncTransactions.ts
export async function syncTransactionsForAccount(account: Account) {
  let transactions;
  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      transactions = await bankClient.fetchTransactions(account.connectionId);
      break;
    } catch (err) {
      logger.debug(`fetch failed for account ${account.id}, retrying`, err);
      await sleep(2000);
    }
  }
  if (!transactions) {
    return;
  }
  await transactionStore.save(account.id, transactions);
}

export async function syncAllAccounts() {
  const accounts = await accountStore.getAll();
  for (const account of accounts) {
    await syncTransactionsForAccount(account);
  }
}
```

```typescript
// infra/bankClient.ts
export async function fetchTransactions(connectionId: string) {
  const response = await fetch(`https://api.bankprovider.com/accounts/${connectionId}/transactions`);
  if (!response.ok) {
    throw new Error(`provider returned ${response.status}`);
  }
  return response.json();
}
```

`bankClient.fetchTransactions` is the only thing this job depends on. The
provider's API returns 401 when a connection's authorization has been
revoked by the user — a state that can't be fixed by retrying.
