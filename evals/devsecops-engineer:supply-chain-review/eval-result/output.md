Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/supply-chain-review/SKILL.md

The question this audit answers: if an upstream package, registry, or maintainer account were compromised right now, would this repository pull the bad version on its next build? Right now, in more than one place, yes.

## Two claims worth checking — both incorrect as stated

**"Renovate auto-updates dependencies weekly, so our posture is already covered."** Update automation is not pinning. Renovate updates what the pins point at; it doesn't establish that the pins hold between updates, and it says nothing about whether CI actually installs from the lockfile in a mode that fails on drift. This repo's Renovate config existing doesn't change any of the findings below.

**"Packages come from our private registry, so we don't need to worry about a public-registry compromise."** A private registry changes who you trust, not whether the anchor holds. The lockfile still needs content hashes for transitive dependencies, and CI still needs to install in frozen mode — a private registry doesn't provide either of those on its own, and this repo's posture on both is exactly the findings below regardless of where packages come from.

## Finding: Third-party deploy action pinned to a mutable tag

**Location:** `.github/workflows/deploy.yml` — `uses: some-org/deploy-action@v2`
**Category:** Mutable CI workflow reference
**Severity:** High

**Reachability:** If `some-org`'s account or the `v2` tag were compromised, the re-pointed action would run with whatever access this `deploy` job holds — which, given the job's own name and its final `./deploy.sh` step, is real deployment access.

**What's happening:** The action is referenced by a version tag, which the publisher (or anyone who compromises their account) can re-point to different code at any time. The next run of this workflow would pull whatever `v2` currently resolves to, not what it resolved to when this was reviewed.

**Why it matters:** This is exactly the job where a compromised action does the most damage — it's the one with deploy credentials.

**Suggested fix:** Pin to the full commit SHA the action currently resolves to, with a comment noting the version it corresponds to for readability.

## Finding: Container base image pinned to a mutable tag

**Location:** `Dockerfile` — `FROM node:20`
**Category:** Mutable container reference
**Severity:** High

**Reachability:** `node:20` can be re-pointed by its publisher to a different image at any time; this Dockerfile builds whatever that tag currently resolves to and ships it as the deployed service's base.

**What's happening:** The base image is referenced by tag, not digest.

**Why it matters:** A tag-pinned base image for a service that's actually deployed is one of the higher-severity versions of this same underlying problem — the base image is the foundation everything else in the container runs on top of.

**Suggested fix:** Pin `FROM node:20` to the specific digest currently in use (`node:20@sha256:...`), and update the digest deliberately when a new base image version is adopted.

## Finding: Lockfile exists but isn't installed from in frozen mode

**Location:** `.github/workflows/deploy.yml` (`npm install`) and `Dockerfile` (`npm install --production`)
**Category:** Frozen-install gap
**Severity:** High

**Reachability:** Anywhere `package.json`'s version ranges allow a newer transitive dependency to resolve differently than what `package-lock.json` currently records, without anyone changing `package.json` itself.

**What's happening:** `package-lock.json` is committed and current, but neither the CI workflow nor the Dockerfile uses `npm ci` — the command that fails when the lockfile and what would actually resolve disagree. `npm install` can silently update the lockfile and proceed rather than stopping.

**Why it matters:** A lockfile that nothing installs from in frozen mode is decoration — it records what should be trusted, but nothing enforces that a build actually gets that and only that.

**Suggested fix:** Replace `npm install` with `npm ci` in both the workflow and the Dockerfile.

## Finding: Install scripts run with no allowlist

**Location:** `.github/workflows/deploy.yml` (`npm install`) and `Dockerfile` (`npm install --production`)
**Category:** Install-time code execution
**Severity:** Medium

**Reachability:** Any dependency (direct or transitive) that ships a lifecycle script — `preinstall`, `install`, `postinstall` — gets to run arbitrary code during install, before any of this repo's own code runs, with whatever access the install process has (CI runner, or the Docker build context).

**What's happening:** Neither install command disables lifecycle scripts or restricts them to an allowlist of known-necessary packages.

**Why it matters:** This is one of the highest-leverage vectors available to a compromised package, and it's invisible to a review that only checks version pinning — a perfectly pinned, hash-verified dependency can still run arbitrary code at install time if its install script is malicious.

**Suggested fix:** Disable install scripts by default (`npm install --ignore-scripts` in CI and in the Dockerfile) and maintain an explicit allowlist for the small number of packages that genuinely need one, applied narrowly rather than repo-wide.

If nothing else rises above what's listed here, that's because this audit didn't reach further than these four files — a real pass would also check `npm audit`/lockfile hash coverage for the full transitive tree, which requires running a command against the repo rather than reading it.
</content>
