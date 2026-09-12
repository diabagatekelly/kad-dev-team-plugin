# Accessibility review: Slice 4 — Reorder saved accounts (`screen-reorder-accounts.html`)

## What was checked, and how

One rendered mockup — `screen-reorder-accounts.html`, the single state `screen-design` produced for this slice. No file for it exists on disk in this session (checked: not present anywhere under this repo), so I couldn't load it by its own URL. Direct `data:` and `about:blank` navigation were both blocked by the browser extension in this session ("Can't interact with browser-internal or unparseable URLs"). I drove it live anyway rather than falling back to a markup-only read: opened a real Chrome tab and used `document.write()` to render the mockup's exact HTML/CSS as the live document, then checked it for real — actual `Tab` keypresses plus `document.activeElement` and computed-style inspection for focus order and visibility (confirmed with screenshots), the WCAG relative-luminance formula against colors read via `getComputedStyle` for contrast, `getBoundingClientRect()` for touch-target sizing, and the accessibility tree (`read_page`) plus direct DOM queries (`tabIndex`, `role`, `aria-*`) for structure and check 7. The one caveat: this was a reconstructed live document rather than the artifact loaded from its own file/URL, so anything that depends on the file's own location (e.g., the `/accounts/reorder-accessible` link actually resolving) wasn't and couldn't be followed — noted, not assumed.

Only one state exists for this slice, so there's no success/empty/error split to check across multiple files — check 5 (touch target), check 8 (live region), etc. are evaluated once, against this single render.

## Findings

**1. [Critical] The core required action of this screen — reordering — has no accessible path at all for keyboard-only or screen-reader users.** `Location:` `ul.card-list li[draggable="true"]`. `Category:` check 7 / escalation rule (no accessible path for a required action). Confirmed live: none of the three `<li>` elements carry a `tabindex`, a keydown handler, or any ARIA reorder pattern (`aria-grabbed`, `aria-dropeffect`, or a `role="listbox"`/`aria-selected` pattern with keyboard move support) — `li.tabIndex` is the browser default non-focusable value and `hasAttribute('tabindex')` is `false`. The only reordering mechanism is the HTML5 native drag-and-drop API, which is pointer-only. The mockup's own hint text acknowledges this and redirects affected users to a separate URL ("A fully accessible reorder view for screen-reader users is also available at /accounts/reorder-accessible") instead of making this screen operable. Per this review's own rule, an accessible version living elsewhere is never equivalent to fixing the screen in front of us — accessibility has to be the primary route, not a bolted-on alternate. This is the ceiling of severity regardless of how the rest of the screen reads. **Suggested fix:** add a keyboard-operable reordering mechanism to this same screen — e.g., a visible "move up"/"move down" control pair per row, or a keyboard-drag pattern (grab/move/drop via Space + arrow keys + Space, announced via `aria-live`) — and retire the separate-URL escape hatch as the primary accessibility strategy; it can remain as a redundant option, not the only one.

**2. [High] Primary navigation icons have no accessible path at all.** `Location:` `nav.rail .icon-nav` × 2 ("Accounts", "Reports"). `Category:` check 7. Confirmed live: both are `<div>`s with only an `onclick` handler and a `title` attribute — no `tabindex`, no `role`, not reachable by `Tab` (only the two `<button>` elements on the page are keyboard-focusable, confirmed by querying `[tabindex], button, a[href], input, select, textarea, [role="button"]`). The accessibility tree exposes each as a plain `generic "Accounts"`/`generic "Reports"` node, not a button or link — a screen-reader user browsing by control has no indication these are interactive at all, and a keyboard user cannot reach or activate them. This looks like a shared nav-rail component rather than something unique to this slice, so the fix likely belongs in the shared component — but it's a real, current defect on the artifact in front of me and is named here rather than deferred as "someone else's screen." **Suggested fix:** real `<button>` (or `role="button"` + `tabindex="0"` + Enter/Space keydown handling) with an `aria-label` (not `title` alone), plus `aria-hidden="true"` on the inner decorative SVG once the parent carries the accessible name.

**3. [High] The failed-save status title is not conveyed as a heading.** `Location:` `.status-block strong` ("Your changes couldn't be saved"). `Category:` check 3 (heading structure). Confirmed via DOM query: the only heading on the page is the single `<h1>` ("Reorder your accounts"); the failure title is a `<strong>`, not `<h2>`+. A screen-reader user navigating by heading will never land on this outcome and has to read the page linearly to discover the save failed. **Suggested fix:** use a real heading element (`<h2>`) for the status title.

**4. [High] The failed-save status block declares no live region.** `Location:` `.status-block`. `Category:` check 8. Confirmed via attribute inspection: `role`, `aria-live`, and `aria-atomic` are all `null`. This is checkable and missing today, independent of whether real save-failure wiring exists yet. Given this communicates an error that blocks the user's action, `role="alert"` is the appropriate choice over `role="status"`. **Suggested fix:** add `role="alert"` to `.status-block`.

**5. [High] The "Try again" control's text and border fail contrast.** `Location:` `.btn-retry`. `Category:` check 1. Confirmed via computed styles and the WCAG relative-luminance formula: `color: #E8A0A0` on a white background measures **2.11:1** — both the 4.5:1 text threshold and the 3:1 non-text/UI-component threshold (the border uses the same color) fail by a wide margin, not a borderline case. This is the only recovery action after a failed save, so low-vision users have a real, identifiable difficulty perceiving that a retry control exists at all. **Suggested fix:** darken `--danger-text` for this use (something in the `#B03A3A`–`#C23434` range clears 4.5:1 on white) or give the button a filled background instead of relying on light text/border on white.

