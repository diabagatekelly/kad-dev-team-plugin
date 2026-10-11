---
model: sonnet
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Could someone abuse this endpoint? It lets staff refund a fine payment.

```typescript
router.post('/charges/:id/refund', async (req, res) => {
  const refund = await stripe.refunds.create({ charge: req.params.id });
  res.json({ refundId: refund.id });
});
```
