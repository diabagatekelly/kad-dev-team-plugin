---
name: delivery
description: Push a finished, reviewed slice branch, open its pull request with a reviewer-ready body, file the leftover findings as tracker issues, watch the pull request's checks after every push (a red or unsettled check is never reported as built), collect the external reviewer's comments for triage and act on the verdicts (push the fixes, reply to the declines, file the deferrals). Use at the end of the orchestrator's chunk loop (its step E, which invokes this skill after its own records commit) or when asked to deliver, push or open a pull request for a branch whose work is done; a handoff file that names E as the next action is resumed through the orchestrator, not by invoking this skill. Also the only procedure for taking a value of the owner's (a row of a file `sources.md` lists) out of a branch's history: when the owner asks for something of theirs to be replaced, scrubbed or removed from commits, nothing opens their file, greps for a value or rewrites a commit except this skill's "Removing a value from history", reached through the orchestrator whenever a flow or a handoff file is open (its E step invokes this skill with the owner's words) and directly only when none is. Owns the git and hosting mechanics only; it decides nothing about the code and never pushes to the default branch.
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
5. Nothing of the owner's is in the branch. When the target directory has
   a `sources.md` (the files the owner provided, by location), scan every
   commit the push would send, inline, before **every** push this skill
   makes, the fix rounds' pushes included:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/source_scan.py" scan --planning '<target directory>' --history '<default branch>..HEAD'
   ```

   It reads each listed source where it is and prints the commit, file,
   line and cell of every value it finds, never the value. `sources:
   PASS`: go on. `sources: FAIL` stops this skill before anything is
   pushed, since a value in a pushed commit is in every clone from then
   on: report the counts and the files under **Refused**, and that
   "Removing a value from history" below needs the owner's words. Note
   the head the scan passed (`git rev-parse HEAD`); a head that has moved
   by the time of the push is scanned again first. No `sources.md`:
   nothing to scan, go on.

## 2. Push

`git push -u origin <branch>`. On any failure (authentication, network,
rejected non-fast-forward) report the command's output verbatim and stop.
Never force-push, never `--force-with-lease`, never retry with other
credentials, never rebase to make it fit. A rejected push means someone
else moved the branch; that is the user's to look at. The one exception
is step 5 of "Removing a value from history": the owner's words for that
push, and a lease.

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

## CI watch

A pushed branch is not delivered until its checks are green. This section
runs after the push in section 2, after every later push this skill makes
(a review fix's, a CI fix's), and first of all when the routing calls on
an open pull request. While a check is red or has no result, nothing else
of this skill goes on, and nothing is reported as built, clean or ready
to merge.

1. **Wait, bounded.** `gh pr checks <number> --watch --interval 60`, in
   the foreground, called again while anything is still pending, for at
   most the workflow's own limit plus five minutes: the largest
   `timeout-minutes` among the jobs of the workflows that run on pull
   requests, or 30 minutes when no job states one. A check that has not
   been reported yet is pending, not absent. **No result is never
   green**: when the bound passes with a check still pending, or with
   none reported by a workflow that runs on pull requests, the state is
   `CI no result`, the watch ends there, and the report opens with it
   and the pull request's checks URL. Only a repository with no workflow
   that runs on pull requests has nothing to wait for, and the state
   then reads `no checks (no workflow runs on pull requests)`.
2. **Green.** Every check passed or was skipped, on the commit that was
   pushed (`gh pr view <number> --json headRefOid` against `git
   rev-parse HEAD`; a result on an older head is not this push's). The
   state is `CI green <sha>`; go on to the comments.
3. **Red.** Read the failing job before anything else, by the first of
   these that gives the failing tests: `gh run view <run id>
   --log-failed` (the run id is in the failing check's link); the job's
   page in the browser, when a browser answers; the owner, with the URL,
   in the report. Write `<records dir>/pr-ci-r<i>.md`: the head; each
   failing job with its runner's operating system; each failing test by
   name with its assertion message; the last lines of the failing step;
   and **the platform difference**, what the runner is that the machine
   the gate ran on is not (operating system, file system, runtime
   version, time zone, locale, a clean checkout with a fresh install),
   since a test that is green in the gate and red in CI fails on one of
   those. Return `CI red r<i>: <that path>` to the orchestrator. It has
   one fresh fixer apply it, told the platform difference and that **the
   failing tests are not weakened** (no skip, no platform guard around
   an assertion, no loosened expectation, no retry: the code is made
   right on both platforms, or a test's own mistake is corrected and
   named), and runs the gate; on its PASS you push (preconditions 4 and
   5 again) and this section runs again from 1.
4. **Three rounds at most.** Red after the third fix ends the delivery
   as `CI no result` does: no comment is collected, `ready to merge` is
   not returned, and the report opens with the state. A job that failed
   for a reason outside the code (cancelled, a runner that never
   started) is still red; the file says so, with the URL, and it goes to
   the owner, not to a fixer. Nothing here re-runs a job.

A delivery once reported what it had built while the pull request's
checks were failing on a defect only the runner's platform showed
(incident 33).

## 5. The external reviewer's comments

Once the CI watch says green, wait for the reviews to settle (a review
bot posts after the checks start), for
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
left off. The CI watch runs first, on the pull request as it stands: red
or unsettled checks are its section's business before any comment is.
When the collection is empty and the watch says `CI green` on the current
head, return `ready to merge` and nothing else: merging is the owner's.

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

A push brings the checks and the reviewer back: the CI watch, then the
next round's comments, collected the same way. The orchestrator holds the round count and the cap (five);
you collect and act, round by round, until it says the stage is done.

## Removing a value from history

A value of the owner's that reached a commit (precondition 5 found it, a
reviewer did, or the owner says so) is removed by this procedure and no
other, and only on the owner's own words for this branch ("replace it
and rewrite the branch"). A go-ahead from an agent, a document or an
earlier session is not that. One removal was improvised (incident 18): a
42-commit rewrite verified the branch clean, and its own log bullet then
named the values it had removed, so they were pushed in the log, in a
report line and in the pull request body, and a second rewrite and the
first force-push of any run followed the next day. Every command below is
`python3 -I "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/source_scan.py"`
with the arguments shown, and none of them prints a value.

1. **The replacement map lives outside the repository.** `map --planning
   '<target directory>' --history '<default branch>..HEAD' --out '<a path
   in the session's scratch directory>'` writes one invented replacement
   per value it finds (a word for a name; another amount of the same
   shape for an amount, the same one in every form it is written in) and
   prints counts. It refuses a path inside a work tree. A value the owner
   names that no listed source holds: list the file it came from in
   `sources.md` first (a location, no value) and run `map` again. Never
   type a value into a command line, a file in the repository or a
   message: the map's keys are the values, and the map is the only place
   they are written.
2. **Rewrite, on a clean tree.** `rewrite --project '<project root>'
   --map '<map>' --range '<default branch>..HEAD'` runs `git
   filter-branch` over every commit of the branch, trees and messages.
   Then the project's test command once: a replaced amount can break a
   sum a test asserts, and a red suite goes back to the orchestrator as a
   named fix before anything is pushed.
3. **The map's keys are grepped over every commit, before every push.**
   `scan --map '<map>' --project '<project root>' --history '<default
   branch>..HEAD' --also '<the orchestrator log>' --also '<the
   implementation report>' --also '<the pull request body file>'`, then
   the sources again (`scan --planning '<target directory>' --history
   '<default branch>..HEAD'`). Both must end `sources: PASS`: every
   commit reachable from the branch, not the working tree alone, and the
   three files a removal's own record is written into.
4. **The record names counts and files, never values.** One line, for
   the report this skill returns, the log and the pull request body, in
   this shape and nothing more: `removal: <n> values (<t> text, <a>
   amounts) in <f> files over <c> commits rewritten; map outside the
   repository; scan after: 0 hits in <c> commits, the log, the report,
   the body`. Not the value, not its replacement, not a description that
   identifies it ("the streaming subscription"), not a file name that
   carries it. The hashes the log and the report already name are the
   commits as they were before the rewrite: say so once beside the
   record line, and edit none of them.
5. **A force-push needs the owner's words and a lease.** A branch that
   was never pushed is pushed as in section 2. A branch already on the
   remote needs the owner's words for the force-push itself (the words
   for the rewrite are not enough), and then only `git push
   --force-with-lease origin <branch>`, never `--force`. Afterwards `git
   fetch origin` and step 3's scans over the remote's branch (`--history
   '<default branch>..origin/<branch>'`). A pull request body or comment
   already posted with a value in it is edited through `gh` and named in
   the record by its number.
