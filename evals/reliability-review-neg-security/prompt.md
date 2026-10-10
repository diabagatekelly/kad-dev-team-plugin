---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

This route lets a member look up their own library account. Can someone
use it to see another member's details, and is anything sensitive leaking
out of it?

```typescript
router.get('/portal/members/:cardNumber', async (req, res) => {
  const member = await members.findByCard(req.params.cardNumber);
  if (!member) {
    res.status(404).json({ error: `no member with card ${req.params.cardNumber}` });
    return;
  }
  log.info('portal lookup', { member });
  res.status(200).json(member);
});
```
