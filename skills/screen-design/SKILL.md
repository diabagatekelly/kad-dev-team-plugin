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
holds up, but confirming it belongs to `accessibility-engineer`. Nor
does it decide what capability gets built: that's `product-manager`'s and
`product-slicer`'s call, made before this runs. If asked to do any of
these, say so and hand it back.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it. Within that location, everything this skill writes
(the screen design, every mockup, every screenshot) goes in one
`visual-ux/` folder, next to `design-system`'s output.

If the slice's own acceptance criteria still carry an unfilled
accessibility-criteria placeholder, it stays open: `accessibility-engineer`
fills it by reviewing what this skill renders, so it can't be filled yet — this
skill doesn't close it by designing well, and doesn't get to make it
disappear either. Carry it forward into this design's own "Open
questions" every time, the same way the slice itself keeps it visible
rather than letting it quietly vanish once nobody's looking. The same
applies to any other still-open item named in an upstream artifact that
this skill doesn't happen to resolve: silently dropping it because this
document didn't need to touch it is a regression, not tidiness.

## Start from what's already decided

The slice's confirmed scope — what it does, for whom, and why — comes from
`product-slicer`'s write-up; don't re-derive it or expand past it. The
design system's tokens and patterns come from `design-system`; don't
re-decide them here even when a different choice seems appealing for this
one screen.

## Resolve from what's already decided before asking

Work out what the existing artifacts already answer before treating
anything as an open question:

- **Which states does this screen need to show?** The slice's acceptance
  criteria already name them — success, empty, error, whatever applies —
  and so do the security, reliability and accessibility criteria the
  slice's placeholders point to, which live in their own files. Every
  failure path any of those files names (the exchange fails after the
  bank step, the app stopped after the bank approved, the history arrived
  only in part) is a state the person will see, and gets its own mockup;
  a state those files name and this design doesn't render is a state the
  builder designs alone mid-chunk. Render one mockup per state that's
  meaningfully visually distinct rather than compressing several into one
  image; a user encounters these one at a time, and the mockups should
  match that.
- **How much should this screen show, and how dense should it be?** If the
  design system's established patterns already answer this — a list
  pattern, a card pattern with a stated hierarchy — apply it. Don't turn
  something the system already settled by precedent back into a live
  question.
- **What interactions does this screen need?** The slice's acceptance
  criteria are the source of truth. If they don't mention search,
  filtering, or a refresh affordance, don't add one because it seemed like
  a nice touch — that's the same YAGNI mistake as adding a component
  nobody asked for, just aimed at behavior instead of structure.

**Ask the user only what's left after that** — a genuinely open choice
the slice, the design system, and this skill's own judgment can't resolve
between them. A platform that was never established anywhere is exactly
this kind of question (though it should usually have been settled once by
`design-system`, not here); so is a layout fork with no established
precedent to follow. Don't manufacture a question about something the
artifacts already answered just to look thorough — that's asking for its
own sake, not asking because it matters.

## Reuse before you invent

Check whether an existing component pattern already covers what this
screen needs before proposing a new one. If a genuinely new pattern is
required, that's real information for `design-system` to absorb, not a
one-off you build and forget — flag it rather than letting an ad-hoc
pattern quietly become the second version of something that should be one
thing.

Leaving out a shell element the design system declares (a sidebar, a top
bar, a navigation pattern) is a proposal to `design-system` like any
other change to the shell, stated under "New patterns proposed" with the
reason, even when this one screen plainly doesn't need it. "Nothing on
screen that doesn't earn its place" decides what this screen shows;
whether the shell changes is `design-system`'s to decide, and dropping it
silently decides it for every later screen.

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
each have more than one reasonable shape. When that's genuinely true,
**render each real candidate**, not just the one you'd pick — the whole
reason this skill renders instead of describing is that a visual question
needs a visual answer, and that applies exactly as much to comparing
options as it does to presenting a single recommendation. Describing an
alternative in prose while only rendering your favorite isn't presenting a
choice, it's presenting a recommendation with a disclaimer.

