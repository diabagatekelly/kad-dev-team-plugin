---
name: design-system
description: Establish, or on request review and evolve, a project's UI design system — aesthetic direction, design tokens, and core component patterns. Runs once per project as the binding constraint every subsequent screen composes within. Use when a UI-touching slice is about to be designed and no design system exists yet, or when asked to review, audit, or evolve an existing one.
---

# Design System

## What this decides, and what it doesn't

The vocabulary every screen in this project will compose from: the
aesthetic direction, the design tokens (color, typography, spacing, and the
rest), and the core component patterns. It does not decide how any one
screen arranges these — that's `screen-design`, invoked per slice against
whatever this skill establishes. It does not verify that a built screen
actually conforms to an accessibility standard — that's
`accessibility-engineer`'s job, once that persona exists. This skill's
accessibility responsibility stops at designing tokens and patterns that
make conformance *possible*, not at confirming any particular screen
achieved it.

## Establishing it the first time

### Read what's already been decided

Before drafting anything, read whatever the project has already settled:
brand direction, platform requirements, and any quality attributes named
for the UI, plus the technology choices from `technology-bootstrap` if that
skill has already run. Work within these — this skill decides the visual
system, not the tech stack or the brand.

### Establish the platform, if nothing has yet

A native mobile app, a responsive web app, and a desktop app don't share a
starting point — this shapes the tokens and patterns as much as aesthetic
direction does, and neither `technology-bootstrap` nor anything else in
this roster necessarily settles it. If nothing has, that's a real decision
for this skill to make once, with the user — not something to leave
implicit or let `screen-design` re-ask per slice. Once decided, it's part
of what this system establishes; every screen inherits it the same way it
inherits the color palette.

### Commit to an intentional direction

Name what this interface is for, who uses it, and what should make it
memorable. Aesthetic direction is taste, not a technical question with one
correct answer.

**If the user hasn't already told you which starting point applies, ask
before doing anything else:** a concrete reference to work from (a
screenshot, a link to an existing product, a named comparison like "make
it feel like Stripe"), or candidates generated for them to choose between.
Extracting from a reference and generating from scratch are different
mechanisms — don't guess which one is wanted and start rendering on a
guess.

**Working from a reference.** Treat it as the intentional direction
already made, not raw material to reinterpret or improve on. If it's an
image, read it directly and extract the actual values driving it: the
dominant/brand color, accent colors, background and surface treatment, how
sharp or rounded corners read, how much (if any) shadow/elevation is
present, the typographic impression (serif or sans, weight, density), and
spacing density. If it's a named comparison with no image, apply your best
informed reading of that reference's actual character instead of sampling
pixels. Either way, render one real mock applying those values to this
project's own component — not multiple candidates, since there's nothing
to choose between when the direction is already given — open it, and
confirm with the user that it reads as a faithful match before treating it
as settled. A reference is a target to hit; assuming your first attempt
landed without checking is a real failure mode. Once confirmed, save that
mock's HTML and a screenshot straight to `visual-ux/` — there's no losing
candidate to keep out of it.

**Generating candidates, when there's no reference.** Generate a small
number of genuinely distinct directions scoped to the actual domain — a
financial tool, a creative tool, and a kids' app don't share a starting
point, so ground the candidates in what this specific product is, not a
generic style menu. Each candidate needs to be a real, fully-committed
point of view (minimal, dense, playful, austere, editorial, whatever
actually fits) — not a hedge between them, and not three variations on the
same idea wearing different colors.

Render a sample of each for real, but treat this render as scratch, not
output: write each candidate's HTML file to a temporary location outside
the artifacts directory (nothing goes in `visual-ux/` yet), then open all
of them as separate browser tabs so they can actually be seen and compared
side by side. Don't describe the candidates in prose and call that
rendering; if there's genuinely no way to view anything in this session,
say so and hand over the files rather than substituting a description
silently. Don't screenshot or save anything to disk at this stage — the
live tabs are for looking, not for producing a record yet.

**Then stop and ask — with a real question, not a narrated choice.** With
the tabs open, ask the user to pick via an actual blocking question. Never
write up a candidate as "chosen" without having genuinely paused for their
answer first, even when one option seems obviously right — deciding on
their behalf and describing it in the past tense afterward is the same
unasked decision this skill exists to avoid, just worded to look like it
wasn't one.

**Only once they've chosen, create `visual-ux/` and populate it with the
winner alone:** the chosen candidate's HTML file (rewritten there, not
moved from scratch) and a fresh screenshot of it. Close the losing
candidates' tabs and discard their scratch files — they don't get a saved
HTML file or screenshot. A prose description of each rejected candidate
and why it lost, in the output's "Candidates considered" section, is
enough of a record; regenerating one to look at again is cheap if it's
ever actually needed.

