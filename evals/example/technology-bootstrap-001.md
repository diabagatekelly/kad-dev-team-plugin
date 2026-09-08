# Technology bootstrap: unblocking slice 1's first failing test

## Situation

One person building and maintaining this, on their own machine, for their
own money. Every recommendation below was scaled to that — the team-sized
answer offered to one person produces setup nobody maintains.

The slice being unblocked is slice 1: connect one institution and see its
transactions. Nothing here is a stack plan for the project.

## Decided

**Language and runtime — TypeScript on Node.** *Recommended and approved.*
Forced because no test can be written without it. One language across
browser and server means one ecosystem for a solo maintainer; aggregator
providers ship JavaScript SDKs first; and static types earn their keep
precisely at the adapter boundary, where the provider's payload is
translated into a `Transaction`.

**Flagged ADR-worthy** — the library ecosystem and every later choice
follow from it, and reversing it means rewriting rather than porting.
**Written up as ADR-002.** The dependency-surface cost and the pinning
posture adopted in response are recorded there as consequences.

**Test runner — Vitest.** *Recommended and approved.* Forced because "how
tests are invoked" has to exist before a test can fail. Runs TypeScript
with no separate build step, and the watch ergonomics are what a solo
maintainer will actually keep using. Not ADR-worthy — a test runner is
cheap to change.

**Package manager — pnpm.** *Recommended and approved.* Forced because the
first installed dependency creates a lockfile, and pinning is far cheaper
now than retrofitted across a dependency tree later.

Chosen on the criterion that matters beyond ergonomics: **prefer the
manager where the safe posture is the default rather than a flag someone
has to remember.** npm was genuinely close — its lockfile also carries
integrity hashes by default. pnpm won a narrow tiebreak by additionally
refusing to resolve packages that were never declared, which npm's flat
layout silently permits. That removes a class of mistake rather than
documenting it.

**Resulting pinning posture**, recorded so the next person can tell it was
chosen rather than inherited — see the consult below for where the standard
came from:

- Exact versions in the manifest; no floating ranges.
- Lockfile committed, carrying content hashes for transitive dependencies,
  not only direct ones.
- Installs run in frozen mode, failing on drift rather than resolving
  fresh. A lockfile nobody installs from in frozen mode is decoration.
- Dependency lifecycle scripts not run by default, with a narrow allowlist
  if something genuinely needs one. These execute before any project code
  does, which makes them the highest-leverage vector in this ecosystem.
  Cost: a package needing a build step must be allowlisted deliberately.

**UI framework — React with Vite.** *User's decision, overriding the
recommendation.* The demand test said this was not forced: slice 1's first
failing test covers connecting and translating against an in-memory
institution source, with no screen involved. The user chose to decide it
now on the grounds that the slice does ship a UI and several of its criteria
are about display — the untrusted-merchant-text criterion and the five
failure states that must be distinguishable.

Recorded as an override rather than as a recommendation, because it is one.
The honest driver, stated when it was presented: slice 1's two screens need
no framework at all. The reason to pick one is the spending and budget views
in later scope-map steps, which makes this a bet on work that isn't
specified yet. Vite pairs directly with Vitest, so it adds one toolchain
rather than two. Cost accepted: the largest dependency surface of the
options considered, on a project whose premise is minimizing what touches
financial data.

## Considered and rejected

| Category | Rejected | Reason |
|---|---|---|
| Language | Python backend + JS frontend | Two languages and two dependency ecosystems maintained by one person — the cost a solo maintainer feels most. |
| Language | Go backend + JS frontend | Small dependency surface genuinely suits the security posture, but same two-ecosystem cost, and a smaller pool of provider SDKs. |
| Test runner | `node:test` | Zero added dependencies, and a real contender given this project's premise — but a TypeScript execution path is still needed, so it's less dependency-free in practice than it looks, and the ergonomics gap is what gets a solo project to stop writing tests. |
| Test runner | Jest | Heavier, slower on TypeScript, configuration burden with no benefit at this size. |
| Package manager | npm | Safe by default too; lost a close tiebreak only on phantom dependencies. Would have been a fine choice. |
| Package manager | Yarn | Safe posture depends more on configuration; a third way of doing things for no solo-project benefit. |
| UI | Svelte with Vite | Smaller dependency surface, equally strong escaping story. Lost on ecosystem depth for the later budget views. |
| UI | Server-rendered HTML | Smallest surface by far and genuinely sufficient for slice 1. Rejected because the interactive budget views in the problem doc would likely force a framework later anyway. |

## Deliberately not decided yet

Named rather than omitted — an omitted decision is indistinguishable from a
forgotten one.

| Category | Owner, and when |
|---|---|
| **The data provider itself** | `software-architect`, as an open boundary question. Gating, and carrying four criteria now: free for personal use, covers the named institution, never returns the bank credential to the app, read-only with no payment capability, and revocable with deletion on request. |
| **Database / persistence** | `architecture-design`, per boundary — only once data must survive a restart. Design Decision 2 put that at slice 3. The boundary is what makes deferring free. |
| **Secrets storage** | `architecture-design` with a `devsecops-engineer` consult. Slice 1 does handle a secret (the provider client secret), but the criterion on it is "not committed" — how it's supplied is not forced before the first test. |
| **Auth provider** | Same, at slice 2, where authentication becomes the dominant concern. |
| **Hosting, deployment, CI/CD** | `devsecops-engineer:operational-readiness`, once a delivery path exists. Slice 1 ships without one by design — it runs on the user's machine. |
| **Monitoring and telemetry** | Not deferred, declined. reliability-requirements-001 rejected it for this scale and noted each pipeline would add an exit route for financial data. |

## Consults

**`devsecops-engineer:supply-chain-review`, for its standard only** — asked
what "pinned" actually means and what keeps a lockfile honest. Its answer,
recorded in the posture above: the lockfile is the trust anchor; pinning
decides what it points at, frozen-mode installs stop the build drifting off
it, and mutable references (version ranges, tags, branch names) are the
vulnerability while content hashes are the fix. It also flagged install-time
lifecycle scripts as the highest-leverage vector in this ecosystem.

Not run as an audit. It audits an existing repository's posture, and at
bootstrap there is no lockfile, no posture, and no build to compromise.

No security consult was needed for the test runner or the UI framework;
manufacturing one would have wasted a turn.
