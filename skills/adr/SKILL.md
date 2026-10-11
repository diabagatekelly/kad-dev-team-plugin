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

**Your response opens with the three checks**, before any question or
draft, one line each:

```
Architectural: yes/no — <why>
Significant: yes/no — <why>
Non-obvious: yes/no — <why>
```

Any "no" and you stop there: say it isn't ADR territory, suggest the
lighter home (a commit message, a PR description, a comment, or nothing),
and write no ADR unless the user then insists. Being asked for an ADR
doesn't make a decision ADR-worthy.

**Template:**

```markdown
# ADR-NNN: <decision title, phrased as the decision, not the topic>

## Status
Proposed | Accepted | Superseded by ADR-NNN

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

Number ADRs sequentially and never edit one after it's Accepted — supersede
it with a new one instead. The history of *changed minds* is itself useful
information; don't destroy it.

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
