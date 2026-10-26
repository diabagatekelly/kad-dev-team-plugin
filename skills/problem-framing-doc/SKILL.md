---
name: problem-framing-doc
description: Write a one-page problem framing doc — the earliest documentation artifact in a project's life, capturing a real problem before any issue, slice, or code exists. Use when a problem exists but nothing has been scoped yet, and you need something stable for later slicing/architecture work to refer back to.
---

# Problem Framing Doc

**Trigger:** a real problem exists, but there is no issue, no slice, and no
code yet. This is the earliest artifact in a project's life — its job is to
pin down the problem crisply enough that later slicing and architecture work
have a stable thing to refer back to, without yet committing to *how* it will
be solved.

A problem framing doc is not a spec and not an ADR — no solution or decision
belongs in it. If you catch yourself designing, stop and move that content to
an ADR once the decision is actually made.

**Gathering the problem.** Ask through `AskUserQuestion` for every
template section the conversation hasn't answered (the problem, why now,
the constraints, what's still open), one question per call, waiting for
each answer before the next; a stated problem with no stated reason or
limits still gets the other questions. Never a numbered list of questions
as text, and never a section inferred from the folder name, the
repository or what a similar product usually does. When the tool isn't
available, ask one question in plain text and end your turn there.

**Template:**

```markdown
# Problem: <short name>

## The problem
What's actually costing time/money/sanity today, in concrete terms. Name the
current process, not the desired future one.

## Why now
What makes this worth solving instead of leaving alone.

## Constraints
Hard limits on the solution space, stated as constraints, not designs —
e.g. "must stay free-tier" is a constraint; "use library X" is a design
decision and doesn't belong here yet. Only what the user stated or the
situation makes binding; a limit you're assuming is an open question, never
both.

## Open questions
Things that must be answered before a first slice can be cut. It's fine —
expected, even — for this section to be non-empty.
```

**No dedicated Non-goals section.** What a problem doesn't cover is almost
always already implied by what "The problem" says it does cover — restating
that adds nothing. If there's a genuinely non-obvious exclusion worth
calling out (e.g. this problem looks like it should include something a
similar product usually bundles, but doesn't), fold one clarifying sentence
into "The problem" itself rather than adding a section that's empty more
often than not. If the exclusion is actually uncertain rather than decided,
that's an open question, not a non-goal — don't assert an exclusion you're
not actually sure of.

Keep it to one page. If it's growing past that, the problem is probably
several problems — flag that rather than writing a longer doc.

**Write for skimming.** Lead with the point; prefer bullets and headers to
prose; a paragraph is one or two sentences at most. If a sentence wouldn't
change what the reader does next, cut it.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.
