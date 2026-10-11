---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Is the error handling in this adapter right? Sometimes the mail provider
just hangs and I'm not sure what happens then.

```typescript
export class SendgridMailer implements Mailer {
  private readonly client = new MailClient(process.env.SENDGRID_API_KEY ?? '');

  async send(to: string, subject: string, body: string): Promise<void> {
    try {
      await this.client.send({ to, subject, body });
    } catch {
      // provider hiccup; the next nightly run will try again
    }
  }
}
```
