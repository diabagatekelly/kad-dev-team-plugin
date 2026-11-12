---
name: readme
description: Write or complete the project's README.md from the manifest, the design document and the slice, so a stranger gets from clone to a running app, the tests and the checks without asking anyone — the chunk loop's Definition of Done needs it at its D step, and the smoke agent follows it on a clean clone. Use when the Definition of Done's README check fails, or when asked for a README. Never invents a command the manifest does not have.
---

# README

**Trigger:** the orchestrator's Definition of Done check at its D step
reports the README missing or incomplete, or the user asks for a README.
Both real runs of the chunk loop delivered a working slice with no README
at all, and the independent assessors named writing one as the first thing
a human would do. This skill writes it from what the project already
states, and nothing else.

## Sources, and the one rule

Read, in this order: the project's manifest (`package.json`,
`pyproject.toml`, `go.mod`, the lockfile and the package manager it
implies, `.node-version`/`.nvmrc`/`engines`), the deployment or runtime
configuration (`wrangler.toml`, `.env.example`, `.dev.vars.example`), the
design document and the slice file the orchestrator names by path, the
technology-bootstrap document, and the existing `README.md` if any.

**Never invent a command.** Every command on the page is one the manifest
declares (`scripts` in `package.json`, a `Makefile` target, a documented
runner), copied exactly, with the package manager the project pins. A
step the project has no command for is written as what is missing ("there
is no lint script yet"), never as a plausible command. Run each command
you write once, from the project root, and keep only the ones that work;
a command you could not run (it needs an account you don't have) says so
beside it.

## The sections, in this order

1. **What it is** — the top heading is the project's name; the first
   paragraph says what the app does today, in the problem's own words
   (from the slice and the design), two sentences at most.
2. **Prerequisites** — the runtime and its version, the package manager
   and how it is obtained (`corepack enable`, say), and every external
   account the slice needs (a provider's sandbox account, a cloud login)
   with where its secrets go (the exact file or variable the configuration
   reads, from `.env.example`/`.dev.vars.example`), never the values.
3. **Clone to running** — numbered commands, from `git clone` to the app
   answering, including the migration or seed step when one exists and
   the address the app answers on. A stranger with the prerequisites runs
   these and nothing else.
4. **Tests and checks** — the test command, the typecheck, the lint and
   the format check, each as the manifest names it; then one line on CI:
   `CI: see .github/workflows/<file>` (or the host's equivalent) when a
   workflow file exists, else exactly `No CI runs these yet.`, the
   sentence `ci-pipeline` replaces when it adds one. Never write "no CI"
   when a workflow is there (a README said it one commit after CI
   landed, incident 26).
5. **Where things live** — where the data is stored locally, where the
   logs go, which files hold local secrets and are ignored by git.
6. **What this slice does and does not** — the slice's behaviour in a few
   bullets, then what is explicitly not in it yet (from the slice's
   non-goals and "kept for later slices"), so nobody reports a missing
   feature as a bug.

Write for skimming: lead with the point, headers and numbered steps over
prose, a paragraph one or two sentences. Nothing about the plugin, the
chunk loop, the planning documents or the reviewers: a README is for the
person running the app, not for the process that built it.

## Writing it

Write `README.md` at the project root with the `Write` tool (or `Edit` an
existing one section by section, keeping what is still true and deleting
what is not; never append a second copy of a section). Then commit it by
name: `git add README.md && git commit -m 'README: clone to running,
tests, scope'`. Never push.

## Report

- **Written** — the path, created or updated, and which sections changed.
- **Commands verified** — each command on the page and that it ran, or
  why it could not be run here.
- **Missing in the project** — anything the sections needed that the
  manifest does not provide (no lint script, no format check), as facts
  for the Definition of Done, not as commands you added.

## What this skill never does

Invent a command, a version or an account the project does not state; add
a script to the manifest (that is a fixer's named fix); describe the
plugin's process; write anything but `README.md`; push.
