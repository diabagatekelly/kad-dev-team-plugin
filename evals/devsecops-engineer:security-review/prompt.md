---
name: devsecops-engineer:security-review
tags: [devsecops-engineer, security-review]
runs: 3
---

Review this code for security issues:

```typescript
// app.ts
app.use('/invoices', requireAuth, invoicesRouter);
```

```typescript
// middleware/auth.ts
export function requireAuth(req, res, next) {
  const user = verifyToken(req.headers.authorization);
  if (!user) return res.status(401).end();
  req.user = user;
  next();
}
```

```typescript
// routes/invoices.ts
router.get('/invoices/:id', async (req, res) => {
  const invoice = await db.query(`SELECT * FROM invoices WHERE id = ${req.params.id}`);
  if (!invoice) return res.status(404).json({ error: 'not found' });
  res.json(invoice);
});

router.post('/invoices/:id/export', async (req, res) => {
  try {
    const invoice = await db.query(`SELECT * FROM invoices WHERE id = ${req.params.id}`);
    const outPath = `/tmp/export-${req.params.id}.pdf`;
    exec(`wkhtmltopdf ${req.query.template || invoice.templateUrl} ${outPath}`);
    res.download(outPath);
  } catch (err) {
    res.status(500).json({ error: err.message, stack: err.stack });
  }
});
```

```typescript
// services/billing.ts
const STRIPE_SECRET_KEY = 'sk_live_51H8x2KJ9pQ...';

function logInvoiceAccess(invoice, user) {
  logger.info('invoice accessed', { invoice, user });
}
```

`invoicesRouter` above is the only router mounted at `/invoices`; nothing
else in the app touches invoice data.
