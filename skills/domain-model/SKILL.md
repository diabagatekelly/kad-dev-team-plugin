---
name: domain-model
description: Model how each outside system or lasting thing behaves over its whole life, once, before any slice is cut — for a bank connection, an account, a subscription, a booking, every state it can be in, how it gets there, what the person can do there and the way out. Use when a unit's requirements name an outside system or lasting thing that `domain-model.md` does not cover yet, or when a later stage (slicing, reliability, a review) meets a state the model lacks. Not a design (no components, no technology choice) and not a slice (no criteria, no order of work).
---

# Domain Model

## What you're producing

`domain-model.md` in the target directory: one table per outside system
or lasting thing the app keeps a relationship with, listing **every state
that thing can be in over its life**, not only the ones the next slice
needs. A lasting thing is anything that outlives one request and can
change without the app doing it: a bank connection, a subscription, an
account at a provider, a booking, a job that runs for hours.

Why it exists: on one project three slices in a row each met one more
state of a bank connection after they shipped. A login that lapses was
unrecoverable and became a slice of its own; that slice left a bank whose
login can never be restarted stuck for good; the next found accounts
added after the connect that are never updated. Each was a dead end a
review found, a High, then a slice. Listing how a call can fail
(`reliability-requirements`) does not find these: they are states of the
thing, not failures of a call.

**Not a design and not a slice.** No component, no technology, no
criterion, no order of work. The model says what can happen and what the
person can do about it; which slice handles which state is
`vertical-slicing`'s, and how it is built is `architecture-design`'s.

## What to read

- The Active requirements document's `## Outside systems and lasting
  things` list: those are the things to model. Model nothing it does not
  name; a thing you think is missing from the list is a finding for
  `product-manager:requirements-refinement`, in your reply, not a table.
- The problem framing document, for which provider is already chosen.
  When none is chosen, model the thing by what any provider of its kind
  does, and say so at the top of its table.
- **The provider's public documentation**, for how the thing really
  behaves: its lifecycle page, its error and status reference, its
  webhooks or events list. Each state cites the page it came from by
  URL. When the session cannot reach the documentation (no web tool, a
  refused request), do not work around it: say so once and mark the
  states `to verify`.

## Find the states

Walk the thing's life in order and write a row for each state you find.
Ask each of these of every thing; most produce at least one row:

- **How does it begin**, and what is it between asked-for and ready?
- **What is it while it works?**
- **How does it stop working without the app doing anything?** Access
  that lapses or is revoked; the provider asking the person to do
  something again; the provider removing it; the account behind it
  closed.
- **What can change at the provider after it was set up?** Parts added
  or removed later (a new account under a connection); records the
  provider corrects, withdraws or replaces after sending them; a
  provisional record that becomes final.
- **What if the same action is refused every time?** A state whose only
  action is the one the provider keeps refusing is a dead end: it gets
  its own row.
- **How does the person end it**, and what is left afterwards?

Give each state a short name, lower-case and hyphenated, in backticks
(`login-lapsed`). That name is the one every later document uses: the
slice's `## Domain states` section, the reliability document's failure
modes, the readiness gate.

For each state fill every column:

- **Entered by**: what puts the thing there, in one line.
- **What the person sees and can do**: in the app, in that state. A
  state the app does not yet show at all says `nothing yet`.
- **Way out**: the action that takes the thing to another state, naming
  that state; or `by itself -> <state>` when the provider moves it; or
  `none needed: <why>` for the end of the thing's life; or `none` when
  there is no way out in the app.
- **Supported**: `yes`, or `unsupported` with the owner's words (below).
- **Source**: the documentation page's URL, or `to verify: <the one
  step that would confirm it>` (a step in the provider's test mode
  where there is one). A state you know of only from memory is `to
  verify`, never a URL you did not read in this session.

## A state with no way out is the owner's to accept

Every state has a way out, or is deliberately unsupported. A state whose
way out would be `none` is a decision about what the product does, so it
is asked, **one `AskUserQuestion` per such state**, your recommendation
first: support it (say what the way out would be) or leave it
unsupported (say what the person is left with while it lasts). Nothing
else is asked here: the states, their names and their sources are yours
to write, and the orchestrator's entry lists them as taken.

**When any state needs that question, the questions are your whole first
response and nothing is written before the answers.** Without the
question tool, ask in plain text and end the turn. Record each answer in
the row's Supported cell: `yes`, or `unsupported (owner, <date>:
"<their words>")`. When no state needs it, write the document straight
away.

## Revised in place, whenever a state turns up

The model is one file for the project, revised in place; the
orchestrator's log is its history. When a later stage meets a state the
table lacks (a slicer that cannot name where a slice leaves the thing, a
reliability pass that finds a refusal that never clears, a reviewer's
dead end), that is a backward route to this skill: add the row with its
source, ask if it has no way out, and say in your reply which states
were added. Never remove a row because no slice handles it yet: an
unhandled state with a way out named is exactly what the next slices are
cut from.

## Check it the way the gate will

The readiness gate's `domain-states-modelled` check reads this file: the
table's first column is the state's name, and its header row names the
`Way out` and `Supported` columns by those words. Keep the header as the
template has it.

## Template

```markdown
# Domain model

One table per outside system or lasting thing. Revised in place.

## <The thing, by its everyday name> (<the provider behind it, or "any provider of this kind">)

| State | Entered by | What the person sees and can do | Way out | Supported | Source |
|---|---|---|---|---|---|
| `<state>` | <what puts it there> | <what they see; what they can do> | <action> -> `<state>` | yes | <URL> |
| `<state>` | <…> | <…> | none | unsupported (owner, <date>: "<their words>") | to verify: <step> |

## To verify
Each `to verify` step, once, for whoever can run it against the
provider's test mode. Omit when there is none.
```

**Write for skimming.** The tables are the document; no prose above them
beyond one line per thing.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save `domain-model.md` there.
Invoked directly, use the location the user gave or that the
conversation plainly implies; if nothing says, ask before writing
anything. Never search the project for a place to put it.
