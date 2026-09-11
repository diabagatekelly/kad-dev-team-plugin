---
name: devsecops-engineer:supply-chain-review
tags: [devsecops-engineer, supply-chain-review]
runs: 3
---

Audit this repository's supply-chain posture.

```yaml
# .github/workflows/deploy.yml
name: Deploy
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: some-org/deploy-action@v2
      - run: npm install
      - run: npm run build
      - run: docker build -t app:latest .
      - run: ./deploy.sh
```

```dockerfile
# Dockerfile
FROM node:20
COPY . .
RUN npm install --production
CMD ["node", "server.js"]
```

`package-lock.json` is committed and up to date. A Renovate config exists
at `.github/renovate.json` with default settings, opening a weekly PR for
any outdated dependency.

Two things the team believes, worth checking rather than assuming true:

1. "We have Renovate auto-updating dependencies weekly, so our supply
   chain posture is already covered."
2. "Our npm packages come from our company's private registry, so we don't
   need to worry about a public-registry compromise."
