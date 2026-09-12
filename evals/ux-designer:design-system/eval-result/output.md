Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/design-system/SKILL.md

# Design system: Reading list

## Direction

**Card Catalog — chosen.** Warm and tactile: this is a personal tool for
saving something to read later, not a productivity dashboard, so it
should feel like flipping through a small, well-kept index — approachable
and a little nostalgic, not clinical. A two-column grid of individually
bounded cards (rather than a plain list) gives it a browsable, physical
quality; an amber/mustard accent against warm neutrals, a small top tab
on each card, and monospace "saved on" stamps carry the index-card feel
through without tipping into pure retro pastiche.

Three structurally distinct directions were rendered as real HTML
mockups and opened as separate browser tabs for live comparison before
this one was chosen; screenshot for the chosen direction:
`visual-ux/design-system.jpg` (source: `visual-ux/design-system.html`).

## Candidates considered

- **A — Quiet Stack.** A single-column, text-only feed with no card
  boundaries — links separated by a thin rule, note inline under the
  title, serif type, a single deep-indigo accent. The lowest-density,
  most minimal structure of the three. Not chosen: read as closer to a
  plain document than a place you'd enjoy browsing back through.
- **C — Bright Signal.** A single-column, high-density list with a
  favicon-style leading icon per link, pill tags, bold sans type,
  electric-blue accent — built for scanning many links quickly. Not
  chosen: optimized for a volume of saved links this project doesn't
  have; felt like a mismatch for a small personal tool with a handful of
  links a week.

## Platform

Responsive web app. Already established, not decided here:
`technology-bootstrap` fixed React with Vite as the UI framework; no
native or desktop path was ever on the table for this project.

## Tokens

**Color**
| Token | Value | Use |
|---|---|---|
| `--color-brand` | `#B8752E` | Primary actions, active states, card top-tab |
| `--color-accent` | `#7A4A1E` | Hover/pressed state for brand elements |
| `--color-neutral-50` | `#FBF8F3` | Page background (warm paper tone) |
| `--color-neutral-100` | `#F2ECE2` | Card background |
| `--color-neutral-300` | `#DDD2C0` | Borders, dividers |
| `--color-neutral-700` | `#4A4034` | Secondary text (timestamps, meta) |
| `--color-neutral-900` | `#231F19` | Primary text |
| `--color-danger` | `#B23B2E` | Errors (e.g. a save that fails outright) |

**Typography** — Inter for all UI text; timestamps and the "saved on"
stamp in a monospace face (`--font-mono`, "IBM Plex Mono") for the
literal index-card feel.
| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `--text-xs` | 12/16 | 400 (mono) | Timestamps, card stamp |
| `--text-sm` | 14/20 | 500 | Note text, secondary labels |
| `--text-base` | 16/24 | 400–600 | Link titles, body |
| `--text-xl` | 24/32 | 700 | Page heading |

**Spacing** — 4px base scale: 4, 8, 12, 16, 24, 32, 48. One scale for
padding, gaps (including the grid gap between cards), and margins alike.

**Border-radius** — `--radius-sm` 6px (inputs, buttons), `--radius-md`
10px (cards).

**Shadow** — `--shadow-card`: `0 2px 6px rgba(35,31,25,0.10)`, a soft
paper-lift on every card; no deeper elevation tier needed at this scale.

**Motion** — one token: `150ms ease-out`, for hover/press only. None,
deliberately, for page-level transitions — nothing here needs one yet.

## Component patterns

- **Save form** — a single URL input plus an optional note field, one
  primary "Save" button. Inline validation only on submit (a malformed
  URL), not as-you-type.
- **Link card** — a two-column grid item (single column on narrow
  viewports): a small colored top tab (`--color-brand`), title (fetched,
  or the raw URL as fallback), note beneath it if present, a monospace
  "saved on" stamp in the corner, `--radius-md`, `--shadow-card`. The
  grid, not a stacked list, is the point of this direction — cards read
  as individual index cards you browse, not rows you scan.
- **Empty state** — centered within the grid area, spanning both
  columns: a short heading, one line explaining what belongs here, and a
  hint pointing at the save form already visible above it — not a
  separate call-to-action button, since the form is already on screen.
- **Button** — primary (brand-amber fill, dark text, `--shadow-card` on
  hover) for "Save"; no secondary variant needed yet — this slice has
  exactly one committing action.

## Accessibility built in

- **Focus state** — a 3px `--color-accent` outline, 2px offset, applied
  via `:focus-visible` to the input and the button.
- **Contrast** — `--color-neutral-900` on `--color-neutral-50` measures
  ≈15:1; the primary button's dark text on the amber `--color-brand` fill
  clears 4.5:1.
- **Touch target** — the save button pads to a 44px effective height.
- **Type scale** — heading weight (700) is set well apart from body
  (400–600), so hierarchy survives to a screen reader's outline.

Confirming that a built screen actually conforms is
`accessibility-engineer`'s job, once that persona exists in this roster —
this section is what makes conformance possible, not a compliance claim.
