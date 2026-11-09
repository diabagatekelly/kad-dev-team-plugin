---
name: delivery
description: Push a finished, reviewed slice branch, open its pull request with a reviewer-ready body, file the leftover findings as tracker issues, collect the external reviewer's comments for triage and act on the verdicts (push the fixes, reply to the declines, file the deferrals). Use at the end of the orchestrator's chunk loop (its step E, which invokes this skill after its own records commit) or when asked to deliver, push or open a pull request for a branch whose work is done; a handoff file that names E as the next action is resumed through the orchestrator, not by invoking this skill. Owns the git and hosting mechanics only; it decides nothing about the code and never pushes to the default branch.
---

# Delivery

**Trigger:** a branch holds finished, committed, reviewed work and needs to
reach the remote, a pull request and the tracker. The orchestrator's chunk
loop invokes this at step E and asks the user nothing: the owner decided on
2026-10-24 that the push and the pull request happen without a question.
Invoked directly ("deliver this", "open the PR"), the same procedure, the
same silence.

**What you are given.** The branch, the base commit it grew from, the
implementation report's path, the records directory (the reviewer and
smoke reports) and the `rounds-slice-<nnn>.jsonl` sidecar, the Definition
of Done results, the tracker `user-story-writeup` recorded for this
project (GitHub, Jira, Linear, something else, or none), and the default
branch to target. If the orchestrator did not give one of these, take it
from the repository (`git rev-parse --abbrev-ref HEAD`, `git remote
get-url origin`, `gh repo view --json defaultBranchRef`), never from a
guess about where things might be.

**Nothing here runs in the background.** Every command is waited for, and
the pull request body carries its issue links before this skill reports:
the second real run filed its issues from a background script, the session
ended, and the body kept its placeholder.

**Everything this skill posts carries the plugin's footer line**, as the
last line of its body: the pull request body, every issue body, every
reply, every issue comment:

```
— kad-dev-team
```

It is the one marker the comment collector (step 5) and the orchestrator's
routing (its step 1b) filter by, so that what the flow posted is never
re-triaged and everything else is, whoever wrote it. Never filter by
author: the owner writes from the same GitHub account the session pushes
as, and their comments are exactly the ones to triage.

## 1. Preconditions, in this order

1. The working tree is clean (`git status --porcelain` is empty). A dirty
   tree is reported and stops this skill: whatever is uncommitted is
   somebody's unfinished work, not yours to commit or discard.
2. The branch is not the default branch. If it is, stop: nothing here goes
   to the default branch except through a pull request someone merges.
3. A remote named `origin` exists. If not, stop and report that the
   repository has no remote; creating one is `repo-bootstrap`'s job, with
   the owner's answers, not something to improvise with a `gh repo create`.
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
returns an answer, not the turn. Hand it the implementation report, the
sidecar and the Definition of Done results, and tell it the body has these
parts, in this order: what was built, one line per chunk with its commit
hash; decided gaps and the mid-build decision commits (`Decision <n>`,
with the persona); escalations and who owns them; a **Definition of Done**
table, one row per check with its result; **Standing**, the Mediums left
standing after the fix rounds, as a list that will carry issue links after
step 4; **Known Lows**, the slice review's Lows grouped by theme (naming,
comments, tests, structure, and so on), each with its file and line, not
filed anywhere; a provenance line naming the models and their roles (the
orchestrator session's model routing, Sonnet implementing and fixing, Opus
reviewing) and this plugin; the trailing reference line the skill uses for
ticket identifiers. Then:

```
gh pr create --base '<default branch>' --head '<branch>' --title '<the slice's title>' --body-file '<the body file>'
```

If a pull request for this branch already exists (`gh pr list --head
<branch>`), update its body with `gh pr edit` instead of opening a second
one. Record the pull request number and URL.

## 4. Issues for what is left standing

Every **standing Medium** (the sidecar's pre-existing Critical, High and
Medium rows that no fix covered, and its `owed` rows, the browser checks a
UI smoke run could not drive; `rounds_record.py --standing` lists both)
becomes one issue, in the tracker the project recorded. **Lows are not
filed**: the second real run turned 585 Lows into 205 issues nobody will
groom; they stay in the pull request body under "Known Lows", where a
human reads them once, and the owner can ask for any of them to be filed.