Either way, "reasonable defaults with no particular character" is never the
answer. That's the absence of a direction, not a safe choice, and it's the
fastest way to produce an interface indistinguishable from every other one.

### Declare the tokens

Every category below needs a declared value — "none, deliberately" is a
valid answer for a category the project genuinely doesn't need yet; silent
absence is not, because nothing distinguishes an omission from a decision.

- **Color** — one dominant brand color, a small number of accents, a
  neutral scale, and semantic colors for success/warning/danger/info.
- **Typography** — font family or families by purpose, a numeric size
  scale, the weights actually used, and line-heights paired to each size.
- **Spacing** — a scale, used consistently for margin, padding, and gap
  alike, not reinvented per component.
- **Border-radius** — a scale, applied the same way across cards, buttons,
  and inputs.
- **Shadow and elevation** — at least one token if the design uses depth at
  all; declare none-needed if it's flat.
- **Motion** — the easing and duration values used in transitions, even if
  it's just one of each.

### Declare the core component patterns

Cover what this project's own scenarios actually need — not a generic
checklist padded out for its own sake. A pattern description needs to be
concrete enough for the next screen to compose from without guessing:
buttons and their states, form fields and their error/disabled treatment,
selection controls, cards, navigation, modals, toasts, tables — whichever
of these (and whatever else) the project will actually use.

### Check cross-pattern coherence

The same token values should show up everywhere a pattern recurs: one
focus treatment across every interactive element, one spacing scale
whether it's inside a card or a modal, matching radii unless a difference
is deliberate and stated. A coherence failure is a defect regardless of
which specific value turns out to be "right" — pick one and apply it
everywhere.

### Design for accessibility by construction

Bake these in while deciding the system, because they're what make
conformance possible for every screen built after:

- A single declared focus-state pattern every interactive element
  inherits.
- Color pairs in the palette that clear standard contrast thresholds for
  text against its background.
- Control patterns sized to a reasonable touch target by default.
- A type scale where heading levels are visually distinguishable from each
  other, so hierarchy survives all the way to a screen reader's outline.

This is design work, not an audit — you're choosing values that make these
things true, not checking whether a specific screen got them right. That
check belongs to `accessibility-engineer`.

## Reviewing or evolving an existing one

When asked to review, audit, or improve an existing design system, the
first job is telling preferences apart from problems.

**Preferences** are choices that are neither right nor wrong — a specific
palette, a font family (as long as it's legible), a border-radius value, a
sidebar instead of a top nav, light versus dark theme. Don't suggest
changing these. They were decided on purpose.

**Problems** are choices that will cause real harm: a contrast pair that
fails standard thresholds, no strategy for smaller screens, a heading
hierarchy that skips a level, body text small enough to hurt readability,
no defined focus state, spacing values with no scale behind them, no
semantic color system for state, touch targets too small to reliably tap.

For each problem found: state what it is, why it matters concretely, and a
specific fix. Present findings without changing anything; apply only what
the user approves. If they push back on a finding, drop it — it was a
preference wearing a problem's clothes.

## Propose before restructuring

If evolving the system means changing the layout shell or an established
pattern in a way that would ripple into screens already built on it,
describe the change and its consequences before applying it. This is the
same "get approval for every real decision" discipline `architecture-design`
already applies to structural changes — a binding constraint doesn't stop
being binding just because you're the one revising it.

## Output format

```markdown
# Design system: <project name>

## Direction
Purpose, tone, and what should make this interface memorable — stated,
not left implicit. If more than one candidate was rendered, name which
one was chosen and link its screenshot in `visual-ux/`.

## Candidates considered
Only when more than one direction was rendered. Each rejected candidate
described in prose and why it wasn't chosen — no saved file needed for
these, only the winning direction's screenshot persists in `visual-ux/`.
Omit this section entirely when the direction came from a reference and
only one mock was ever rendered.

## Platform
What this targets, and whether that was already established or decided
here.

## Tokens
Color, typography, spacing, border-radius, shadow, motion — one entry per
category, including any declared "none, deliberately."

## Component patterns
One entry per pattern this project actually needs, concrete enough to
compose from without guessing.

## Accessibility built in
The focus pattern, contrast approach, touch-target sizing, and heading
scale chosen — and why they hold up by construction.

## Findings (review/evolve only)
Problems found, separated from preferences left alone, each with why it
matters and the fix applied or proposed.
```

Keep it skimmable — this is what every future screen composes against, not
an exhaustive style guide nobody will read before their fifth screen.
