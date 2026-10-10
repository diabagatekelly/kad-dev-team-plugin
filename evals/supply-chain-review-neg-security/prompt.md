---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Is this search handler safe? A member types the title they're looking for.

```typescript
router.get('/portal/history', async (req, res) => {
  const title = String(req.query.title ?? '');
  const rows = await db.query(
    `select isbn, title from loans where card_number = $1 and title ilike '%${title}%'`,
    [sessionOf(req).cardNumber],
  );
  res.json(rows);
});
```
