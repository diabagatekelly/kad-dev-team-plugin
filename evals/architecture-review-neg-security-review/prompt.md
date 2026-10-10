---
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Can you check this JWT authentication middleware for security
vulnerabilities — things like signature validation bypasses, algorithm
confusion, or missing expiry checks?

```typescript
export function authenticate(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  const payload = jwt.decode(token);
  req.user = payload;
  next();
}
```