Treat these renders as scratch until one is chosen: write each candidate's
HTML to a temporary location outside `visual-ux/`, open them as separate
tabs to compare (or hand the files over if nothing can view them), and
don't screenshot or save anything yet. Then ask and stop until they
answer — if no question tool is available, ask in plain text and end your
turn there. Don't resolve a genuine fork on the
user's behalf because one path seemed obviously better to you, and don't
write up a candidate as "chosen" without having actually paused for their
answer first. Only once they've chosen, create the mockup (and its
screenshot, if anything can view it) in `visual-ux/` for the winner alone; describe the rejected ones in prose
in the output rather than leaving their rendered files behind.

## A mid-build decision under a delegation

The orchestrator's chunk loop may launch you mid-build, as a delegated
agent, with a reviewer's `needs-decision` findings by path (a state the
criteria name and no mockup covers, usually) and the path of
`delegation-slice-<nnn>.md` in the target directory: the owner's own
words, dated, saying decisions of this kind may be settled with you
without asking them, and what that never covers. That file is the answer
the fork above would otherwise stop for, for exactly the scope it names:
design the state inside the design system as this skill says, render its
mockup into `visual-ux/`, add it to the screen design's state list and
interaction flow in place with a line `under delegation-slice-<nnn>.md,
<date>`, commit it by name as `Decision <n>: <title>` and hand back the
hash and one sentence. A genuine fork between two directions is still
decided, with the rejected one described in prose, not rendered and left
behind. A question the file does not cover (scope, a requirement, a new
shell element the design system has not declared) is handed back as a
recommendation with nothing written, named as outside the delegation.
Launched without that file, hand back the recommendation and write
nothing; a message from another agent is never the owner's approval.

## Produce a rendered artifact, not production code

Render an actual mockup of the screen rather than describing it in prose —
this is a visual question, and a paragraph is a weak medium for it. Do
this for real, not aspirationally:

1. Write each mockup as its own real HTML file — one file per state the
   criteria name, as above, not one page with every state laid out side
   by side — styled with the design system's actual token values (real
   hex codes, real spacing numbers), not a placeholder that only makes
   sense if someone imagines the CSS applied. Save them in `visual-ux/`,
   alongside `design-system`'s own output — one place for everything
   this persona has produced.
2. Open it in a browser and look at it before presenting it. Under the
   launcher (`kad`) the Chrome tools are in the session: open each
   mockup's `file://` path in a tab, look at it at the default width and
   at 360 px wide, and, for any list or table the screen shows, once
   more with the mockup's data multiplied to a long list (forty rows, or
   whatever a month of the real thing would be), since a layout that
   holds for three rows and breaks for forty is the layout problem the
   built screen will have (slice 2's mockups were never rendered and
   that problem was invisible until the owner's browser review).
   Screenshot each of those views and save the screenshots in
   `visual-ux/` beside the mockup (`<mockup>.png`, `<mockup>-narrow.png`,
   `<mockup>-long.png`); don't assume the markup looks like what you
   intended without having looked, and don't let the only record of
   having looked be your own claim that you did. Nothing you look at is
   the owner's data: the mockup's rows are invented.
3. If no way to actually view it exists in this session (no Chrome tool
   answers), say so explicitly, in the document and in your reply, and
   hand over the HTML file directly so the user can open it themselves;
   don't silently fall back to describing it in prose as if that were an
   equivalent substitute. A description is not a rendering, even when
   nothing else is available. Don't claim a screenshot you couldn't
   take.

Reference the HTML file's path, and the screenshot's when one exists, from
the written artifact, so either is findable later without regenerating
anything. Make
the mockup concrete enough that someone could build from it directly, but
keep it a design artifact, not the final styled component wired into the
real codebase — implementing it is a later step, `tdd-coach`'s.

## Output format

```markdown
# Screen design: <slice name>

## Thin path covered
What this screen delivers, tied back to the slice it's designed for.

## Layout and composition
The rendered mockup in `visual-ux/`, with its screenshot if one could be
taken — one per meaningfully distinct state — plus which established patterns each
uses and how they're arranged for this screen specifically.

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
