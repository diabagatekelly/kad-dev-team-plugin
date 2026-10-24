---
name: audit-review
description: Review real sessions recorded in kad-dev-team's audit mode (KAD_AUDIT=1) to find where a persona or skill didn't do what its SKILL.md says, and turn each real miss into a proposed fix and an eval case. Use when asked to review audit logs, check how the plugin behaved in real use, or find what needs fine-tuning.
---

# Audit review

Audit mode (`hooks/audit.sh`, on when `KAD_AUDIT=1`) logs prompts and every
`kad-dev-team` skill and agent call per session, and keeps the transcript of
any session that used the plugin, under `$KAD_AUDIT_DIR` (default
`~/.claude/kad-audit`). This skill reads those records against the skills'
own rules. It proposes; it changes no skill and commits nothing without the
user's say-so.

## 1. Pick the sessions

Run `python3 -I evals/tools/audit_report.py --since <last review>` (the date
is in `$KAD_AUDIT_DIR/last-review` if a previous review wrote one). Read
every session with flags first, then a sample of the unflagged ones: a
session with no pushback can still be one where the skill quietly did the
wrong thing and the user fixed it later by hand.

## 2. Read each one against the rules that applied

Judge each session by the plugin version that ran it, not the current
one. The transcript names it: every Skill result begins with `Base
directory for this skill: .../kad-dev-team/<version>/skills/<name>`, and
a session that spans a `/reload-plugins` can carry two versions. `git log
-S'"version": "<version>"' -- .claude-plugin/plugin.json` names that
version's bump commit, and `git show <commit>:skills/<name>/SKILL.md`
gives that version's rules. The install record's `gitCommitSha` in
`~/.claude/plugins/installed_plugins.json` is the version installed now,
which is only the one that ran if nothing was updated since. A miss that
version made and the current one already fixes is a finding to record,
not a fix to propose.

For each `kad-dev-team` call in a session, read the skill's
`skills/<name>/SKILL.md` at that version, then the transcript from that
call to the next user prompt (subagent transcripts are in
`transcripts/<session>/`). If the project has an `orchestrator-log.md`,
run `python3 -I evals/tools/orchestrator_log_check.py <project dir>`
(with `--skill` pointing at that version's orchestrator SKILL.md, saved
to a scratch file). It checks the log's format, its route order against
the state table, append-only from git and the transcripts, every entry
against the skill call that followed it, and which files each stage
actually wrote. Its errors are leads to read in the transcript, not
findings yet. Ask of each call:

- Should it have fired here, and did anything fire that shouldn't have?
- Did it ask when its skill says to ask, and not ask what the documents
  already answered?
- Did it stay inside its mandate, hand back what isn't its call, and leave
  other stages' documents alone?
- Did it save where it was told, and report what its output format says?
- Did the user correct it, redo its work, or undo a file it wrote? The
  correction is usually the clearest statement of what should have
  happened.

Sort each finding into one of:
- **Skill gap:** no rule covers it, or the rule is unclear. Propose the
  wording.
- **Rule ignored:** the rule is there and wasn't followed. Note whether the
  eval suite already covers it; a miss the suite passes means the cases
  need a harder variant.
- **Preference:** the user wanted something the plugin doesn't encode.
  Ask the user before turning it into a rule.
- **Fine:** behaved as written; the user's change was their own call.

## 3. Turn a real miss into an eval case

Every confirmed miss should end as a case, so it can't come back unseen.

- **Never commit a real transcript or real project content.** Sessions
  come from the user's other projects. Rebuild the situation on the
  `evals/fixtures/library-app/` fixture (or a new overlay beside the
  existing `*-plants/`), with the same shape of request and the same trap.
  Only reuse the real transcript itself if the user explicitly says it may
  go into this repo.
- For a miss partway through an interactive skill, write the earlier turns
  as a phase-1 case on the fixture, freeze it with
  `evals/tools/freeze-history.sh`, and grade the turn that went wrong as
  the next phase (see `evals/README.md`, "Interactive skills").
- Follow the playbook in `evals/README.md`: calibrate with and without
  the plugin, and record the case's bar with
  `evals/tools/record_thresholds.py` once the result is accepted.

## 4. Report

Write the review to `$KAD_AUDIT_DIR/reviews/<date>.md`: sessions read,
findings by category with the transcript lines that show them, the
proposed skill wording, and the proposed cases. Then summarise it for the
user and ask which fixes and cases to make. Once the user has seen it,
write today's date to `$KAD_AUDIT_DIR/last-review`.
