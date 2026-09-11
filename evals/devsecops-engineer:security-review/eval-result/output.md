Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/security-review/SKILL.md

## Finding: Any authenticated user can read or export any invoice by ID

**Location:** `routes/invoices.ts` — `GET /invoices/:id` and `POST /invoices/:id/export`
**Category:** Authorization (missing), distinct from authentication
**Severity:** Critical

**Reachability:** Both routes sit behind `requireAuth`, so the caller must be an authenticated user — but any authenticated user, not specifically the invoice's owner. `req.params.id` is fully caller-controlled with no ownership check against `req.user`.

**What's happening:** `requireAuth` establishes *who* the caller is; nothing on either route establishes that the caller *may access this specific invoice*. Any logged-in user can read or export any other user's invoice simply by supplying its ID.

**Why it matters:** Authentication and authorization answer different questions, and only the first is handled here. This isn't a hypothetical — it's the direct, intended behavior of both routes as written, reaching another user's financial data with no exploit beyond changing a number in the URL.

**Suggested fix:** Add an ownership check — look up the invoice's owner and compare against `req.user` before returning or exporting it, in both routes.

## Finding: SQL injection via unparameterized query interpolation

**Location:** `routes/invoices.ts` — both routes, identical pattern: `` db.query(`SELECT * FROM invoices WHERE id = ${req.params.id}`) ``
**Category:** Injection
**Severity:** Critical

**Reachability:** `req.params.id` is attacker-controlled and interpolated directly into SQL text with no parameterization or escaping.

**What's happening:** The query is built as a string with the caller-supplied ID spliced in directly, letting that value participate in SQL structure rather than staying data.

**Why it matters:** Beyond the ID itself, an attacker can inject arbitrary SQL — reading other tables, bypassing the intended query shape entirely. This compounds the authorization gap above rather than being redundant with it.

**Suggested fix:** Use a parameterized query / prepared statement for the ID everywhere this pattern appears, not manual escaping.

## Finding: Command injection via unsanitized query parameter passed to a shell command

**Location:** `routes/invoices.ts` — `POST /invoices/:id/export`: `` exec(`wkhtmltopdf ${req.query.template || invoice.templateUrl} ${outPath}`) ``
**Category:** Injection (OS command)
**Severity:** Critical

**Reachability:** `req.query.template` is a caller-supplied query parameter, passed directly into a shell command string with no sanitization, and preferred over the stored `invoice.templateUrl` when present.

**What's happening:** This is the same underlying shape as the SQL injection above — untrusted text becoming structure instead of staying data — on a different surface: a shell command instead of a query. An attacker-controlled `?template=` value can inject arbitrary shell syntax (e.g. `; rm -rf /` or a reverse shell) that `exec` will run.

**Why it matters:** This is the most severe finding here — it reaches code execution on the server, not just data exposure.

**Suggested fix:** Never build a shell command from caller input. If a template must be selectable, validate it against an allowlist of known template identifiers server-side, and use an execution API that takes arguments as an array rather than a single interpolated string.

## Finding: Live secret key hardcoded in source

**Location:** `services/billing.ts` — `const STRIPE_SECRET_KEY = 'sk_live_...'`
**Category:** Secrets in source
**Severity:** Critical

**Reachability:** Anyone with read access to the repository (including its history) has the live key.

**What's happening:** A live Stripe secret key is committed directly in source rather than sourced from a managed secret store at runtime.

**Why it matters:** This key grants live billing access. It's already compromised by virtue of having been committed, not just currently exposed.

**Suggested fix:** Move it to a managed secret store and load it at runtime. Rotate it — removing it from the current tree doesn't remove it from history, so a new key is required, not just deletion of this line.

## Finding: Stack trace and raw error message returned to the caller

**Location:** `routes/invoices.ts` — `POST /invoices/:id/export` catch block: `res.status(500).json({ error: err.message, stack: err.stack })`
**Category:** Information disclosure via error response
**Severity:** Medium

**Reachability:** Any caller who triggers a failure on this route (including the failures above) receives the full stack trace and raw error message in the response body.

**What's happening:** Internal detail — file paths, library internals, potentially query fragments — is returned directly to the caller instead of a generic failure message.

**Why it matters:** A caller should learn their request failed, not learn why in terms that describe the server's internals. This also becomes a second exit for anything sensitive that ends up in `err.message` (e.g. a DB error echoing part of the failed query).

**Suggested fix:** Return a generic error message to the caller; log the full error (through a channel that doesn't itself leak secrets) server-side instead.

## Finding: Whole objects logged instead of identifiers

**Location:** `services/billing.ts` — `logger.info('invoice accessed', { invoice, user })`
**Category:** Sensitive data exposure via logs
**Severity:** Medium

**Reachability:** Anyone with access to the application's logs.

**What's happening:** This logs the entire `invoice` and `user` objects, not specific fields or identifiers. This is a distinct problem from "a sensitive field got logged" — it's that logging the whole object leaks every field either one has, including fields added later by someone who never considered this log line when adding them.

**Why it matters:** The failure here is that it's unbounded and fails silently the moment either object gains a new sensitive field (a card token, an address, anything) — nobody reviewing a future change to `Invoice` or `User` is likely to notice this log line at all.

**Suggested fix:** Log identifiers instead — `{ invoiceId: invoice.id, userId: user.id }`. If the fact that access happened needs to be auditable, the audit record should log that access happened, not the data accessed.
</content>
