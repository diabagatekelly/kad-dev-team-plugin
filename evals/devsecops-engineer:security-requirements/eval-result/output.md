Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/security-requirements/SKILL.md

Answers received:
- Sensitive data: "The account connection credentials or token, and the transaction history it pulls in — nothing else yet."
- Users/separation: "Right now it's just me, but I don't want anything built that assumes there's only ever going to be one person using this."
- Obligations: "No — this is personal use of my own accounts. Nothing regulatory, nothing beyond the bank and the connection provider's own terms of service."
- Existing conventions: "Nothing — this is greenfield, no existing auth pattern anywhere in the app yet."

```markdown
# Security requirements: Slice 1 — Connect one account and see its transactions

## What's in play

Established by asking, not assumed.

**Sensitive data classes**

| Class | Status in this slice |
|---|---|
| Account connection credential/token | Enters, grants read access to the connected account's transaction history. |
| Transaction history | Enters once a connection succeeds. |

**Users and separation:** one person today, but nothing here may assume that's permanent — the connected account needs an owner reference, not a hardcoded singleton, so a second person can be added later without redoing this slice's data model.

**Obligations:** none beyond the bank and connection provider's own terms of service. No regulatory regime — confirmed, not assumed.

**Existing conventions to match:** none. Greenfield — no auth pattern exists anywhere in the app yet.

## Threat pass

**What an attacker would want, specifically:**

1. **The account connection credential/token** — the prize. Whoever holds it can read the connected account's full transaction history.
2. **The transaction history itself** — merchant names, amounts, and timing are a usable profile even without further account access.

**Where untrusted input or identity crosses in:**

1. **Every inbound request to the application itself.** The application is already hosted and reachable over the internet, and this slice's thin path — connect, select, list — has no login or identity check anywhere in it. That means every request that reaches the app is currently treated as the account owner, with nothing distinguishing the real owner from anyone else who reaches the same URL.
2. **The connection provider's responses**, including transaction descriptions, which originate from merchants and the bank, not from the app or the user.

**What's reachable from there:**

The first entry point is not theoretical — it's the whole slice. With no identity check and the app already reachable over the internet, anyone who reaches the app's URL can view the connected account's complete transaction history. This doesn't require exploiting anything; it's the direct, intended behavior of the thin path as currently scoped, running on infrastructure that makes it reachable by more than its owner. That is this slice's actual highest-severity exposure, more severe than anything reachable through the provider's responses.

**Considered and dismissed, with reasons:**

- **Encryption at rest** — nothing is described as persisted beyond the session in this slice; not a weak control, an absent need. Revisit if a later slice persists transaction data.
- **Monitoring, telemetry, and analytics as an exit route** — this is a greenfield slice with no telemetry or analytics mechanism of any kind, so there is currently nothing to leak sensitive data through this exit. Revisit the moment any telemetry is added, since that would create a new exit for the same data this document otherwise keeps inside the request/response path.
- **Rate limiting and abuse** — a reliability/availability concern once the app is genuinely serving multiple identities; not a security gap in itself.
- **Audit logging** — no obligations regime applies and there's no second party to be accountable to yet.

## Acceptance criteria

These sit alongside the slice's functional criteria, in the same form.

**Secrets stay out of logs**
> Given a connection is being established or transactions are being retrieved,
> When any log output is produced, including on failure paths,
> Then no line contains the account connection credential or token.

**Failures don't leak provider internals**
> Given the connection attempt fails,
> When the app reports the failure to the user,
> Then the message describes what failed without including the provider's raw response, request headers, or the credential/token value.

**Exceptions and stack traces don't carry the credential**
> Given an unhandled exception occurs anywhere in the account-connection or transaction-retrieval path,
> When the exception is raised and its stack trace is captured,
> Then neither the exception message nor the stack trace contains the credential/token, even though the failure-response criterion above governs only what's shown to the user.

**A failed connection leaves nothing behind**
> Given a connect attempt fails partway through,
> When the user retries,
> Then no credential or partial connection state from the failed attempt is still held by the application.

**Transport is encrypted**
> Given the app communicates with the connection provider,
> When a request is made,
> Then it is sent over an encrypted connection, and a non-encrypted endpoint is refused rather than silently accepted.

**Test data is fabricated**
> Given tests exist for the account-connection integration,
> When they run,
> Then they use a fabricated credential/token and fabricated transactions, and no real provider credential or real account data appears in any fixture.

## Decisions

No approval-seeking decisions in this pass — everything above applies the slice's own stated facts directly. The identity/access-control gap below is a finding, not a decision this pass gets to settle.

## Out of scope for this slice

- **Fine-grained authorization once a second identity exists** — not needed until a second person is actually added; noted so it isn't forgotten once the identity gap below is resolved.
- **Protecting data at rest** — nothing is persisted beyond the session in this slice as scoped.

## Open questions

None beyond the finding below. The actual identity/session model is a `software-architect` decision once `product-slicer` resolves what happens to this slice's scope.

## Finding — routed to `product-slicer`, not resolved here

**This slice has no login or identity check of any kind, and the application is already hosted and reachable over the internet, handling real financial data.** The criteria above protect the credential/token itself and the failure paths around it, but they don't and can't close this gap — without an identity check, the data those criteria protect is still readable by anyone who reaches the app, not just its owner. That's not a smaller version of the problem this document solves; it's a different problem this slice's current thin path (connect, select, list) was never scoped to cover.

This is a scope question, and scope belongs to `product-slicer`, not to this pass. I'm not resolving it here and not listing it as one option among several for you to pick — reporting it and routing it.

Reported and routed to `product-slicer`.
```
</content>
