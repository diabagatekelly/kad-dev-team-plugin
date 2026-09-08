# Security requirements: Slice 1 — Connect one institution and see its transactions

Replaces the security placeholder in slice-001. Written against design-001,
which materially changed what's in play: the bank credential never enters
the system, and the access token and provider callback do.

## What's in play

Established by asking, not assumed.

**Sensitive data classes**

| Class | Status in this slice |
|---|---|
| Bank username and password | **Never enters.** The provider's connect flow holds them. This is the slice's strongest security property. |
| Provider access token | Enters, lives in memory only, never at rest (design Decision 2). Grants read of financial history. |
| **Provider client secret** | Enters. This is the credential the *app* uses to authenticate to the provider — distinct from the bank credential, and easy to miss precisely because Decision 1 removed the more obvious one. |
| Transaction history | Enters, in memory only. Dates, amounts, merchant descriptions. |

**Users and separation:** none. No user concept exists in this slice
(design Decision 4), and the app is not network-reachable. Authorization is
therefore nearly absent here and becomes the dominant concern in slice 2.

**Obligations:** none beyond the provider's and the bank's terms of
service. Purely personal use, own accounts, no regulatory regime — the user
confirmed this, and no regime is being assumed.

**Host:** a machine the user alone uses and controls. This is what makes
"no authentication because it's local" a real property rather than a
convenience.

**Existing conventions to match:** none. Greenfield.

## Threat pass

**What an attacker would want, specifically:**

1. **The provider access token** — the prize. Yields the user's full
   transaction history through the provider, without touching the bank.
2. **The provider client secret** — lets an attacker act as this
   application against the provider.
3. **The transaction history itself** — merchant names, amounts, and timing
   are a detailed profile, useful for targeted fraud even with no account
   access.

**Where untrusted input or identity crosses in:**

1. **The provider's callback** delivering the token at the end of the
   connect flow. A trust boundary — the app must not accept a token from an
   arbitrary caller.
2. **The provider's API responses.** Transaction descriptions originate
   from merchants and the bank, not from the provider or the user. They are
   externally controlled text that gets rendered.
3. **The user's own input** in the connect flow (which institution).

**What's reachable from there:**

The second entry point is the one that isn't theoretical. A transaction
description containing markup, rendered into the transaction list, executes
in the same context that holds the access token in memory — so untrusted
text from a merchant name reaches the highest-value secret in the slice.
That chain is what earns it a criterion rather than a mention.

**Considered and dismissed, with reasons** — so no one re-derives them:

- **Encryption at rest** — nothing is stored (design Decision 2). Not a
  weak control here; an absent one. Returns as a real concern at slice 3,
  when refresh forces persistence.
- **Authorization between users** — no user concept exists. Slice 2.
- **Session handling and CSRF** — no authentication and no sessions. Slice 2.
- **Rate limiting and abuse** — the app is loopback-bound with one user;
  there is no attacker population. Provider-side throttling is a
  reliability concern, not this.
- **Audit logging** — no obligations regime applies, and there is no second
  party to be accountable to.

## Acceptance criteria

These sit alongside slice-001's functional criteria, in the same form.

**The credential never enters**
> **Given** the user is completing the provider's connect flow,
> **When** they submit their bank username and password to that flow,
> **Then** no bank username or password crosses the institution-transactions
> boundary into the application, and the application receives only an access
> token.

**The app is not reachable from another machine**
> **Given** the app is running,
> **When** a request is made to it from any host other than the machine it
> runs on,
> **Then** the request is not served.

This is the testable statement of the boundary slice-001's scope depends
on. If this criterion cannot hold, the no-authentication narrowing is void.

**Secrets stay out of logs**
> **Given** a connection is being established or transactions are being
> retrieved,
> **When** any log output is produced, including on the failure paths,
> **Then** no line contains the access token or the provider client secret.

**Failures don't leak the provider's internals**
> **Given** the provider returns an error during connection or retrieval,
> **When** the app reports the failure to the user,
> **Then** the message describes what failed without including the
> provider's raw response, the request headers, or the access token.

**A failed connection leaves nothing behind**
> **Given** a connect attempt fails partway through,
> **When** the user retries,
> **Then** no token or partial connection state from the failed attempt is
> still held by the application.

**The client secret is not committed**
> **Given** the repository,
> **When** it is inspected,
> **Then** the provider client secret is not present in any committed file,
> and the app reports a clear startup failure when it is absent rather than
> running in a degraded state.

**Untrusted merchant text is displayed, not executed**
> **Given** a retrieved transaction whose description contains markup or
> script content,
> **When** it is shown in the transaction list,
> **Then** the description is displayed as literal text and no part of it is
> interpreted as markup or executed.

