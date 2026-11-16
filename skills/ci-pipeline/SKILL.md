---
name: ci-pipeline
description: Write the continuous-integration configuration a repository is missing, so its pull requests run the same checks the orchestrator's gate runs locally (install with the frozen lockfile, typecheck, lint, the test suite with its coverage gate) on Linux and macOS, hardened (pinned action commits, least-privilege permissions, no secrets); and, for a project with a screen, the screen-change check's own job (a pinned headless Chromium captures every driven state and a script compares it with the committed baselines). Use inside the first delivery that finds no CI in the repository, inside the first delivery of a slice with a screen that finds no screen-change check, or when asked to add CI or a pipeline to a project. Writes CI only; deployment, environments and infrastructure are a separate, later skill.
---

# CI pipeline

**Trigger:** the repository has no continuous-integration configuration
(`.github/workflows/*.yml`, or the equivalent for the host the remote
names) and a pull request is about to be opened; or the user asks for CI.
`technology-bootstrap` defers infrastructure until a slice forces it, and a
pull request with no checks is the first thing that does. Also: the
project has a screen (a screen design under the planning directory's
`visual-ux/`) and no `.github/workflows/screens.yml`; section 3 alone
then, when the repository already has its CI. Not this skill:
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
  `gate-checks.json`, an entry's `cmd` is one of those commands too when
  two things hold: it is a script of the project's manifest, run through
  the runner the project uses (pnpm, npm, yarn or bun; `uv run` or the
  project's own task for Python), and its exit code is its verdict,
  which is an entry with no `count` (the tool keeps its own baseline) or
  a counted one whose `baseline` is 0. A counted entry with a baseline
  above 0 exits non-zero on the violations the owner already accepted,
  and only the gate compares the count: CI would be red on a tree the
  gate passes, so it is listed under "Not run in CI" with its baseline.
  So is an entry whose tool is a binary the manifest does not install,
  which is never installed by a third-party action. Coverage thresholds stay where
  the project enforces them (the test runner's configuration); CI adds
  none of its own.

- **A screen:** list the screen designs, `ls '<planning
  directory>'/visual-ux/screen-*.md` (the planning directory is the one
  the orchestrator named, or the one the project keeps its documents
  in). Any, with no `.github/workflows/screens.yml`: section 3 is owed
  in this run, after section 2, and it is not a judgement call. A
  project with no capture file, no baseline and no route yet is the
  ordinary first state, which section 3 is written for; "nothing to
  capture yet" is never a reason to leave it out, and the report never
  says the screen job was skipped.

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
  `actions/setup-python` and `astral-sh/setup-uv` (and
  `actions/upload-artifact` in the screen job of section 3).
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

## 3. The screen job, for a project with a screen

Whenever section 1 found a screen design and no
`.github/workflows/screens.yml`. One that exists is left alone, like any
workflow. The check: a
real headless browser renders every state the project's capture file
drives, on made-up data, and a script compares each image with the
baseline committed beside the screen designs; a difference in a state
the slice's screen design does not list fails the job. It is its own
workflow file, so no existing workflow is touched. In this order:

1. **Copy the plugin's four files, as they are.** Never write them from
   memory, never edit a copy:

   ```
   mkdir -p screens tools
   cp "${CLAUDE_SKILL_DIR}/screens/capture.mjs" "${CLAUDE_SKILL_DIR}/screens/package.json" "${CLAUDE_SKILL_DIR}/screens/package-lock.json" screens/
   cp "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/screen_check.py" tools/screen_check.py
   ```

   `screens/` is a package of its own: Playwright, exact-pinned with its
   lockfile, is the browser (its Chromium), installed by CI with `npm ci`
   in that folder. The project's manifest and lockfile do not carry it
   and are not edited; nothing is installed here. `capture.mjs` is the
   harness; its header says what `screens/states.mjs`, the project's own
   file, has to export. That file is not yours to write: the report says
   whether it exists. The orchestrator has the states written before
   the push.
2. **The threshold file**, only when absent:
   `<planning directory>/visual-ux/baselines/screen-check.json` holding
   `{"max_changed_percent": 0.1}`. A state differs when more than that
   share of its pixels do, anti-aliasing ignored. The number is the
   owner's: one that is there is never changed, by you or by a fixer.
3. **`.github/workflows/screens.yml`**, one job named `screens`:
   - `on`, `permissions: contents: read`, `concurrency` and
     `timeout-minutes` as in section 2.
   - `runs-on: ubuntu-24.04`: one named image, never `-latest` and no
     matrix. Pixels are compared, and two images, or two systems, render
     the same page differently with no change in the code.
   - Steps: checkout with `fetch-depth: 0` (the comparison reads the
     default branch's screen designs) and `persist-credentials: false`;
     Node set up (the project's version; 24 when the project is not a
     Node one), with the project's own toolchain as in section 2;
     the project installed with its frozen lockfile, since the capture
     starts the built app; then, as separate named steps:

     ```
     - name: Install the pinned browser
       working-directory: screens
       run: npm ci && npx playwright install --with-deps chromium
     - name: Capture every state
       run: node screens/capture.mjs --out screens-out/captures
     - name: Compare with the baselines
       if: always()
       env:
         BASE: ${{ github.base_ref }}
         HEAD_SHA: ${{ github.event.pull_request.head.sha || github.sha }}
       run: python3 -I tools/screen_check.py compare --planning '<planning directory>' --captures screens-out/captures --out screens-out --base "${BASE:+origin/}${BASE:-HEAD}" --head "$HEAD_SHA"
     - name: Keep the captures and the differences
       if: always()
       uses: actions/upload-artifact@<sha> # <tag>
       with:
         name: screens
         path: screens-out
     ```

     The artifact is named `screens` and holds `captures/`, `diff/`,
     `screen-check.txt` and `screen-check.json`: `delivery` downloads it
     by that name.
   - **CI stays read-only.** No step commits, pushes or opens anything,
     and no permission is widened: a baseline is committed by the loop,
     at delivery, from the artifact. Every `uses:` pinned as in section
     2, `actions/upload-artifact` looked up the same way.
4. Validate the YAML as in section 2, then commit by name: `git add
   .github/workflows/screens.yml screens/capture.mjs screens/package.json
   screens/package-lock.json tools/screen_check.py` and the threshold
   file when you wrote it, `git commit -m 'CI: the screen-change check on
   pull requests'`. Never push here.

## 4. Report

- **Written** — the file, the host, the toolchain version and where it came
  from.
- **Runs** — each step and the exact command, that they match the
  gate's, and the two operating systems the checks job runs on.
- **Pinned** — each action, tag and SHA.
- **Not run in CI** — any gate command the workflow could not include and
  why.
- **Screens** — only when section 3 ran: the workflow, the image it runs
  on, the Playwright version `screens/package.json` pins, the threshold
  file (written, or there already with its number), and whether
  `screens/states.mjs` exists yet.
- **Review** — that `devsecops-engineer:operational-readiness` reviews this
  once a deployment path exists; a test-only workflow needs no readiness
  review.

## What this skill never does

Write deployment, environment or infrastructure configuration; add
secrets; touch an existing workflow; push; commit a baseline image or
give a workflow leave to; edit the copies of the plugin's screen files,
or the threshold once it exists; write for a host other than
GitHub (report instead); invent a test, lint or typecheck command the
project does not document. The `flexion-ai-devops-tools:ci-pipeline-setup`
skill, where installed, is a reference for hardening rules, not a
dependency of this one.
