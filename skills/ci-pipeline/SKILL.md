---
name: ci-pipeline
description: Write the continuous-integration configuration a repository is missing, so its pull requests run the same checks the orchestrator's gate runs locally (install with the frozen lockfile, typecheck, lint, the test suite with its coverage gate) on Linux and macOS, hardened (pinned action commits, least-privilege permissions, no secrets). Use inside the first delivery that finds no CI in the repository, or when asked to add CI or a pipeline to a project. Writes CI only; deployment, environments and infrastructure are a separate, later skill.
---

# CI pipeline

**Trigger:** the repository has no continuous-integration configuration
(`.github/workflows/*.yml`, or the equivalent for the host the remote
names) and a pull request is about to be opened; or the user asks for CI.
`technology-bootstrap` defers infrastructure until a slice forces it, and a
pull request with no checks is the first thing that does. Not this skill:
deployment, environments, secrets, release jobs, or a change to a workflow
that already exists (report what the gate runs that CI does not; the
change is the user's to ask for).

## 1. Read the project, decide nothing

- **Host:** `git remote get-url origin`. `github.com` means GitHub Actions
  and the rest of this skill. Any other host: stop and report that only
  GitHub Actions is written today; the delivery proceeds without CI and
  says so.
- **Stack and commands**, from the project's own manifest, the same way
  the gate finds them: `package.json` scripts named `test`, `typecheck` (or
  `tsc` in a script), `lint`; the package manager from `packageManager` or
  the lockfile present (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`,
  `bun.lock`); the Node version from `.nvmrc`, `.node-version` or
  `engines.node`, else the major version the gate ran under (`node
  --version`). A Python project: `pyproject.toml` with `uv.lock` or
  `poetry.lock`, the test command from its scripts or `pytest`. Anything
  else: stop and report what was found; don't invent a build.
- **What the gate runs** is in the orchestrator's log and the project's
  documented test command; CI runs exactly those commands, so a local green
  and a remote green mean the same thing. When the project root has a
  `gate-checks.json`, each entry's `cmd` that is a manifest script (`pnpm
  run <name>`, `npm run <name>`) is one of those commands too, with the
  baseline the file or the tool holds; an entry whose tool is a binary
  the manifest does not install is listed under "Not run in CI" in the
  report, never installed by a third-party action. Coverage thresholds stay where
  the project enforces them (the test runner's configuration); CI adds
  none of its own.

## 2. Write one workflow

`.github/workflows/ci.yml`, and nothing else:

- `on: pull_request` and `push` to the default branch only.
- `permissions: contents: read` at the top; no job widens it.
- `concurrency` keyed on the ref, `cancel-in-progress: true`.
- One `checks` job on **two operating systems**, `strategy.matrix.os:
  [ubuntu-latest, macos-latest]` with `runs-on: ${{ matrix.os }}` and
  `fail-fast: false`: the gate runs on one machine, and a defect only
  the other system shows (a path's case, a rename over an open file, a
  signal, a line ending) reaches the pull request red with nothing local
  to explain it (incident 33). Both always; never one "to save minutes",
  and never a third unless the project's manifest says it supports it.
  Its steps: checkout, toolchain setup with the
  version from step 1, the package manager enabled (`corepack enable` for
  pnpm or yarn), install with the frozen lockfile (`pnpm install
  --frozen-lockfile`, `npm ci`, `yarn install --immutable`, `uv sync
  --frozen`), then typecheck, lint, the gate checks that are manifest
  scripts, and test as separate named steps in that order, each only if
  the project has the script. A step the project has
  no command for is left out, not stubbed.
- One `audit` job on `ubuntu-latest` alone (an advisory does not depend
  on the system), same setup, running the package manager's audit at high
  severity (`pnpm audit --audit-level=high`, `npm audit --audit-level=high`,
  `pip-audit` where available). It fails the run; a project that wants it
  advisory changes that itself.
- Every `uses:` pinned to a full commit SHA with the tag as a trailing
  comment (`uses: actions/checkout@<sha> # v4`). Resolve each SHA at write
  time with `gh api repos/<owner>/<action>/git/ref/tags/<tag>` (follow an
  annotated tag to its commit); never copy a SHA from memory. No
  third-party actions beyond `actions/checkout`, `actions/setup-node`,
  `actions/setup-python` and `astral-sh/setup-uv`.
- No secrets, no `secrets.*`, no deploy step, no matrix of runtime
  versions unless the project already supports more than one in its
  manifest (the operating-system matrix above is the only other one), no
  caching of anything but the package manager's store through the setup
  action's built-in cache option.
- Timeouts on every job (`timeout-minutes`, fifteen unless the suite's
  documented runtime says otherwise).

Then validate the YAML parses (`python3 -c "import yaml, sys;
yaml.safe_load(open(sys.argv[1]))" .github/workflows/ci.yml`, or the
equivalent available). Then the README's CI line, when a README exists:
replace its `No CI runs these yet.` sentence (the one `readme` writes
under "Tests and checks") with `CI: see .github/workflows/ci.yml`, or add
that line under its tests section when the sentence is not there, with
the `Edit` tool. Commit by name, the README only when it changed:
`git add .github/workflows/ci.yml README.md && git commit -m 'CI: test,
typecheck and coverage on pull requests'` (without `README.md` in the
`git add` when there is none; `readme` writes the CI line itself later,
and the report says the README was not there). Never push here;
`delivery` pushes.

## 3. Report

- **Written** — the file, the host, the toolchain version and where it came
  from.
- **Runs** — each step and the exact command, that they match the
  gate's, and the two operating systems the checks job runs on.
- **Pinned** — each action, tag and SHA.
- **Not run in CI** — any gate command the workflow could not include and
  why.
- **Review** — that `devsecops-engineer:operational-readiness` reviews this
  once a deployment path exists; a test-only workflow needs no readiness
  review.

## What this skill never does

Write deployment, environment or infrastructure configuration; add
secrets; touch an existing workflow; push; write for a host other than
GitHub (report instead); invent a test, lint or typecheck command the
project does not document. The `flexion-ai-devops-tools:ci-pipeline-setup`
skill, where installed, is a reference for hardening rules, not a
dependency of this one.
