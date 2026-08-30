---
name: user-story-writeup
description: Write up a scoped slice as a trackable work item — a user story describing what's about to be built, before any code exists — or decide whether it should become a filed issue at all and in which system. Use once a slice has been cut (thin path + acceptance criteria) and needs a tracking destination before implementation starts.
---

# User Story Write-Up

**Trigger:** a slice has been cut — it has a thin path and acceptance
criteria — and now needs to become a trackable unit of not-yet-built work.
This describes work that's *about* to happen, not a change that already
happened; if the work is already done and ready for review, that's
`pr-writeup`, not this.

**Before writing, if there's no established tracking destination yet, STOP
and ask — do not produce a finished write-up first.** This is a blocking
question, not a disclaimer to note inline and proceed past:
1. Should this become a tracked issue at all, or just be handed straight
   to the next persona (e.g. `software-architect`) without filing anywhere?
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

**Write it as a user story**, not a task list: who benefits, what they can
do once this ships, and why — pulled directly from the slice's thin path
and acceptance criteria, not re-derived. A reviewer or implementer should
be able to follow it top to bottom with no cross-referencing back to the
slice write-up.

- Keep ticket/issue IDs out of the narrative — put them on a short trailing
  reference line (e.g. "Tracked under PROJ-123") instead of weaving them
  into sentences.
- Carry the slice's acceptance criteria through faithfully — this isn't
  the place to re-scope, tighten, or loosen what was already decided.
- If AI materially shaped the requirement or the slice this is based on,
  say so accurately and keep it current: name the specific model/tool and
  its role, not just "AI."
