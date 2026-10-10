---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

This nightly job calls our SMS provider for every member with a book due
soon. Will it hold up in production — what happens when the provider is
slow or down, and would I even notice?

```typescript
export async function sendReminders(loans: Loan[], sms: SmsClient): Promise<void> {
  for (const loan of loans) {
    await sms.send(loan.phone, `Your book ${loan.isbn} is due ${loan.dueOn}.`);
  }
}

setInterval(() => void sendReminders(loadDueSoon(), smsClient), 24 * 60 * 60 * 1000);
```
