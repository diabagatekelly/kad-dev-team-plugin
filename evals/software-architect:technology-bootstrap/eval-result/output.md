Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/technology-bootstrap/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/supply-chain-review/SKILL.md

Before applying the demand test, one thing isn't established yet: who's building and maintaining this. Asking — *(scripted answer: "Just me. Solo side project, and I'd rather not maintain a lot of tooling.")* — noted, and every recommendation below is scaled to a solo maintainer who wants minimal upkeep, not team-scale tooling.

Working through the design: strategic types (Account, Transaction, ConnectionOutcome), a bank-connection adapter, a persistence-interface-backed store, and a transaction list view. Applying the demand test — *can slice 1's first failing test be written without deciding this?* — category by category:

**Language and runtime — forced.** Recommending **TypeScript on Node.js**. Rejected: Python (no fluency advantage stated, and would split the stack from the web UI this slice already implies for no benefit) and Go (strong for typed backends, but heavier ecosystem switch for a solo maintainer with no stated need for it). Presenting for approval — *(scripted answer: "I'm most fluent in TypeScript and I'd like to stay there — the UI is going to be a web app anyway.")* — approved, and this also confirms the recommendation independently. **Flagging as ADR-worthy**: this is the choice the rest of the stack follows from.

**Test runner — forced.** Recommending **Vitest**. Rejected: Jest (still the more established choice, but needs extra config for native ESM/TS in a new project, which is exactly the upkeep a solo maintainer said they don't want) and Mocha+Chai (more assembly required for equivalent functionality). Presenting for approval — *(scripted answer: "Whatever you'd recommend as the standard choice for that ecosystem — I don't have a preference, go with it.")* — approved.

**Package manager and its pinning posture — forced.** This one touches a runtime-safety question, so consulting `supply-chain-review` first for its standard, not for a full audit (there's no repo yet to audit): its mental model is that a lockfile is a trust anchor only if it (a) carries content hashes for transitive dependencies, not just direct ones, and (b) is installed from in a frozen mode that fails on drift rather than silently re-resolving. Applying that standard plus this skill's own "defaults over flags" tiebreak: **recommending pnpm**. All three mainstream candidates (npm, Yarn, pnpm) write content hashes into their lockfiles by default. The difference is frozen-mode installs: npm and Yarn Classic both support a strict mode, but it requires remembering to invoke it (`npm ci` instead of `npm install`; `yarn install --frozen-lockfile`) — a flag depends on everyone remembering it, including a one-off script two years from now. pnpm detects a CI environment and refuses to move off the lockfile without an explicit override, so the safe posture holds without anyone opting in. Rejected: npm (safe posture requires remembering the right command), Yarn Classic (same flag-dependent gap). Presenting for approval — *(scripted answer: "I want whatever means I don't have to remember a flag to stay safe. Pick the one where that's the default.")* — approved, and it's the same reasoning already applied. **Flagging as ADR-worthy**: sets a security posture for the life of the project and the reasoning here is genuinely non-obvious (both end states audit identically after the fact).

**UI framework — not forced by the first test.** The design's first testable behavior is the connection/store logic (an account connects, its outcome is recorded, transactions are retrievable from the store) — none of that requires rendering anything. The transaction list view is real and will need a framework choice, but not before the first failing test exists. Leaving this open rather than deciding it now.

**Persistence technology — not forced.** The design already names a persistence boundary (strategic-owned interface, store adapter implements it), and slice 1 states transactions only need to last the current session — "re-pulling on next use is acceptable and expected." An in-memory implementation behind that interface satisfies every acceptance criterion here. The boundary is what makes deferring this free. Owner: `architecture-design`, per boundary, once a future slice needs data to survive a restart.

Everything else — hosting, CI/CD, a database, a deployment target, an auth provider — wasn't raised as a question at all; asking would produce infrastructure this slice doesn't ship with. Confirmed via the general catch-all — *(scripted answer: "I haven't thought about that yet and don't want to decide it now.")* — which is exactly right, since none of it is forced.

```markdown
# Technology bootstrap: Slice 1 — Connect one checking account and see its transactions

## Situation
Solo maintainer, side project, explicitly wants minimal tooling to maintain.
Unblocking slice 1's first failing test in a currently empty repository.

## Decided
- **Language/runtime: TypeScript on Node.js.** Forced — no test can be
  written without a language. Matches the maintainer's stated fluency and
  the web-app UI this slice implies. **ADR-worthy** — the rest of the stack
  follows from this.
- **Test runner: Vitest.** Forced — same reason. Native ESM/TS support with
  no extra config, matching a solo maintainer's low-upkeep preference.
- **Package manager: pnpm, with its default frozen-lockfile-on-CI
  behavior kept on.** Forced — the moment a dependency is installed there's
  a lockfile. Chosen over npm/Yarn because its safe posture (refuses to
  drift from the lockfile in CI) is the default, not a flag someone has to
  remember. **ADR-worthy** — sets a security posture for the life of the
  project via a non-obvious distinction.

## Considered and rejected
- **Language/runtime:** Python — no fluency or technical advantage stated,
  would split the stack from the web UI for no benefit. Go — solid choice
  in general, but an unnecessary ecosystem switch for a solo maintainer.
- **Test runner:** Jest — still common, but needs extra configuration for
  native ESM/TS in a new project; that's upkeep the maintainer said they
  don't want. Mocha+Chai — more manual assembly for equivalent coverage.
- **Package manager:** npm — lockfile hashing is fine, but frozen installs
  require remembering `npm ci` over `npm install`. Yarn Classic — same
  flag-dependent gap (`--frozen-lockfile`).

## Deliberately not decided yet
- **UI framework** — not forced by the first failing test (that test
  exercises connection/store logic, not rendering). Decide when the first
  test that actually drives a screen is written.
- **Persistence technology** — the persistence boundary already exists, and
  an in-memory implementation satisfies every acceptance criterion in this
  slice (transactions are session-only by design). Owner: `architecture-design`,
  per boundary, once a future slice needs data to survive a restart.
- **Hosting, deployment, CI/CD** — owner: `devsecops-engineer:operational-readiness`,
  once there's an actual delivery path to review.
- **Auth provider** — not relevant to this slice (it doesn't authenticate a
  user); owner: `architecture-design` per boundary plus a `devsecops-engineer`
  consult, only if a future slice authenticates someone.
- **Secrets storage** — the slice's security criteria already say the vendor
  access token is not persisted in slice 1, so nothing forces a secrets
  store yet. Owner: same consult, when a future slice needs to hold one.

## Consults
`supply-chain-review` (inline, via `devsecops-engineer`): asked what
"pinned" actually means for a package manager. Answer applied above — a
lockfile with content hashes for transitive dependencies, installed in a
mode that fails on drift rather than silently re-resolving; the choice
itself stayed mine, using "defaults over flags" as the tiebreak.
```
</content>
