# Accessibility review: Slice 1 — Connect one institution and see its transactions

## What was checked, and how

All seven rendered mockups in `visual-ux/` (`screen-connect-start`,
`screen-connect-in-progress`, `screen-connect-failed`,
`screen-transactions-success`, `-preparing`, `-empty`, `-error`), driven
live in a browser rather than read from markup alone: keyboard focus via
`element.focus()` and computed-style inspection (synthetic `Tab` keydown
events weren't reliably reaching page focus in this session — noted so
this doesn't read as a live tab-order walkthrough), contrast computed from
the actual rendered color values via WCAG's relative-luminance formula,
and DOM structure/attribute inspection for headings, landmarks, and ARIA.
No `<input>`/`<label>` pairs exist anywhere in this slice — the provider's
embedded widget owns all credential entry, entirely outside this app's DOM
by `design-001`'s own decision — so check 6 (label-input pairing) doesn't
apply to this slice and isn't scored.

## Findings

**1. [High] The nav rail and quick-action control have no accessible path
at all.** `Location:` every screen's `nav.rail` (`.icon` × 4, `.add-btn`).
`Category:` check 7 (interactive-looking element, no real semantics).
Every one is a `<div>` with `tabIndex === -1` or no interactive role;
only the active "Accounts" icon carries a `title` attribute, which isn't
a reliable substitute for an accessible name and isn't announced
consistently by screen readers. Confirmed by querying `tabIndex` against
all five elements on `screen-connect-start.html`: zero are keyboard-
reachable. Not Critical today only because this slice's own acceptance
criteria don't require navigating anywhere else or using the quick action
— but every one of these controls needs a real `<button>`/`role="button"`
with `tabindex="0"`, keyboard handling, and an `aria-label` before a later
slice makes any of them do something, or this becomes a required action
with no accessible path (this review's own Critical bar).
**Suggested fix:** replace `<div class="icon">`/`<div class="add-btn">`
with real `<button>` elements (or add `role="button"`, `tabindex="0"`,
`aria-label`, and keydown handling if the visual can't change), and use
`aria-current="page"` in place of `title` for the active destination.

**2. [High] The design system's declared focus treatment was never
implemented.** `Location:` all seven mockups' `<style>` blocks.
`Category:` check 4 (focus visible). `design-system-001.md`'s
"Accessibility built in" section declares one focus treatment — "2px
accent-blue outline, 2px offset" — applied to every interactive element.
None of the seven screens' CSS contains a `:focus` or `:focus-visible`
rule. Confirmed live: focusing the one real interactive element on
`screen-connect-start.html` (the primary button) falls back to the
browser's native default outline (`1px solid rgb(0,95,204)`, `0` offset),
not the declared system pattern. **Suggested fix:** add the declared
focus rule to the shared button/interactive-element styles once (ideally
promoted into whatever the real stylesheet becomes, rather than repeated
per screen).

**3. [High] Status-block titles carry no heading, unlike the pattern's own
precedent.** `Location:` `screen-connect-in-progress.html`,
`screen-connect-failed.html`, `screen-transactions-preparing.html`,
`screen-transactions-empty.html`, `screen-transactions-error.html`.
`Category:` check 3 (heading order/structure). `screen-design-001.md`
describes preparing/empty/error as one reused composition, and
`screen-connect-start.html`'s visually analogous empty-state title is a
real `<h2>` — but all five status-block titles ("Couldn't connect to
Chase," "Still preparing your transactions," "No transactions found,"
"Hosted by your data provider," "Couldn't retrieve your transactions")
are `<strong>` text. Confirmed: each of these five pages has exactly one
heading (`<h1>`, the page title) and zero others. A screen reader user
navigating by heading never encounters which outcome they landed on.
**Suggested fix:** use `<h2>` for the status-block title, matching
`screen-connect-start.html`'s own precedent.

**4. [High] The failed-retrieval retry button's text fails contrast.**
`Location:` `screen-transactions-error.html`, `.btn-retry` ("Try again").
`Category:` check 1 (contrast). Rendered color `#D64545` on white
measures 4.38:1; the button's 13px/600-weight label doesn't qualify as
large text, so the 4.5:1 threshold applies and this falls just short.
**Suggested fix:** darken the danger color for this specific text use (a
value around `#C23434` clears 4.5:1 against white) or add a filled
background behind the label instead of relying on text-on-white.

**5. [Medium] Status/banner containers declare no live region.**
`Location:` the same five screens as finding 3. `Category:` check 8 (live
region declared in markup). None declare `role="status"`, `role="alert"`,
or `aria-live` on the status-block container — checkable now, in the
static markup, independent of whether a real transition exists yet to
fire it. **Suggested fix:** add `role="status"` to the neutral/info
outcomes (preparing, empty) and `role="alert"` to the failure outcomes
(connect-failed, retrieval-error), on the container that replaces the
table/embed.

**6. [Medium] Decorative icons carry no `aria-hidden`.** `Location:`
every inline SVG across all seven screens (nav icons, empty-state glyph,
status dots). `Category:` check 2 (text alternatives). Each icon is
purely reinforcing adjacent text that already states the same thing, so
none needs an accessible name of its own — but none is marked
`aria-hidden="true"` either, so assistive tech may still announce an
unlabeled graphic alongside the text. **Suggested fix:** add
`aria-hidden="true"` to every purely decorative SVG.

**7. [Medium] The danger status-dot's icon-on-tint contrast is
borderline.** `Location:` `screen-transactions-error.html`, `.dot`
("!"). `Category:` check 1 (contrast). `#D64545` on `#FCEAEA` measures
3.77:1 — clears the 3:1 UI-component/large-text bar but would fail a
strict 4.5:1 normal-text read, and the glyph's 18px/700-weight sizing
sits right at the large-text cutoff, genuinely ambiguous rather than a
clear failure. Logged as Medium rather than blocking, since the same
meaning is redundantly available in the adjacent (currently non-heading —
see finding 3) title text.

**8. [Medium] Every interactive control falls below the 44×44 baseline.**
`Location:` all seven screens. `Category:` check 5 (touch-target size).
Confirmed via rendered `getBoundingClientRect()`: primary button 40px
tall, nav icons 44×40, the quick-action control 36×36, secondary/outline
buttons 38px tall, the retry button 36px tall. These match
`design-system-001.md`'s own declared values exactly (it states "nav
icons 44×40px, chips and secondary buttons ≥34px tall, primary buttons
40px tall") — the system declared these sizes itself; they just don't
clear the checked baseline. **This is a `design-system` token issue, not
a per-screen slip** — fixing it changes every screen built on these
tokens, so it routes back to `ux-designer:design-system` as a real,
propose-before-restructuring change rather than something to patch
per screen.

## Accessibility acceptance criteria

Replacing this slice's placeholder. Split by what this pass could confirm
against the rendered artifact versus what only becomes checkable once
real code exists.

**Confirmed-now — checkable against the shipped screens directly:**

> Given any screen in the connect-and-view-transactions flow,
> When a keyboard user tabs through it,
> Then every interactive element — including the account-rail navigation
> and the quick-action control — receives a visible focus indicator
> matching the design system's declared focus pattern, in an order that
> follows the screen's visual layout.

> Given a status or banner state is shown (connect failure, still-
> preparing, nothing-found, retrieval-failed),
> When the screen renders,
> Then the state's title is conveyed through a heading element, not
> through bold text alone.

> Given an icon used purely to reinforce adjacent text,
> When a screen reader reads the screen,
> Then the icon is hidden from the accessibility tree and only the
> adjacent text is announced.

> Given the primary action, reconnect, retry, and quick-action controls,
> When their rendered size is measured,
> Then each meets a minimum 44×44 CSS-pixel hit target, directly or via
> surrounding hit-area spacing.

> Given the "Try again" control on a failed-retrieval screen,
> When its text color is measured against its background,
> Then the contrast ratio is at least 4.5:1.

**Deferred — real, testable commitments that need real code to verify:**

> Given a connection attempt fails, times out, or the provider becomes
> unreachable,
> When the corresponding banner replaces the connect embed,
> Then a screen-reader user is notified that the state changed without
> needing to re-scan the page for it.

> Given the provider's embedded connection widget,
> When a user operates it by keyboard or screen reader,
> Then its accessibility is the provider's own responsibility — out of
> this app's scope by `design-001`'s own boundary, named here so it isn't
> mistaken for an oversight rather than a deliberate exclusion.

## Not yet verifiable

- **Full keyboard operability across a real interaction** (e.g., does
  focus land somewhere sensible after a real "Connect" hand-off or a real
  "Try again" retry) — `screen-design` renders one static file per state
  with no wiring between them, so there's no live transition to walk
  through yet.
- **Whether an added live-region role actually announces correctly** once
  wired to a real state change — finding 5 confirms the role is missing
  today; confirming it works is a real-code check.
- **Cognitive load under real, multi-step use** — each state was reviewed
  in isolation, not as a sequence a person actually moves through.

## Open questions

- ~~Finding 8 (touch targets) needs a `design-system` decision, not a
  per-screen fix — flagging back to `ux-designer` rather than resolving
  it here.~~ **Resolved by `design-system-001`'s "Findings" section:**
  every control pattern now meets 44×44px, applied to the mock and all
  seven of this slice's rendered screens.
- Everything under "Not yet verifiable" above stays open until real code
  exists to check it against — carried forward rather than dropped now
  that this pass is otherwise complete.