**6. [Medium] Two controls fall below the 44×44 touch-target baseline.** `Location:` `.btn-retry` (measured 87×32) and each `.icon-nav` (measured 32×32). `Category:` check 5. Confirmed via `getBoundingClientRect()`. For the nav icons this compounds finding 2 — even a pointer/touch user with fine-motor impairment gets an undersized target on top of the missing semantics. **Suggested fix:** raise `.btn-retry` height to at least 44px (matching `.btn-primary`'s existing 44px), and size the nav icon hit area to 44×44 (padding around the current 18px glyph, not just the glyph itself).

**7. [Medium] The status-dot indicator is completely invisible.** `Location:` `.status-dot`, inline `style="background:#FCEAEA;color:#D64545;"`. `Category:` check 1 / general defect. Confirmed: the dot's `background-color` and its `.status-block` parent's `background-color` are both `rgb(252,234,234)` — a measured **1.00:1** contrast, i.e., no one can see it, sighted or not. This doesn't exclude anyone from the *information* (the adjacent text states the same failure redundantly), so it's Medium rather than High, but it reads as an unintentional bug — the `color` value (`#D64545`, presumably meant for a glyph or the background itself) never actually paints anything visible. **Suggested fix:** apply the intended color to whatever should render (an icon glyph, or swap `background`/`color` usage) and verify ≥3:1 against the `#FCEAEA` card once fixed.

**8. [Low] The reorderable list's accessible name presupposes an interaction some users can't perform.** `Location:` `ul.card-list[aria-label="drag to reorder your accounts"]`. `Category:` check 7, related to finding 1. Once a keyboard-operable reorder path exists (finding 1), this label should be revisited so it doesn't tell a screen-reader user to "drag" when that's not how they'll interact with it.

## Accessibility acceptance criteria

Replacing this slice's placeholder, sitting alongside the slice's existing functional criterion.

**Confirmed-now — checkable against the shipped screen directly:**

> Given the reorder-accounts screen with at least two saved accounts,
> When a keyboard-only or screen-reader user attempts to reorder them,
> Then a fully keyboard-operable reordering mechanism is available on this same screen — not solely through a separate URL.

> Given the reorder-accounts screen,
> When a keyboard user tabs through it,
> Then the "Accounts" and "Reports" navigation controls receive visible keyboard focus, are activatable with Enter or Space, and are exposed to assistive technology with an accessible name and a button or link role.

> Given the failed-save status block is rendered,
> When a screen-reader user navigates the page by heading,
> Then the failure message's title is conveyed through a heading element, not bold text alone.

> Given the failed-save status block is rendered,
> When its container markup is inspected,
> Then it declares `role="alert"` (or an equivalent live-region attribute).

> Given the "Try again" control,
> When its text and border colors are measured against their rendered background,
> Then both meet at least 4.5:1 (text) and 3:1 (border) contrast.

> Given the "Try again" control and the "Accounts"/"Reports" nav icons,
> When their rendered size is measured,
> Then each meets a minimum 44×44 CSS-pixel hit target, directly or via surrounding hit-area spacing.

> Given the status-dot indicator,
> When its color is measured against the status-block background,
> Then it meets at least 3:1 contrast, or is removed if it can't carry a visible, purposeful state.

**Deferred — real, testable commitments that need real code to verify:**

> Given a user reorders their saved accounts using the keyboard-operable mechanism (once implemented),
> When the save completes,
> Then the new order is confirmed to assistive technology without requiring the user to re-scan the list.

> Given a save attempt fails,
> When the status block appears or updates,
> Then a screen-reader user is notified of the failure without already needing focus inside that region.

> Given a full reorder-and-save flow completed by keyboard alone,
> When the flow finishes,
> Then focus lands somewhere sensible (the updated list or a confirmation), not lost to the top of the page or the body.

## Not yet verifiable

- **Whether the added live-region role actually announces correctly** once wired to a real failed-save transition — finding 4 confirms the role is missing today; confirming it fires correctly is a real-code check.
- **Whether focus moves anywhere sensible after a real save or a real retry** — this is one static file with no interaction wiring between states.
- **Full keyboard operability of the reorder flow end-to-end**, once a keyboard mechanism exists to build it against — today there's nothing to walk through (finding 1 covers the current, confirmable absence).
- **Cognitive load under real, multi-step use** — this screen was reviewed as a single static render, not as a sequence someone actually moves through.

## Open questions

- Finding 2 (nav rail) reads like a shared/global component issue rather than something unique to this slice — worth confirming with whoever owns the nav rail whether fixing it here also needs to happen wherever else it's reused, rather than only on this screen.
- Finding 1 is the one this review can't resolve alone: whether the fix is move-up/move-down buttons, a keyboard-drag pattern, or something else is a design call for `ux-designer`, not mine to prescribe beyond naming the requirement (a real keyboard path on this screen).
- Everything under "Not yet verifiable" stays open until real code exists to check it against — carried forward rather than dropped now that this pass is otherwise complete.
