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

### Commit to an intentional direction

Name what this interface is for, who uses it, and what should make it
memorable. Pick a real point of view — minimal, dense, playful, austere,
whatever actually fits the product — and execute it deliberately.
"Reasonable defaults with no particular character" is not a direction, it's
the absence of one, and it's the fastest way to produce an interface
indistinguishable from every other one. If a genuinely brand-defining
choice like this has more than one real candidate, that's a decision for
the user, not something to settle by picking the safer-looking option.

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
not left implicit.

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