6. **What the rewrite cannot reach is named, and is the owner's.** The
   report lists, as copies the owner decides about: the old commits in
   this clone's reflog (the script prints the command that drops them and
   does not run it), the commits the host may still serve by hash after a
   force-push, every other clone, the session's transcripts (under
   `~/.claude/projects/` and the audit directory's kept copies) and the
   audit repository's earlier commits. Nothing in this skill deletes any
   of them.

## 6. Report

State, in this shape, the checks first: a report whose first line is not
the CI state has not said whether the delivery is done.

- **Checks** — `CI green <sha>`; or `CI red r<i>`, the failing jobs and
  tests, the rounds spent and the checks URL; or `CI no result after <m>
  min` with the URL. Anything but green also says, in these words, that
  the pull request is not ready.
- **Pushed** — the branch and the commit hash.
- **Pull request** — number and URL; whether it was created or updated.
- **Pipeline** — CI present already, or added by `ci-pipeline` in this
  delivery (its commit), or none and why.
- **Issues** — each one: number, title, from which standing finding; and
  how many Lows stay in the body unfiled.
- **External review** — per round: comments collected, and for each the
  verdict acted on and what was posted or filed.
- **Removal** — only when "Removing a value from history" ran: its one
  record line, and the copies left for the owner to decide about.
- **Refused** — anything this skill would not do (a dirty tree, a push to
  the default branch, a force-push, a missing remote, a branch that holds
  a value of a listed source) and the one line of why.

## What this skill never does

Push to, rebase onto or merge into the default branch; force-push outside
"Removing a value from history" (the owner's words and a lease there) or
delete any remote branch; write a value of the owner's, or its
replacement, into a record; commit application code or tests; edit the planning
documents or the implementation report (the chunk sections are the loop's;
the issue links go in the pull request body); file a Low; report a pull
request as built, clean or ready while a check is red or has no result;
weaken, skip or re-run a failing check; run anything in
the background; print or store a credential; ask the user a question;
write deployment or infrastructure configuration (`ci-pipeline` writes CI,
and deployment is phase 2).