**Test data is fabricated**
> **Given** tests exist for the institution-transactions adapter,
> **When** they run,
> **Then** they use a fabricated token and fabricated transactions, and no
> real provider credential or real account data appears in any fixture.

**Transport is encrypted**
> **Given** the app requests data from the provider,
> **When** the request is made,
> **Then** it is sent over an encrypted connection, and a non-encrypted
> endpoint is refused rather than silently accepted.

### Criteria on provider selection

Verified before integration, not after. These gate the architect's open
provider question.

**Read-only, no payment capability**
> **Given** a candidate provider,
> **When** the access the app would receive is reviewed,
> **Then** that access permits reading transactions only and cannot
> initiate a payment or transfer.

**Amended after provider selection.** With Plaid chosen, this is enforced
by *this application* requesting only the transactions product — Plaid's
Transfer capability is a separate product the app simply does not ask for.
It is app-side discipline, not something the provider prevents. The
criterion still holds and is still checkable; it is checkable against our
own link-token request, not against a provider guarantee. SimpleFIN was the
only candidate where read-only was structural, and it failed the cost
constraint.

**Revocation and deletion**
> **Given** the user wants to end the relationship with the provider,
> **When** they follow the provider's documented process,
> **Then** the connection can be revoked and deletion of their data can be
> requested.

## Decisions

**Accepting a third party as holder of the bank credential.** *Approved by
the user, conditional on vetting.* The provider holds what this app
deliberately doesn't. Rejected alternative: the app holding the credential
itself, which would reverse design Decision 1.

**Flagged ADR-worthy** — placing a trust boundary and accepting a known
class of risk both clear the bar. **Written up as ADR-001**, merged with
design Decisions 1 and 5 rather than kept as a separate record: the
mechanism, the vendor, and the accepted risk only make sense read together.
The declined vetting bars are recorded there as an explicit consequence.

**What "vetted" means.** *User selected read-only access and deletion on
demand.* Offered and not selected: a published security posture (SOC 2 or
equivalent), and documented credential handling.

**Accepted risk, recorded rather than escalated.** Declining the
documented-credential-handling bar means the property this entire design
rests on — that the provider never returns the bank credential to the app —
holds by observed behavior rather than by written guarantee. That is a
defensible trade-off for personal tooling and it is the user's call, not
this persona's to override. It is written down so it is a decision rather
than an oversight, and so it can be revisited if the slice ever becomes
network-reachable.

## Out of scope for this slice

- **Everything authentication and authorization** — slice 2, where it
  becomes the dominant concern rather than an absent one.
- **Protecting data at rest** — slice 3, when refresh forces persistence
  and the token stops being memory-only.
- **Connection expiry and re-authorization** — slice 4.
- **Anything that moves money** — excluded from the problem's current
  scope, and now excluded at the provider level by the read-only criterion.

## Open questions

- ~~**Does the provider's connect flow require a publicly reachable
  callback?**~~ **Resolved.** Plaid permits `https://localhost` as a
  redirect URI in Production, so the not-reachable-from-another-machine
  criterion and the provider's callback requirement are not in conflict.
  Slice 1 does not change shape, and no scope decision needs to go to
  `product-slicer`. A self-signed certificate is required for local HTTPS,
  which is a setup cost, not a security finding.
- ~~**Provider selection carries two additional gating criteria**~~
  **Delivered to `software-architect` and applied** — see Decision 5 in
  design-001.
- **The provider client secret criterion is correctly worded for Plaid.**
  Worth recording because it nearly wasn't: Teller would have required an
  mTLS client certificate, making the app-held secret a private key rather
  than a client secret, and this criterion would have needed rewording.
  Plaid uses a client ID and secret, so it stands as written.
- ~~**Revocation and deletion is still unverified for Plaid**~~ **Verified,
  criterion satisfied.** Two independent paths exist: this app can call
  `/item/remove`, which deletes the Item's product data and cannot be
  undone without re-linking; and the user can independently disconnect the
  app and delete their data from Plaid's systems through Plaid Portal
  (my.plaid.com), with a Privacy Request Form as fallback. Bank-side
  revocation via the institution's own connected-apps settings is a third
  path Plaid doesn't control.

  **Caveat, moot now and real later:** deleting data from Plaid does not
  delete data already held by *this* application. Slice 1 persists nothing
  (design Decision 2), so there is nothing here to strand. This becomes a
  genuine obligation at slice 3, when refresh forces persistence — deletion
  at the provider will no longer imply deletion in the app.
