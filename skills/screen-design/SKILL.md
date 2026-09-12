---
name: screen-design
description: Compose one UI-touching slice's screen within the project's established design system — layout, component composition, and interaction flow. Use once a slice has been cut and a design system already exists (or has just been established) for this project.
---

# Screen Design

## What this decides, and what it doesn't

How this one slice's screen is arranged, which established components it
uses, and what happens as the user moves through it. It does not re-decide
a token, a component pattern, or the layout shell — those are
`design-system`'s job, already settled by the time this runs. If applying
this slice genuinely seems to need one of those to change, that's a
proposal back to `design-system`, not something to quietly work around
here. It also does not verify accessibility compliance — design so it
holds up, but confirming it belongs to `accessibility-engineer`.

## Start from what's already decided

The slice's confirmed scope — what it does, for whom, and why — comes from
`product-slicer`'s write-up; don't re-derive it or expand past it. The
design system's tokens and patterns come from `design-system`; don't
re-decide them here even when a different choice seems appealing for this
one screen.

## Reuse before you invent

Check whether an existing component pattern already covers what this
screen needs before proposing a new one. If a genuinely new pattern is
required, that's real information for `design-system` to absorb, not a
one-off you build and forget — flag it rather than letting an ad-hoc
pattern quietly become the second version of something that should be one
thing.

## Apply the design-quality heuristics

Run the interaction flow through these, adapted per screen rather than
mechanically checked off:

- **Consistency** — same action, same label, same visual treatment
  everywhere it appears in this project, not just on this screen.
- **Visible feedback** — every action the user takes produces a response
  sized to its weight: a subtle change for a hover, a clear state change
  for a filter, an explicit confirmation for something that saves or
  deletes.
- **Errors prevented, then recovered from** — block what you can before
  submission; when something still fails, say specifically what and how to
  fix it.
- **User stays in control** — every dialog has an obvious way out, every
  multi-step flow can go back, nothing traps the user in a state they
  didn't choose.
- **Recognition over recall** — what the user needs is visible on screen;
  don't make them remember something from a step ago or type a value they
  already selected.
- **Fast for the common case, learnable for the rest** — optimize the path
  most people take most often; keep less-common options available without
  cluttering the primary one.
- **The user's language, not the system's** — labels read the way someone
  who actually does this work would say it out loud, not the underlying
  field or schema name.
- **Nothing on screen that doesn't earn its place** — if an element
  doesn't help this task right now, it's competing with what does.
- **A clear end** — multi-step interactions have a visible beginning,
  middle, and a completion the user can't mistake for "did that even
  work?"

When two of these genuinely pull against each other for this screen (e.g.
showing more context helps recognition but adds clutter), pick one and
write down why — the trade-off is a decision worth keeping, not something
to re-litigate the next time someone looks at this screen.

## Get the copy right too

Interaction flow includes what the interface says, not just how it's
laid out:

- **Calls to action** name the specific outcome, verb first — not "OK" or
  "Continue." A destructive action's button names the destruction, not
  "Confirm."
- **Errors** say what happened, why if it's actually known, and what to do
  next — in that order, in plain language, without blaming the user.
- **Empty states** explain what belongs here, why it's empty right now,
  and how to fill it — never just "No results."
- **Confirmations** name the action that succeeded, past tense, in one
  calm line — save real enthusiasm for moments that actually warrant it.
- **Field labels** read as nouns, not questions, and required fields are
  marked the same way everywhere on the screen.

## Validate by walking through it as the user

Before presenting the design, walk it mentally as the person using it
would: can they tell what to do first? Can they finish the task without
leaving this screen? Do they know what happened after each action? Can
they recover if they make a mistake? Does this match what the rest of the
product already trained them to expect?

## Self-critique before presenting

Check the composed screen against five angles before handing it over:

1. **First impression** — one clear primary surface, not several elements
   competing to be the point of the screen.
2. **Usability** — interactive elements look interactive; a destructive
   action looks different from a constructive one.
3. **Visual hierarchy** — the most important thing has the most visual
   weight; related elements sit close together, unrelated ones don't.
4. **Consistency** — every value traces back to a token from the design
   system, nothing ad-hoc.
5. **Accessibility** — semantic elements used for what they are, and color
   never carrying meaning by itself.

## Ask when more than one legitimate direction exists

A navigation flow, an information architecture, a sequencing choice can
each have more than one reasonable shape. Present the real options and let
the user pick — don't resolve a genuine fork on their behalf because one
path seemed obviously better to you.

## Produce a rendered artifact, not production code

Render an actual mockup of the screen rather than describing it in prose —
this is a visual question, and a paragraph is a weak medium for it. Make
it concrete enough that someone could build from it directly, but keep it
a design artifact, not the final styled component wired into the real
codebase. Implementing it is a later step, for whichever persona owns
writing code once one exists to hand it to.

## Output format

```markdown
# Screen design: <slice name>

## Thin path covered
What this screen delivers, tied back to the slice it's designed for.

## Layout and composition
The rendered mockup, plus which established patterns it uses and how
they're arranged for this screen specifically.

## Interaction flow
What happens at each step, including error and empty states, walked
through as the user would experience it.

## New patterns proposed, if any
Anything this screen needed that the design system didn't already have,
flagged back to `design-system` rather than invented ad hoc.

## Open questions
Anything genuinely unresolved, and who resolves it next.
```

Keep it skimmable — this answers "what does this screen look like and do,"
not a full specification of every possible state.
