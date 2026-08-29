---
name: docs-writer
description: Purposeful documentation for software projects — problem framing docs, ADRs, WHY-not-WHAT comments, and knowing when NOT to write documentation. Use when capturing a new problem before any issue/slice/code exists, recording an architectural or design decision, deciding whether a comment is warranted, or auditing existing docs for staleness and ceremony.
---

# Docs Writer

## Core stance

Documentation is a liability, not an asset — every doc is a promise to keep
something in sync with reality, and broken promises (stale docs) are worse
than no promise at all. Default to **no doc**: self-documenting code, clear
naming, and tests are the primary way a codebase explains itself.

Write a doc only when losing the information it carries would cost more than
maintaining it. That test rules out: restating what the code already says,
ceremonial docs nobody reads (design-doc-as-ritual), and docs that duplicate
information already tracked elsewhere (issue tracker, git history, tests).

Four artifact types cover almost everything worth writing down. Each has a
different trigger — don't reach for the wrong one.

## Skimmability is not optional

Every artifact here is read by someone time-poor and skimming, not settling
in for a narrative. Lead with the point. Prefer bullets, tables, and headers
over prose. Cap paragraphs at 1-2 sentences — none is better. Cut
throat-clearing and "how we got here" history. If a sentence doesn't change
what the reader does next, delete it.

This governs everything below — a technically correct doc that's a wall of
text has still failed.

## 1. Problem framing doc

**Trigger:** a real problem exists, but there is no issue, no slice, and no
code yet. This is the earliest artifact in a project's life — its job is to
pin down the problem crisply enough that later slicing and architecture work
have a stable thing to refer back to, without yet committing to *how* it will
be solved.

A problem framing doc is not a spec and not an ADR — no solution or decision
belongs in it. If you catch yourself designing, stop and move that content to
an ADR once the decision is actually made.

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
decision and doesn't belong here yet.

## Non-goals
What this problem explicitly does not include, to keep scope from creeping
in before slicing even starts.

## Open questions
Things that must be answered before a first slice can be cut. It's fine —
expected, even — for this section to be non-empty.
```

Keep it to one page. If it's growing past that, the problem is probably
several problems — flag that rather than writing a longer doc.

## 2. Architecture Decision Record (ADR)

**Trigger:** a decision has been made that is either expensive to reverse or
non-obvious enough that future-you (or a teammate) would otherwise re-litigate
it or forget why it was made. Not every decision earns an ADR — routine,
easily-reversible choices don't.

Ask before writing one: "if this doc didn't exist, what would go wrong six
months from now?" If the answer is "nothing," skip it.

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

## 3. WHY-not-WHAT comments

Default to zero comments. A comment earns its place only when it explains
something the code cannot express on its own:

- a constraint that isn't visible locally ("this must stay synchronous — the
  caller holds a lock")
- a workaround for a specific external bug or limitation
- a non-obvious invariant a future edit could silently break
- a rejected-sounding-more-obvious alternative and why it doesn't work

Never write a comment that a reader could produce by reading the next line.
`// increment counter` above `counter++` is noise, not documentation. Delete
comments like this on sight during review rather than leaving them.

## 4. PR and issue descriptions

**Trigger:** describing a change for review, or filing/updating a ticket.

- Explain each piece of work in plain language a reviewer can follow without
  cross-referencing anything else.
- Keep ticket/issue IDs out of the narrative — put them on a short trailing
  reference line (e.g. "Tracked under PROJ-123") instead of weaving them
  into sentences.
- If AI materially produced the change, say so accurately and keep it
  current: name the specific model/tool and its role (plan, implement,
  review), not just "AI." Update the note when the tooling or role changes —
  a stale provenance note is a lie by omission.

## Staleness / ceremony audit

When reviewing existing docs (not writing new ones), flag:

- **Stale**: describes behavior the code no longer has. Worse than no doc,
  because it actively misleads.
- **Restates code**: could be deleted with zero information loss because the
  code already says it as clearly.
- **Ceremonial**: exists to satisfy a process checkbox, not to answer a real
  future question. Usually identifiable because no one can say who would
  read it or when.
- **Orphaned decision history**: an ADR that was quietly overturned in
  practice but never marked Superseded — the doc and the codebase now
  disagree about what was decided.

Report findings the same way any review does: file, the specific claim that's
wrong or pointless, and what to do about it (delete, update, or supersede).
Don't propose new process to prevent staleness — the fix is almost always
"delete the doc," not "add a review cadence."
