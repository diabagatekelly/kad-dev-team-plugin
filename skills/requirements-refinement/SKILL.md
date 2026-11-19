---
name: requirements-refinement
description: Pin down the concrete user requirement for one scope-map step (or one small, un-mapped problem) by asking the user directly — who benefits, what they actually want, and why — before any slice gets cut. Use once a step is about to be worked and its WHAT hasn't been confirmed with the user yet, before handing off to product-slicer. When the request points at a file of the owner's (a sheet, an export, a screenshot), invoke this skill before opening that file with any tool: the skill says how such a file is read.
---

# Requirements Refinement

**Trigger:** a scope-map step (or a small problem that skipped scope-map
entirely) is next in line to be worked, and nobody has actually asked the
user what they specifically want built for it. The problem doc states the
problem; the scope map names the rough shape; neither decides WHAT to
build — that decision doesn't get made by inference, it gets made by
asking.

**This is a live conversation, not a reading exercise.** Ask the user
directly — don't derive the answer from the problem doc or scope map alone,
even when a plausible answer seems obvious. A wrong assumption here
reshapes the slice that gets built on top of it.

**Your first response is questions, not a requirements doc.** Read the
problem doc, scope map and any code first so the questions are sharp, and
don't ask what they already answer. Before the questions go out, hold
each one against what you read: a fact a document states or the code
shows (who signs in, which provider takes the payment, what a route
already returns) is never put to the user as if unknown. "I couldn't
tell from the code" means look once more, at the routes and the wiring,
before it becomes a question. What you found is said as what you read,
and the question is only what the user wants done about it. Then ask in
one pass and stop until the user answers. Engineering heuristics (risk-avoidance, smallest-first)
are `product-slicer`'s, not grounds for deciding the WHAT on the user's
behalf.

**The pass is complete only when every question on the list below that
the documents don't answer has been put to the user.** A question you
haven't asked yet is not "Not yet confirmed"; it is still owed, and the
document isn't written until it has been asked. Writing the document
around the holes and asking the rest afterwards turns each late answer
into a revision of a document that didn't need to exist yet. Ask through
`AskUserQuestion` when it is available, one question per call.

**Ask, merged into one pass:**
- Who specifically benefits from this piece? Reuse what the problem doc or
  scope map already narrowed down; only ask if it's still generic ("the
  user") or genuinely ambiguous for this one piece.
