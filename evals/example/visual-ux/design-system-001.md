# Design system: Replace by-hand Excel accounting

## Direction

Reference: Wave (waveapps.com/accounting), matched rather than reinterpreted,
per the user's explicit choice of a named product to match. Read directly
from two sources — Wave's own marketing site (navigated live, screenshotted)
and two screenshots of Wave's actual Transactions screen the user supplied
directly after the first pass missed the mark.

This project has no marketing surface — it's a single-user tool with no
landing page — so the match target is Wave's *product* look (white cards,
navy icon rail, restrained neutrals) rather than its colorful marketing site
(navy/violet gradients, serif display headlines). That's a deliberate
narrowing of the reference, not a partial match: there's nothing in this
project for a marketing-style serif headline to sit on.

One mock was rendered — the transaction-list screen slice 1 actually ships —
and confirmed as a faithful match after one revision round. The first pass
used solid-filled icon badges, a shaded gray table header, and a solid navy
sidebar close to black; the user supplied two further screenshots of Wave's
real Transactions screen, which corrected that to outline-style nav icons, a
white (not shaded) table header, a lighter/more saturated navy, and green
reserved only for credit amounts — debits stay plain dark text, matching what
the reference itself does.

## Platform

Responsive web app, browser-based. Already implied by two decisions made
before this skill ran, not re-opened here: `technology-bootstrap-001` chose
React + Vite (a browser-only stack), and `problem.md`'s hosted-anywhere
constraint requires eventual reachability "from any device." Slice 1 itself
runs desktop-local in a browser tab; the layout should tolerate a narrower
window since hosted-anywhere is already on the roadmap, but no dedicated
mobile/tablet breakpoint work has been done — declared out of scope until a
step actually forces it.

## Tokens

**Color**
- Dominant — Navy `#16205C`: the icon-rail surface.
- Accent (interactive) — Royal blue `#2954E6`, darkening to `#1E44C4` on
  hover/press: primary buttons, links, active states, focus ring.
- Chip/tinted surface — `#EAF0FE`: background for filter/sort chips and
  informational banners, paired with the accent color as border and text.
- Neutral scale — page background `#F7F5F1` (warm off-white), card surface
  `#FFFFFF`, border `#DADCE3`, subtle row divider `#F1F2F5`, secondary text
  `#6B7280`, primary text `#111827`.
- Semantic — success/credit `#1C9B5A` (reserved for money coming in, not
  used as general numeric emphasis), warning `#C77D18`, danger `#D64545`
  (connection failures, destructive actions), info reuses the accent blue.
- Deliberate departure from the reference: debit/negative amounts stay in
  plain dark text rather than red. Red is reserved for actual failure states
  (a rejected connection), not routine negative numbers — this is what the
  reference itself does on close inspection, not an invented deviation.

**Typography**
- Family: Inter — an open substitute for Wave's proprietary product
  typeface, matched for its geometric, high-legibility character. One family
  for all UI text; Wave's serif display face lives only on its marketing
  site, which this project has no counterpart to, so it isn't carried over.
- Scale: 13 / 14 / 16 / 18 / 26 / 32px.
- Weights used: 400 (body), 600 (labels, buttons, table headers), 700 (page
  headings).
- Line-heights: 1.2 for headings, 1.5 for body and table text.

**Spacing** — 4px base unit: 4, 8, 12, 16, 20, 24, 32, 40, 48. One scale for
padding, gaps, and margins alike.

**Border-radius**
- `8px` — inputs, selects, dropdown-style controls.
- `12px` — cards and banners.
- Full pill (`999px`) — buttons and filter/sort chips.

**Shadow and elevation** — one token: `0 1px 2px rgba(16,27,76,0.06), 0 4px
12px rgba(16,27,76,0.08)`. Soft, low-contrast — the same layered-card look
the reference uses to stack its report panels.

**Motion** — one easing curve, `cubic-bezier(0.4, 0, 0.2, 1)`, at 150ms for
hover/focus state changes. No larger transition declared yet — none,
deliberately, until a screen actually needs one.

## Component patterns

- **Buttons** — three variants: primary (solid accent-blue pill, white text,
  for the single most important action on a screen), secondary (white pill,
  accent-blue border and text, for a paired lower-emphasis action like "Try
  again"), and chip (tinted-blue pill, for toggle-style filters like
  Filter/Sort — visually distinct from a committing action).
- **App shell** — a slim white top bar (wordmark only) above a fixed-width
  (68px) navy icon rail: outline-style SVG icons at 20px, a circular
  outlined "+" quick-action above the nav icons, and a dimmed (35% opacity)
  treatment for nav destinations that don't exist yet — this project's later
  scope-map steps.
- **Cards** — white surface, 12px radius, the one elevation token, no
  internal border. Contains the transaction table and any future
  tabular/report content.
- **Tables/lists** — white header row (not shaded) with a single bottom
  border, secondary-gray semibold column labels in normal case, row
  dividers in the subtle `#F1F2F5` tone, numeric columns right-aligned with
  tabular figures, credit amounts in success-green, everything else in
  primary text color.
- **Status banners** — three states this slice's acceptance criteria
  specifically require (info/"still preparing," neutral/"nothing found,"
  danger/"connection not established"), each a rounded tinted card with a
  small colored status dot, a bold title, a muted description line, and an
  optional inline action ("Try again") for the recoverable case.
- **Dropdown/select controls** — 8px-radius rectangular controls (distinct
  from the pill radius used for committing actions), thin neutral border.

## Accessibility built in

- Single focus treatment: 2px accent-blue outline, 2px offset, applied
  identically to buttons, chips, and (once built) inputs and nav icons.
- Contrast: primary text (`#111827`) on white/off-white clears 7:1; accent
  blue on white clears AA for UI components and large text; white text on
  the navy rail clears AAA.
- Color is never the only signal: every banner pairs its color with a status
  dot and a written label ("Connection not established," not just a red
  tint); credit amounts stay bold and consistently positioned, not
  color-only.
- Touch targets: nav icons 44×40px, chips and secondary buttons ≥34px tall,
  primary buttons 40px tall.
- Heading scale (26/18px vs. 14/13px body) keeps hierarchy visually and
  structurally distinguishable.

## Findings (review/evolve only)

Not applicable — this is the system's first establishment, not a review of
an existing one.

---

Artifacts: `visual-ux/design-system-mock.html` (the rendered mock, confirmed
as a faithful match) and `visual-ux/design-system-mock.jpg` (its
screenshot). No losing candidates to record — the reference path renders one
mock, not several.
