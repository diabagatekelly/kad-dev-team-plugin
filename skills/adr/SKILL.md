---
name: adr
description: Write or review an Architecture Decision Record (ADR) once a decision has been made. Use when a decision is architectural, costly to reverse, or non-obvious enough that the reasoning would otherwise be forgotten or re-litigated.
---

# Architecture Decision Record (ADR)

**Trigger:** a decision has been made. Not every decision earns an ADR —
check all three before writing one:

1. **Architectural** — does it touch system structure, a technology/framework
   choice, a cross-cutting pattern, or infrastructure?
2. **Significant** — would reversing it be costly, does it affect more than
   one area, does it set a standard others will follow?
3. **Non-obvious** — could a reasonable person question the choice or expect
   a different alternative?

If any of the three is "no," this isn't ADR territory — a README note or a
comment is probably enough.

**Step one, every time: the three checks, answered before anything
else.** Before reading a file, before a question or a draft, and just as
much when the user has already made the case, named the alternatives
and told you the file name. One line each:

```
Architectural: yes/no — <why>
Significant: yes/no — <why>
Non-obvious: yes/no — <why>
```

Any "no" and you stop there: say it isn't ADR territory, suggest the
lighter home (a commit message, a PR description, a comment, or nothing),
and write no ADR unless the user then insists. Being asked for an ADR
doesn't make a decision ADR-worthy.

The three lines are the record that the check was made, and where they
live depends on the answer. Any "no": they open your reply, followed by
the lighter home. All three yes: they go into the ADR itself, as its
"Why this is an ADR" section (template below), so the document carries
its own justification and a reader never has to trust that the check
happened; the reply then only needs to say where the file is. An ADR
without that section, or a reply that goes straight to "I wrote the
ADR" with the three lines in neither place, has skipped the step however
sound the decision was; a request that arrives fully argued is the case
most worth checking, because nobody else will. Each answer is yes or
no. A check that feels borderline gets the answer it falls on and the
reason, not "borderline": the rule above needs a yes or a no to act on.

**Template:**

```markdown
# ADR-NNN: <decision title, phrased as the decision, not the topic>

## Status
Proposed | Accepted | Superseded by ADR-NNN

## Why this is an ADR
Architectural: yes — <why>
Significant: yes — <why>
Non-obvious: yes — <why>

## Context
The forces at play — constraints, requirements, prior art — stated neutrally,
without arguing for the answer yet.

## Decision
What was decided, stated as a single clear sentence if possible.

## Alternatives considered
Each alternative with the concrete reason it was rejected. "We didn't like
it" is not a reason; "it requires a paid tier, violating the free-tier
constraint" is.

## Consequences
What becomes easier, what becomes harder, and what this decision forecloses.
Be honest about the downsides — an ADR that only lists upsides wasn't
reasoned through.
```

**Revise in place while the decision is still yours; supersede once
someone has built on it.** Number ADRs sequentially. One still `Proposed`,
or `Accepted` with nothing yet designed or built on it, is corrected in
place, and the orchestrator log records what changed. Once a later stage
has relied on it, never edit it: write a new numbered one and mark the old
`Superseded by ADR-NNN`. The history of *changed minds* is itself useful
information; don't destroy it. A project that keeps its planning in git
may choose in-place revision for every document; the orchestrator records
that choice once in its log and every skill honours it.

**An ADR never answers "how."** No code, no file paths, no config values, no
function names, no testing approach — those belong in the code or in a
design doc, and including them here guarantees the ADR goes stale. If a
sentence describes implementation rather than the decision itself, cut it.

**Write for skimming.** Lead with the point; prefer bullets and headers to
prose; a paragraph is one or two sentences at most. If a sentence wouldn't
change what the reader does next, cut it.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.