- What are they actually trying to accomplish here, in their own terms?
- Why this, why now — is there a priority or trade-off they care about
  (e.g. "I want live bank sync even though it's riskier, because that's
  the whole point for me")? Don't assume risk-avoidance or smallest-first
  is what they'd choose; ask.
- What's the simplest version that would still feel like real progress to
  them — not the simplest version that's easiest to build.
- Were there alternative approaches they considered or rejected, and why?
  Capture the reason, not just the choice.

**An answer that skips one of your questions is not an answer to it.**
When the user's reply settles most of what you asked and says nothing
about the rest (what staff see of it, say), don't fill the gap from the
problem doc or from what seems reasonable, and don't drop it. Record it
under "Not yet confirmed" in the document, with what the answer would
change, and ask it again in your reply. A document that quietly confirms
something nobody said is the inference this skill exists to prevent.

The reverse holds too: a question the user answered is answered, even
when they didn't speak to every example you offered or gave a reason
where you asked for a trigger. Don't ask for the examples they skipped,
and don't ask again for a deadline when they told you why. Re-ask only
what they didn't address at all.

**Then reconcile the problem doc's constraints — a separate pass from
asking what they want.** The questions above decide the WHAT. This decides
what is already binding on it, and it is the step most likely to be
skipped, because a constraint written at problem-framing time rarely looks
like it belongs to the step in front of you.

Walk the problem doc's Constraints one at a time. For each: does it apply
to this unit? If yes, **say what it forces here.** If no, say why not.
Both answers get written down; a constraint that silently doesn't appear is
indistinguishable from one nobody read.

**Draw the consequence — restating the constraint is not the job.** This is
the whole point of the pass. "The system may be hosted off your own
hardware" is not a note about hosting; it means something reachable over a
network will display this unit's data, which forces a question about who is
allowed to see it. "Single user today, not single-user forever" is not a
note about the future; it means nothing here may assume one hardcoded
identity. A constraint carried forward as a quotation has not been
reconciled.

**A finding says what is forced and who decides it, not how to build it.**
One or two lines: the capability nobody has scoped, or the behaviour that
needs deciding, and the stage it goes to. Naming the file that shows it is
fine; prescribing the change (which route, which check, what the code
should do instead) is the design conversation, and writing it here is the
HOW this skill stays out of.

**A constraint that looks like a later step's problem is the one that gets
dropped.** "Applies to every step" includes this step. If the scope map
sets a constraint aside as cross-cutting, that makes it *yours to apply
here*, not someone else's to handle later — deferring it to whoever designs
or builds this is how it surfaces after slicing, when the cost of acting on
it is highest.

**When a consequence would change the shape of the work, ask.** Same
convention as everything else here. Noticing that a constraint forces a
capability nobody has scoped is a real finding and belongs in this
conversation, not three stages downstream.

This is not deriving the WHAT from the problem doc — that rule above still
holds. Checking a stated constraint against a decided scope is a different
activity from inferring what someone wants.

**Then walk the problem doc's Open questions the same way.** Each one this
unit would have to assume an answer to is either asked here or listed
under Not yet confirmed with what the answer would change. Half an answer
is a skipped question: "where may the data live" answered while "from
which devices" was never asked leaves the device question for whichever
later stage trips over it, and a later stage that has to assume it is the
backward route this pass exists to prevent. A question the problem doc
leaves open and this unit doesn't touch is left where it is, with a line
saying so.

**A file the owner provides is described, never quoted.** A sheet, an
export or a screenshot the owner points at stays where it is, outside the
repository, and nothing in it is written down by value: not in this
document, not in a question, not in a reply. In this order:

1. **List it before anything opens it**, as a row of `sources.md` in the
   target directory (create the file in this shape when it is not there).
   `Listed at` is `git rev-parse --short HEAD` at that moment: what was
   in the tree at that commit cannot have come from a file nobody had
   read, and the scan does not count it. Write a dash instead when there
   is no commit or no shell, and whenever the file was read, or a value
   of it may already be written down, before this row existed: with a
   dash everything counts. In `Tab or range`, name the one tab the stage
   reads when the file has several, never `all` for a workbook of many:
   the scan reads the tab named and nothing else, and every cell of
   every tab of a large workbook matches the language of any repository.

   ```markdown
   # Sources

   Files the owner provided. Locations only: no value from any of them
   is written here or anywhere else in the repository. Nothing opens one
   of them but kad-dev-team's `source_scan.py` (its `describe` for a
   file's shape, its `scan` for what got written down): never `cat`,
   read or grep one. A value that reached a commit is removed by the
   `delivery` skill's "Removing a value from history", on the owner's
   words, and no other way.

   | Source | Location | Tab or range | Read on | Listed at |
   |---|---|---|---|---|
   | <what it is> | `<its path, outside the repository>` | <the tab or range the owner named> | <date> | `<commit>` |

   ## Allowed by the owner

   Values a source also holds that the owner has said may be written,
   in their words, dated. Nobody else adds a line.
   ```
2. **Read its shape, not its rows**, and only the tab or range the owner
   named: `python3 -I "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/source_scan.py"
   describe '<path>' --tab '<tab>'` prints the column names, the row count
   and what kind of cell each column holds, and never a cell (add
   `--extract '<a scratch file outside every repository>'` when rows have
   to be counted by a script: the session never prints that file). With
   no shell: the first line alone for the column names (`Read` with
   `limit: 1`) and a count-only search for the rows. Never `cat`, `head`,
   `Read` in full or load the file with a library to look inside:
   whatever a command prints stays in the session's transcript for good,
   and one command that dumps a file puts the whole of it there (incident
   15). A file `describe` cannot read (a screenshot, a PDF)
   is listed the same way and looked at for its layout alone.
3. **Invent every example** (the names, the amounts, the dates) and say
   so once in the document ("examples are invented; none is a row of the
   sheet"), however much better a real row would make the point. One real
   row taken as an example in a requirements document was carried by the
   slice, the design, the story, the plan's test names and thirteen test
   files (incident 16).
4. **Check what you build on before you repeat it.** When `sources.md`
   lists a source, `python3 -I "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/source_scan.py"
   scan --planning '<target directory>'` prints the file, line and cell of
   every value of a listed source it finds, never the value. A hit in
   your own document is rewritten with an invented value; a hit in a
   document that is not yours is reported as a backward route to its
   owner, not edited; a hit that is the app's own word and no row of the
   file is the owner's to allow, never yours. The readiness gate and the
   chunk gate run the same scan.

**Template:**

```markdown
# Requirements: <step name — "scope-map-NNN step K", or "problem: <short name>" if no scope map> (requirements-001)

## Status
Active | Superseded by requirements-NNN

## User
Who specifically benefits from this piece.

## What they need
The confirmed capability, in plain language — decided with the user
directly for this one piece, not inferred from the problem doc or scope
map alone.

## Why this, why now
Any priority or trade-off the user expressed for this piece specifically.
State it even if it contradicts what a risk-avoidance heuristic would have
picked — that's the point of asking.

## Confirmed in scope
What's definitely part of this piece, as the user confirmed it. Plain
language — not a thin path, not acceptance criteria.

## Confirmed out, for now
What was raised but the user confirmed isn't part of this piece yet, and
why. Narrower than the scope map's whole-problem "Out of scope"; distinct
from `product-slicer`'s own "Explicitly deferred," which covers
slicing-technique deferrals decided later, once a thin path exists.

## Not yet confirmed
Anything you asked that the user's answers didn't settle, and any problem
doc open question this unit bears on that they didn't settle, one line
each: the question and what the answer would change. Neither in nor out
until they say. Never a question you haven't asked yet. Omit the section
when nothing is open.

## Constraints in force
Every constraint from the problem doc, one line each: what it forces for
*this* unit, or why it doesn't apply here. Consequences, not quotations.
Note any that turned out to force a capability nothing has scoped yet —
that's a finding for `product-slicer`, not a note.

## Outside systems and lasting things
Every system outside the app this unit talks to, and every thing the app
keeps a relationship with over time (a bank connection, a subscription,
a booking), by its everyday name, one line each; `none` when the unit
has neither. Names only, as the user spoke of them: no states, no
design. It is the list `software-architect:domain-model` models before
anything is sliced.
```

Keep it skimmable — this document answers "what did the user actually
confirm," not "here is a full specification."

**Never write a thin path, Given/When/Then acceptance criteria, or apply a
slicing technique** (happy-path-first, input variations, reduce scope,
etc.) — those stay `product-slicer`'s and `acceptance-criteria`'s job once
this hands off a decided WHAT. Nor chunk the whole problem into steps;
that is `scope-map`'s. If asked to do one of those, say so and hand it
back. If you catch yourself describing *how* the capability gets built
rather than *what* the user confirmed they want, stop — that's the next
persona's job, not this one's.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.

**Revise in place while the document is still yours; supersede once
someone has built on it.** While this stage's conversation with the user
is open, or while no later stage has cut, designed or written criteria
from the document, answers and corrections edit the Active file in place
and the orchestrator log records what changed. Supersede with a new
number (`Superseded by requirements-NNN`, numbered sequentially, same as
`scope-map` and `adr`) only when a later stage has already relied on the
document and the change alters what that stage decided. A project that
keeps its planning in git may choose in-place revision for every
document; the orchestrator records that choice once in its log and every
skill honours it.