- **GitHub:** `gh issue create --title '[<Severity>] <the finding's title>'
  --body-file '<body>' --label tech-debt --label 'severity:<level>'`, the
  body being the finding's text, file and line, the reviewer that raised
  it, the pull request number and the footer line. The severity label
  (`severity:critical`, `severity:high`, `severity:medium`) is what the
  orchestrator's routing reads first when it looks for open Critical and
  High issues; the title prefix is its second reading, the quoted
  `**Severity:**` line in the body its third. If a label does not exist,
  create it once with `gh label create`. Run the commands one after
  another in the foreground, waiting for each. The criteria walk's NOT
  REACHABLE rows (`rounds_record.py --standing` lists them as `walk:`)
  and the smoke runs' `owed` rows go into **one** issue, the owner's
  checklist, titled `Owner's checklist: slice <nnn>`, one checkbox per
  row with its reason.
- **Another tracker:** write each issue's title and body to a file next to
  the report (`<report>-issues.md`) and report them; the mechanics of
  filing in Jira, Linear or anything else are project-specific tooling,
  exactly as `user-story-writeup` says, and this skill does not assume
  them.
- **None recorded:** the list stays in the pull request body, and the
  report says no tracker is recorded.

Then, in the same turn, edit the pull request body so each standing
Medium links its issue. One issue per finding, never one issue for all of
them, never a standing Medium dropped because it looks small.

## 5. The external reviewer's comments

Wait for the pull request's checks and reviews to settle: poll
`gh pr checks <number>` every sixty seconds until nothing is pending, for
at most fifteen minutes; then read the reviews, the review comments and
the issue comments (`gh api repos/<owner>/<repo>/pulls/<number>/reviews`,
`.../pulls/<number>/comments` and `.../issues/<number>/comments`). A
review bot that has not posted within the bound is treated as having
nothing to say this round; the report says so. Collect every comment
whose body does not end with the plugin's footer line, whoever wrote it
(the owner's included; never filter by author), that is not resolved
(`gh api graphql` for the review threads' `isResolved`, or the comment's
thread marked resolved) and has no reply of this flow's under it, with
its id, author, path, line (`null` for an issue comment), body and the
commit it was left on, into `<reviews dir>/pr-r<round>-comments.json`,
and return the count and the path. You do not judge the comments: that is
`code-reviewer:external-review-triage`, which the orchestrator launches
with that file.

**Called from the routing** (the orchestrator's step 1b found a slice's
pull request open): the same collection and the same acting on verdicts,
on the pull request as it stands, with the branch checked out; the round
count starts where the pull request's last `pr-r<round>-comments.json`
left off. When the collection is empty and the checks are green, return
`ready to merge` and nothing else: merging is the owner's.

When the orchestrator comes back with the verdicts, act on each:

- **fix:** the orchestrator has had `tdd-coach` apply it and the gate has
  passed; you `git push` the branch. Then reply on the comment, one line,
  naming the fixing commit, the footer line under it.
- **decline:** reply on the comment with the triage's reason, as written,
  the footer line under it, one reply per comment:
  `gh api -X POST repos/<owner>/<repo>/pulls/<number>/comments/<id>/replies -f body='<reason>'`
  (an issue comment gets its reply as a new comment on the pull request,
  quoting the first line of the one it answers).
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
- **Issues** — each one: number, title, from which standing finding; and
  how many Lows stay in the body unfiled.
- **External review** — per round: comments collected, and for each the
  verdict acted on and what was posted or filed.
- **Refused** — anything this skill would not do (a dirty tree, a push to
  the default branch, a force-push, a missing remote) and the one line of
  why.

## What this skill never does

Push to, rebase onto or merge into the default branch; force-push or delete
any remote branch; commit application code or tests; edit the planning
documents or the implementation report (the chunk sections are the loop's;
the issue links go in the pull request body); file a Low; run anything in
the background; print or store a credential; ask the user a question;
write deployment or infrastructure configuration (`ci-pipeline` writes CI,
and deployment is phase 2).
