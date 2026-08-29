---
name: pr-issue-writeup
description: Write a PR description or issue write-up for review, or decide whether a piece of work should become a filed issue at all and in which system. Use when a change is ready for review, a ticket needs filing/updating, or a scoped slice/task has no tracking destination yet.
---

# PR and Issue Descriptions

**Trigger:** describing a change for review, or filing/updating a ticket.

**Before writing, if there's no established ticket yet, STOP and ask —
do not produce a finished write-up first.** This is a blocking question,
not a disclaimer to note inline and proceed past:
1. Should this become a tracked issue at all, or just be described inline
   (e.g. in a PR, a commit, or handed straight to the next persona)?
2. If filing, which system — GitHub, Jira, Linear, something else?

Only write the artifact after that's answered. Match its format to that
system's real conventions if you know them. If the answer is "no
preference" or "you decide," *then* fall back to generic (title +
description, no system-specific markup) — generic is the answer you give
once asked, never a substitute for asking. Never hardcode a filing
mechanism (no assuming `gh issue create`, no assuming Jira) — the
mechanics of actually creating the ticket in a given system are
project-specific tooling, not this skill's job. This skill writes the
content; a project-specific plugin or the user does the filing.

- Explain each piece of work in plain language a reviewer can follow without
  cross-referencing anything else.
- Keep ticket/issue IDs out of the narrative — put them on a short trailing
  reference line (e.g. "Tracked under PROJ-123") instead of weaving them
  into sentences.
- If AI materially produced the change, say so accurately and keep it
  current: name the specific model/tool and its role (plan, implement,
  review), not just "AI." Update the note when the tooling or role changes —
  a stale provenance note is a lie by omission.
