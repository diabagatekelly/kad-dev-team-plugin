---
name: delivery
description: Push a finished, reviewed slice branch, open its pull request with a reviewer-ready body, file the leftover findings as tracker issues, collect the external reviewer's comments for triage and act on the verdicts (push the fixes, reply to the declines, file the deferrals). Use at the end of the orchestrator's chunk loop (its step E) or when asked to deliver, push or open a pull request for a branch whose work is done. Owns the git and hosting mechanics only; it decides nothing about the code and never pushes to the default branch.
---

# Delivery

**Trigger:** a branch holds finished, committed, reviewed work and needs to
reach the remote, a pull request and the tracker. The orchestrator's chunk
loop invokes this at step E and asks the user nothing: the owner decided on
2026-10-24 that the push and the pull request happen without a question.
Invoked directly ("deliver this", "open the PR"), the same procedure, the
same silence.

**What you are given.** The branch, the base commit it grew from, the
implementation report's path, the directory of reviewer reports and the
`rounds-slice-<nnn>.jsonl` sidecar, the tracker `user-story-writeup`
recorded for this project (GitHub, Jira, Linear, something else, or none),
and the default branch to target. If the orchestrator did not give one of
these, take it from the repository (`git rev-parse --abbrev-ref HEAD`,
`git remote get-url origin`, `gh repo view --json defaultBranchRef`), never
from a guess about where things might be.

## 1. Preconditions, in this order

1. The working tree is clean (`git status --porcelain` is empty). A dirty
   tree is reported and stops this skill: whatever is uncommitted is
   somebody's unfinished work, not yours to commit or discard.
2. The branch is not the default branch. If it is, stop: nothing here goes
   to the default branch except through a pull request someone merges.
3. A remote named `origin` exists. If not, stop and report that the
   repository has no remote; creating one is `repo-bootstrap`'s job (phase
   2), not something to improvise with a `gh repo create`.
4. The suite is green: the last gate run in the orchestrator's log says so,
   or, invoked directly, run the project's documented test command once and
   read the result. Never deliver a red branch.

## 2. Push

`git push -u origin <branch>`. On any failure (authentication, network,
rejected non-fast-forward) report the command's output verbatim and stop.
Never force-push, never `--force-with-lease`, never retry with other
credentials, never rebase to make it fit. A rejected push means someone
else moved the branch; that is the user's to look at.

## 3. The pull request

Invoke `kad-dev-team:pr-writeup` with the `Skill` tool for the body; it
returns an answer, not the turn. Hand it the implementation report and tell
it the body has these parts, in this order: what was built, one line per
chunk with its commit hash; decided gaps; escalations and who owns them;
the Lows and standing Mediums left, as a list that will carry issue links
after step 4; a provenance line naming the models and their roles (the
orchestrator session's model routing, Sonnet implementing and fixing, Opus
reviewing) and this plugin; the trailing reference line the skill uses for
ticket identifiers. Then:

```
gh pr create --base '<default branch>' --head '<branch>' --title '<the slice's title>' --body-file '<the body file>'
```

If a pull request for this branch already exists (`gh pr list --head
<branch>`), update its body with `gh pr edit` instead of opening a second
one. Record the pull request number and URL.

## 4. Issues for what is left

Every Low in the report's `### Lows` list and every Medium the log marks
standing after the cap becomes one issue, in the tracker the project
recorded:

- **GitHub:** `gh issue create --title '<the finding's title>' --body-file
  '<body>' --label tech-debt`, the body being the finding's text, file and
  line, the reviewer that raised it, and the pull request number. If the
  `tech-debt` label does not exist, create it once with `gh label create`.
- **Another tracker:** write each issue's title and body to a file next to
  the report (`<report>-issues.md`) and report them; the mechanics of
  filing in Jira, Linear or anything else are project-specific tooling,
  exactly as `user-story-writeup` says, and this skill does not assume
  them.
- **None recorded:** the list stays in the pull request body, and the
  report says no tracker is recorded.

Then edit the pull request body so each listed finding links its issue.
One issue per finding, never one issue for all of them, never a finding
dropped because it looks small.

## 5. The external reviewer's comments

Wait for the pull request's checks and reviews to settle: poll
`gh pr checks <number>` every sixty seconds until nothing is pending, for
at most fifteen minutes; then read the reviews and the review comments
(`gh api repos/<owner>/<repo>/pulls/<number>/reviews` and
`.../pulls/<number>/comments`). A review bot that has not posted within
the bound is treated as having nothing to say this round; the report says
so. Collect every comment not written by the account this session pushes
as, with its id, author, path, line, body and the commit it was left on,
into `<reviews dir>/pr-r<round>-comments.json`, and return the count and
the path. You do not judge the comments: that is
`code-reviewer:external-review-triage`, which the orchestrator launches
with that file.

When the orchestrator comes back with the verdicts, act on each:

- **fix:** the orchestrator has had `tdd-coach` apply it and the gate has
  passed; you `git push` the branch. Then reply on the comment, one line,
  naming the fixing commit.
- **decline:** reply on the comment with the triage's reason, as written,
  one reply per comment:
  `gh api -X POST repos/<owner>/<repo>/pulls/<number>/comments/<id>/replies -f body='<reason>'`.
- **defer:** file it as an issue exactly as in step 4, and reply on the
  comment with the issue number.
- **resolved:** (the comment no longer applies to the code as it stands)
  reply with the commit that made it moot.

A push brings the reviewer back; the next round's comments are collected
the same way. The orchestrator holds the round count and the cap (five);
you collect and act, round by round, until it says the stage is done.

## 6. Report

State, in this shape:

- **Pushed** — the branch and the commit hash.
- **Pull request** — number and URL; whether it was created or updated.
- **CI** — present already, or added by `ci-pipeline` in this delivery
  (its commit), or none and why.
- **Issues** — each one: number, title, from which finding.
- **External review** — per round: comments collected, and for each the
  verdict acted on and what was posted or filed.
- **Refused** — anything this skill would not do (a dirty tree, a push to
  the default branch, a force-push, a missing remote) and the one line of
  why.

## What this skill never does

Push to, rebase onto or merge into the default branch; force-push or delete
any remote branch; commit application code or tests; edit the planning
documents or the implementation report (the Lows list and the chunk
sections are the loop's; the issue links go in the pull request body);
print or store a credential; ask the user a question; write deployment or
infrastructure configuration (`ci-pipeline` writes CI, and deployment is
phase 2).
