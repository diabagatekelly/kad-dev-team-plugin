# Design system: Riverside Library member portal

## Direction

**Reading room.** Calm, plain and unhurried, like the library's own
signage: warm paper background, one deep teal for anything you act on,
generous spacing. Members come here to sort out something small (a loan,
a fine) and leave; nothing competes with the one thing they came to do.
Chosen from three rendered candidates; mock: `visual-ux/design-system.html`.

## Candidates considered

- **Index card:** bordered cards with a typewriter face. Rejected: the
  novelty wore thin on a page about money owed.
- **Dashboard:** dense tables and summary tiles. Rejected: built for staff
  volume, not a member with one or two items.

## Platform

Responsive web, phone first: the portal is a browser app (the card is
tokenised in the browser, `design-001.md`), and most members open it on a
phone. Decided here with the user.

## Tokens

**Color**

| Token | Value | Use |
|---|---|---|
| `--paper` | `#FAF7F2` | Page background |
| `--surface` | `#FFFFFF` | Cards, form panels |
| `--ink` | `#1F2A33` | Body text, headings |
| `--muted` | `#9AA3AA` | Secondary text, field help |
| `--border` | `#8A8178` | Card and input borders |
| `--brand` | `#1F5F5B` | Primary buttons, links |
| `--brand-hover` | `#174845` | Primary hover/pressed |
| `--success` / `--success-bg` | `#2E6B3A` / `#E6F2E8` | Success notice |
| `--danger` / `--danger-bg` | `#A3302A` / `#FBEAE8` | Error notice, field errors |

**Typography:** `system-ui` stack throughout; amounts use
`font-variant-numeric: tabular-nums`.

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `--text-sm` | 14/20 | 400 | Secondary text, field help |
| `--text-base` | 16/24 | 400, 600 | Body, labels, buttons |
| `--text-lg` | 20/28 | 600 | Section headings (h2) |
| `--text-xl` | 28/36 | 700 | Page heading (h1) |

**Spacing:** 4, 8, 12, 16, 24, 32, 48 (px), for padding, gaps and margins
alike.

**Border-radius:** `--radius-sm` 6px (buttons, inputs, notices),
`--radius-md` 8px (cards).

**Shadow:** none, deliberately: cards separate by border and spacing.

**Motion:** `120ms ease-out` for hover and pressed colour changes only.

## Component patterns

- **Page shell:** header with the library name (links home) and a nav of
  the member's areas (My loans, My fines); `aria-current="page"` on the
  current one. One `h1` per page, sections under `h2`. Content column max
  640px, 16px side padding on phones.
- **Button:** primary (`--brand` fill, white text) for the one committing
  action on a screen; secondary (white, `--brand` text and border) for
  everything else. Min height 44px. Busy state: label changes to say
  what's happening ("Paying…"), button disabled until the result arrives.
  Labels are verb-first and name the outcome.
- **Card:** `--surface`, 1px `--border`, `--radius-md`, 16px padding. A
  card that can be chosen is a real control (a radio inside a
  `fieldset`/`legend` group, the whole card as its label); the chosen one
  gets a 2px `--brand` border *and* a visible "Selected" text, never colour
  alone.
- **Form field:** visible label above (`<label for>`), 44px input with a
  1px `--border`, help text below in `--muted`, error text below in
  `--danger` linked with `aria-describedby`. Placeholders never replace
  labels.
- **Notice:** full-width block above the content it's about, 4px left
  border in `--success` or `--danger` on the matching `-bg`, an
  `aria-hidden` icon, a short heading and one sentence saying what happens
  next. Success uses `role="status"`, error uses `role="alert"`.
- **Amount:** right-aligned, tabular figures, always with the currency
  symbol and two decimals (`$3.00`).

## Accessibility built in

- **Contrast:** `--ink` on `--paper` 13.67:1, `--muted` on `--paper`
  6.01:1, white on `--brand` 7.38:1, `--ink` on `--danger-bg` 12.55:1,
  `--success` on `--success-bg` 5.56:1; `--border` is 3.82:1 on
  `--surface`, enough for input boundaries.
- **Touch targets:** buttons, inputs, nav links and choosable cards are at
  least 44px high.
- **Headings:** 28/20/16 with weight steps 700/600/600, so h1 and h2 read
  as distinct levels.

Whether a built screen conforms is `accessibility-engineer`'s check; these
are the choices that make it possible.
