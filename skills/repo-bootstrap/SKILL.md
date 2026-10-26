---
name: repo-bootstrap
description: Give a project that has no git repository, or no remote, the smallest thing the chunk loop needs before it can start — a repository, a default branch, a .gitignore, a private remote and a first push — each decided with the owner, never improvised, and recorded in the technology-bootstrap document. Use when the orchestrator's A step finds no repository or no origin ("flow not started: no repository"), or when asked to create the repository for a project. Writes no application code and no CI (ci-pipeline's); never pushes to a repository that already exists.
---

# Repository bootstrap

**Trigger:** the orchestrator's chunk loop stopped at its A step with
`flow not started: no repository` (the target is not inside a git
repository, or the repository has no `origin`), or the user asks for the
repository to be created. Not this skill: CI (`ci-pipeline`, written inside
the first delivery), deployment (phase 2), branch protection and hosting
settings beyond the private/public choice, or anything about a repository
that already has a remote (a second remote, a rename, a transfer are the
user's, by hand).

The first real run of the chunk loop improvised `git init`, `gh repo
create`, a rename and a push from the orchestrator's own turn, outside any
skill, and the owner had to ask what repository it had just created. This
skill exists so that never happens again: every step below is decided with
the owner before it runs, and the result is written down where the next
slice will read it.

## 1. Read what exists, decide nothing yet

Inline, with Bash, from the project root (the directory holding the
manifest; the orchestrator names it):

- `git rev-parse --show-toplevel`: is there a repository, and is its top
  level the project root or a parent (a project folder inside a larger
  repository is not a missing repository; stop and report that, since
  the slice branch would live in the parent)?
- `git remote get-url origin`: is there a remote?
- `gh auth status`: is a GitHub login available in this session? Without
  one, this skill can create the local repository and stop before the
  remote; it never asks for or stores a credential.
- The technology-bootstrap document in the target directory, if one
  exists: it may already record a hosting decision.
- `.gitignore`: present or not; the stack from the manifest decides what
  it must cover.

## 2. Four decisions, each one `AskUserQuestion`

One question per call, in this order, with a recommendation first and the
alternatives named; skip a question the user's message already answered
in so many words:

1. **Create a repository here?** Recommended: yes, at the project root.
   Alternative: the user names an existing repository to use instead, and
   this skill stops (adding a remote to someone's existing clone is a
   by-hand step).
2. **Default branch name.** Recommended: `main`. Alternative: whatever the
   user's other repositories use.
3. **Remote.** Recommended: a private GitHub repository named after the
   project folder, under the account `gh auth status` shows, created
   with `gh repo create`. Alternatives: public; a different name; no
   remote yet (then the loop cannot deliver, and the A step will stop
   again at E; say so).
4. **What `.gitignore` covers.** Recommended: the stack's generated
   output (`node_modules/`, `dist/`, `.wrangler/`, `__pycache__/`,
   `.venv/` and the like, from the manifest), local secrets (`.env`,
   `.dev.vars`, `*.local`), local databases and logs. The user may add
   patterns; nothing is removed from a `.gitignore` that already exists.

## 3. Do exactly what was decided

In this order, each command's output read before the next:

1. `git init -b <default branch>` when there is no repository (never
   `git init` inside an existing one).
2. Write or extend `.gitignore` with the `Write`/`Edit` tool.
3. `git add` the planning documents and the `.gitignore` by name (never
   `-A`), `git commit -m 'Repository: bootstrap'`.
4. `gh repo create <owner>/<name> --private --source . --remote origin
   --push` (or `--public` when decided), when a remote was decided and
   `gh` is logged in. On any failure report the command's output verbatim
   and stop; never retry with other credentials, never create the
   repository through a browser flow.
5. `git remote get-url origin` and `git log --oneline -1` to confirm.

## 4. Record it

Append to the technology-bootstrap document in the target directory (or
create `technology-bootstrap.md` there with only this section when none
exists) a section `## Repository` with: the date, the default branch, the
remote URL and its visibility, what `.gitignore` covers, and each decision's
alternatives and who chose. This is the document the next slice's
orchestrator reads before it assumes a remote exists.

## 5. Report

- **Repository** — created at which path, or found, with the default
  branch.
- **Remote** — the URL and visibility, the first pushed commit, or that
  none was created and why.
- **Ignored** — the `.gitignore` patterns added.
- **Recorded** — the technology-bootstrap section's path.
- **Refused** — anything this skill would not do (a repository already
  present, no `gh` login, a parent repository) and the one line of why.

Then the orchestrator re-inspects; its A step runs again from the start.

## What this skill never does

Push to a remote that already existed; add a second remote; rename or
transfer a repository; set branch protection or hosting settings beyond
the visibility; write CI, deployment or infrastructure; commit application
code; store, print or pass along a credential; decide any of the four
questions without asking.
