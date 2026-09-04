---
name: orchestrator
description: Route a problem to whichever kad-dev-team persona/skill applies next, by inspecting what already exists (problem doc, scope map, requirements, slices) rather than the user having to name the right persona each time. Use when the user wants to move a problem forward and hasn't said which persona/skill to use, or says "what's next" / "keep going" on a problem already in progress.
---

# Orchestrator

**This is a skill the main agent loads, not a persona to spawn.** Every
persona in this roster that plans work (`docs-writer`, `product-manager`,
`product-slicer`, `software-architect`) blocks on `AskUserQuestion` and
must run inline — never as an async `Agent` spawn. Orchestrating them means *you* adopt each one's
instructions in turn, in this same conversation, the same way you would if
the user had asked for that persona directly. There is no launching or
parallelism here.

**Skip this skill** when the user already named what they want directly
("write an ADR for X," "audit the docs for staleness") — routing only
earns its keep when the user hasn't said which persona/skill applies and
you'd otherwise have to guess or ask them to pick.

**Stay inside your lane while inspecting.** Every read you do — in step 2,
and when adopting a persona in step 4 — is confined to (a) the `AGENT.md`
and `SKILL.md` files the routing actually needs, and (b) the resolved
target directory. Never read anywhere else in the project "for context" —
not this plugin's own `evals/`, not other skills' fixtures, not unrelated
directories. If this is being dogfooded inside the plugin's own repo,
those directories look like real project content but aren't; outside that
repo, they won't even exist. Either way, wandering into them isn't this
skill's job.

## Procedure

**1. Identify the target.** You're invoked with the artifacts directory as
a parameter, or not:
- **Given one** — that's the target. Skip straight to step 2. Don't
  second-guess it, don't search for a different one.
- **Not given one** — ask once, before doing anything else: "Where do this
  problem's artifacts already exist, or where should they be created if
  we're starting from scratch?" Whatever the user answers becomes the
  target for every persona this skill invokes on this problem, this
  session and any future one — record it nowhere except by virtue of the
  first artifact actually landing there. Never guess a location yourself
  and never search the project for one instead of asking — if it wasn't
  handed to you, ask.

**2. Inspect what already exists in the target directory** — cheap,
mechanical checks only, never a semantic read of full artifact prose:
- A problem framing doc (a file whose top heading is `# Problem: ...`)?
- Any `scope-map-*.md` files? If more than one, the current one is the
  highest-numbered file whose `## Status` says `Active` (not `Superseded
  by ...`).
- Any `requirements-*.md` files? Same Active/Superseded rule. Which unit
  (scope-map step, or "the problem" if there's no scope map) does the
  current one belong to?
- Any slice files? For each, does its title name a source scope-map step
  (e.g. "scope-map-001 step 2")? A slice with no such reference was cut
  directly from the problem doc. Has it been written up as a user story
  yet (a matching user-story artifact, if this project tracks those
  locally — otherwise take the user's word for whether filing happened)?
  Has it been designed yet (a matching design-doc artifact from
  `architecture-design`, if this project tracks those locally — otherwise
  take the user's word)?

**3. Route by what's missing**, in this order. Each row assumes everything
above it in the table is already satisfied for the current unit of work
(a scope-map step, or the whole problem if no scope map applies):

| Detected state | Route to |
|---|---|
| No problem framing doc | `docs-writer:problem-framing-doc` |
| Problem doc exists; no scope map, no requirements doc, no slice anywhere yet | `docs-writer`, to decide — per `scope-map`'s own trigger criteria, by reading the problem doc — whether this needs a scope map or is small enough to treat as one unit. This is the persona's judgment call from the problem doc's own content, not an orchestrator-level question; it may still ask the user if genuinely torn, just not by default. |
| A unit is identified (the lowest-numbered Active scope-map step with no requirements doc yet, or — if no scope map exists — the problem itself) and has no requirements-refinement doc | `product-manager:requirements-refinement` for that unit |
| The current unit has a requirements-refinement doc but no slice yet | `product-slicer` (`vertical-slicing` + `acceptance-criteria`), using the requirements doc as the primary input for WHAT to slice — not re-deciding it |
| A slice exists for the current unit but hasn't been written up as a user story yet | `docs-writer:user-story-writeup` |
| The current unit's slice has been written up as a user story but has no design doc yet | `software-architect:architecture-design` for that slice |
| The current unit's slice has a design doc | **Stop — see step 5.** Don't advance to the next scope-map step. |

Never invent a stage this table doesn't cover. ADRs and `staleness-audit`
are event-triggered, not part of this forward spine — hand off to them
only if the user asks.

**4. Execute exactly one routed step, inline.** Read the target persona's
`AGENT.md` and the specific `SKILL.md` the trigger matched — nothing else.
Adopt those instructions directly — this is live use, not a dry run: if
that persona would ask the user something, actually ask via
`AskUserQuestion`. Tell it explicitly where to save its output — the
location resolved in step 1. It should not ask where to save or invent a
different location; you already resolved that. Produce the real artifact
and save it there, using that persona's own filename/heading convention.

**5. Report, then ask whether to continue — never chain silently.** State
what was detected, why it routed where it did, and what got produced.
Then:
- **If step 3 found a next row** (there's more to do for the current
  unit): name what that next step would be and ask whether to continue to
  it now, in this same conversation. If yes, loop back to step 2 for the
  now-current state — don't re-run step 1. If no, stop and wait.
- **If the current unit just reached the terminal row** (its slice was
  just designed by `software-architect`): don't propose anything further.
  Say plainly that this is as far as the roster currently reaches —
  `tdd-coach` would implement this design next, and doesn't exist yet.
  Moving on to the next scope-map step's requirements or slicing before
  this one is implemented and learned from would repeat the mistake this
  rule exists to prevent: deciding too much before anything's been built.
  If the user explicitly wants to start a different unit anyway, that's
  their call to make by asking directly — not something this skill
  offers.
