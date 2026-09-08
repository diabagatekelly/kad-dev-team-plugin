---
name: supply-chain-review
description: Audit a repository's dependency posture against one question — if an upstream package, registry, or maintainer account were compromised right now, would this repo pull the bad version on its next build? Covers packages, CI workflow references, and container base images, plus how accepted findings get recorded. Use when hardening dependencies, responding to a compromised-package advisory, or auditing a repo's supply-chain posture.
---

# Supply Chain Review

## The question this answers

**If an upstream package, registry, or maintainer account were compromised
right now, would this repository pull the bad version on its next build?**

Everything below serves that one question. It's worth stating out loud at
the start of a review, because it converts an open-ended topic into
something with an actual answer, and because it keeps the review from
drifting into "are our dependencies up to date," which is a different
question with a different answer.

This is a repo-posture audit, not a review of a change. It runs against a
repository, not a diff.

## The mental model

**The lockfile is the trust anchor.** It records exactly what resolved,
ideally with a content hash per artifact, so a later install gets the same
bytes or fails. Everything else exists to keep that anchor honest:

- **Pinning** decides what the anchor points at.
- **Frozen-mode installs** stop the build from silently moving off it.
- **Signature or attestation verification** establishes that the bytes came
  from who they claim.
- **Update automation** makes moving the anchor a deliberate, reviewable
  act rather than something that happens ambiently.

A repo can have all four and still be exposed if any one is missing — a
lockfile nobody installs from in frozen mode is decoration.

## Mutable versus immutable references

This is the single idea underneath most findings, and it generalizes
across every ecosystem, so reason from it rather than from a per-tool
checklist.

**Mutable references are the vulnerability**: version ranges, floating
specifiers, branch names, and tags — including release tags, which can be
re-pointed by the publisher or by anyone who compromises their account.

**Immutable references are the fix**: content hashes, full commit SHAs,
and image digests. Bytes that cannot change under you.

Apply it in all three places the supply chain actually reaches:

1. **Language packages** — exact versions in the manifest, a committed
   lockfile carrying content hashes for transitive dependencies too, and
   an install command in CI that fails on drift rather than resolving
   fresh.
2. **CI workflow references** — third-party actions and reusable workflows
   pinned to a full commit SHA, not a tag. A tag here is as mutable as any
   other tag, and the code runs with whatever access the job has.
3. **Container base images** — pinned by digest, not tag. The same
   reasoning extends to anything the image pulls in during its own build.

## What else to check

- **Transitive dependencies, not just direct ones.** The lockfile pins
  them; a review that only reads the manifest misses most of the tree.
- **Install-time code execution.** Lifecycle and install scripts run before
  any of your code does, which makes them the highest-leverage vector in
  ecosystems that allow them. Disabled by default with a narrow allowlist
  is the strong posture.
- **License risk.** Dependency risk isn't only vulnerabilities — a license
  incompatible with how the project is distributed is a real finding, and
  it usually arrives through a transitive dependency nobody chose.
- **Vulnerability triage is severity × reachability.** The same advisory in
  a production path and in a dev-only tool are not the same finding. Ask
  whether the vulnerable code path is reachable at all before ranking it.
- **Update automation is not pinning.** An automated-update configuration
  updates pins; it does not create them. Treating one as a substitute for
  the other is a common and confident mistake.
- **A private registry is not by itself a defense.** It changes who you
  trust, not whether the anchor holds. Check the lockfile still carries
  hashes and CI still runs frozen.

## Accepting a finding

Some findings will be accepted rather than fixed — no patched version
exists, the vulnerable path isn't reachable, the risk is understood and
tolerated. That's legitimate, and how it's recorded is what decides whether
it stays legitimate.

**An accepted finding needs a named classification and a written reason,
recorded where the next person will find it.** Bare suppression, with no
reason attached, is indistinguishable from an oversight six months later —
and the person who has to judge it will not be the person who accepted it.

Useful classifications:

- **Not vulnerable — false positive**: the flagged pattern isn't what the
  scanner thinks it is.
- **Not vulnerable — mitigated by design**: the code is intentional and
  something structural prevents exploitation. Say what that something is.
- **Accepted risk**: real, understood, tolerated for a stated reason.

**The user picks the classification — never infer it.** These differ in
what they claim: "false positive" asserts the scanner is wrong, "accepted
risk" asserts a judgment about consequences. Only the person who owns the
consequences can make the second claim, and quietly filing a real risk as
a false positive is how a suppression list stops meaning anything. Ask via
`AskUserQuestion` and record the reason in their terms.

**Don't offer "accept temporarily" unless something actually enforces the
expiry.** Without a mechanism that surfaces it again on a date, a temporary
acceptance is a permanent one wearing a disguise, and it's worse than a
plain acceptance because it reads as though someone will revisit it.

## Findings and severity

- **Critical** — nothing pins at all on a path that reaches production: no
  lockfile, or CI resolving fresh on every build.
- **High** — a mutable reference on a path that executes with meaningful
  access (an unpinned CI action in a job holding credentials, a
  tag-pinned base image for a deployed service). A reachable known
  vulnerability with a fix available.
- **Medium** — pinned but unverified (no signature or attestation checking
  where available). Install scripts enabled with no allowlist. A license
  finding requiring a decision.
- **Low** — hardening with no current exposure; a dev-only vulnerability
  that isn't reachable.

Use the same finding report format as `security-review`, with
**Reachability** stating what a compromise upstream would actually reach.

If the repo's posture is already sound, say so plainly and name what's
holding it up, so the next audit knows what it's protecting rather than
re-deriving it.
