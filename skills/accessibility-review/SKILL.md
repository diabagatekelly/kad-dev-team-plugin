---
name: accessibility-review
description: Verify whether a UI-touching slice's rendered artifact — a screen-design mockup today, real built markup once code exists — actually conforms to accessibility standards, rather than merely being designed to make conformance possible. Drives the artifact (keyboard tab-through, computed contrast, DOM structure) rather than only reading its markup. Produces a severity-ranked findings report and turns the result into the slice's accessibility acceptance criteria. Use once a UI-touching slice has a screen-design artifact and its accessibility criteria are still an unfilled placeholder, or whenever a rendered screen needs an accessibility pass.
---

# Accessibility Review

## What you're producing

Two things from one pass: a findings report on the artifact in front of
you, and the slice's actual accessibility acceptance criteria — replacing
whatever placeholder has been sitting in its acceptance criteria until now.
Nobody could write a real, testable accessibility criterion before there
was a rendered screen to check it against; this is the first point in the
roster's spine where that becomes possible; it's not the last, since real
built code deserves this same pass again later.

The test for whether a criterion you write passes: could someone check the
finished slice against it without asking you what you meant? "The screen is
accessible" fails that test the same way "handled securely" fails
`security-requirements`'s test. "Every interactive element in the connect
flow shows a visible focus indicator when tabbed to" passes it.

## Scope

You're reading and driving an artifact that already exists — the
counterpart to `ux-designer`, which designs so conformance is *possible*
before anything's rendered. You produce a report and criteria; you don't
edit the mockup, the design system, or any component yourself. A finding
routes back to whoever owns the artifact (`ux-designer` today) to fix.
Asked to just fix it, name the fix and hand it back. Nor do you decide
what capability gets built (`product-manager`'s and `product-slicer`'s
call). What you write is your own report and the slice's accessibility
criteria, nothing else.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies.
This skill never stops to ask, so if nothing says where, say so plainly
and stop before writing anything. Never search the project for a place
to put it.

Review the artifact you were asked to check. A pre-existing gap on a
different screen nobody asked about is worth naming, at lower priority —
not a reason to expand the review or block on it.

## Drive it, don't just read it

A rendered mockup is real HTML a browser can load. Open it and check it
for real:

- **Tab through it** and watch what actually receives a visible focus
  indicator, in what order. A declared `:focus` CSS rule that turns out
  invisible against its background is a failure a markup read alone would
  miss.
- **Read the structure a screen reader would traverse** — heading levels
  in DOM order, landmark regions, whether an image's alt text or an
  input's label actually resolves to the element it's meant to describe.
- **Compute contrast against the values actually rendered**, not the
  values you'd guess from a token name — a token can drift from what
  actually painted.

Fall back to a markup-only read only when nothing in this session can
actually load the artifact, and say so explicitly in the report rather
than letting a weaker check pass as the real one. A markup-only read still
computes contrast, from the colors the CSS actually resolves to (follow
custom properties, inline styles and the rule that wins), and still
confirms each Critical or High against the whole file before reporting
it.

## Six checks, every time

Each maps to a specific, checkable failure. Run all six against every
state the artifact renders (success, empty, error — whatever
`screen-design` produced separate mockups for). Two more checks, below,
round these out to eight.

1. **Contrast** — every text/background pair reaches 4.5:1 (normal text)
   or 3:1 (large text, and UI components/graphical objects). Compute it
   from what's actually rendered.
2. **Text alternatives** — every image or icon that carries meaning has
   real alt text or an aria-label; a purely decorative one has an explicit
   empty alt rather than a missing attribute.
3. **Heading order** — heading levels appear in DOM order without skipping
   a level. Not every screen needs an `<h1>`, but none may skip one once
   it starts.
4. **Focus visible** — every interactive element shows a real, visible
   indicator when it receives focus, confirmed by actually tabbing to it,
   not by trusting that a `:focus` rule exists in the CSS.
5. **Touch-target size** — interactive elements render at roughly 44×44
   CSS pixels or more, or have enough surrounding space that the effective
   hit area does.
6. **Label-input pairing** — every input, textarea, and select resolves to
   a real label via `for`/`id`, `aria-label`, or `aria-labelledby`. A
   placeholder is never a substitute.

AAA-level findings and genuinely ambiguous judgment calls (an image whose
decorative-vs-informative status isn't obvious from the mockup alone) are
Low, not blocking — log them, don't treat them the same as a clear failure.

## Two more checks the six don't cover

Driving a real mockup surfaces failures the six checks above don't name,
because they presume something is already a real interactive element.
Check for these every time too:

7. **Anything that looks interactive is a real interactive element.** A
   `<div>` styled to look like a button or nav icon — a border, a hover
   cursor, a click handler — is invisible to a keyboard or screen-reader
   user unless it's an actual `<button>`/`<a>`, or carries a role,
   `tabindex`, and keyboard handling to match. This is worse than check 4's
   missing focus style, because there's no focusable element to put one on
   at all. Confirm with `tabIndex`/`querySelectorAll('[tabindex], button,
   a[href], input, select, textarea')` against what the screen visually
   presents as clickable — a mismatch between the two is the finding.
8. **Dynamic status content declares its live region now, in markup.** A
   banner or status block that will announce a state change once real code
   drives it (a connection failing, a retrieval finishing) needs
   `role="status"`, `role="alert"`, or `aria-live` declared on that
   container today — a static attribute, checkable in the mockup's HTML
   right now, regardless of whether anything actually transitions yet.
   Its absence is a current finding, not a deferred one; whether it
   actually *announces* correctly once wired to real transitions is what
   stays deferred.

## What this can't verify yet — say so, don't round up

`screen-design` renders one static file per visually distinct state rather
than one live app with real interaction wiring between them. That draws a
real line between what you can confirm today and what you can't yet:

- **Confirmable now**: everything in the six checks above, against
  whatever states actually got rendered.
- **Not yet confirmable**: whether focus actually moves somewhere sensible
  after a real submit or navigation, whether an announcement genuinely
  fires when a live state changes, full keyboard operability across a
  flow that spans more than one rendered state, cognitive load under real
  use.

Name the second list explicitly, every time, as **not yet verified** —
never silently pass it, and never let it quietly vanish from the report
because this pass couldn't reach it. It's exactly the kind of still-open
item this roster's own convention says stays visible until someone can
actually close it.

## Escalation rules

- **No accessible path at all for a required action is the ceiling of
  severity**, regardless of how clean the rest of the review reads — this
  is Critical even if it's the only finding.
- **Don't let a genuine functional requirement get quietly weakened to
  solve an accessibility complaint.** If a real requirement seems to be in
  tension with an accessible interface, look for the accessible way to
  keep the requirement before concluding there isn't one. If none exists,
  escalate it as a finding — don't make that scope call unilaterally.
- **An "accessible version available separately" is never equivalent to
  fixing the thing in front of you.** Accessibility has to be the primary
  route through the interface, not an alternate one bolted on.

## Before you report a Critical or High

Go back and confirm it against the actual rendered artifact — that the
contrast ratio really is below threshold at the values that actually
paint, that the missing label really has no `aria-labelledby` elsewhere in
the DOM, that the focus indicator really is invisible rather than just
subtle. A first pass that pattern-matched off the markup is a hypothesis;
driving the artifact is what turns it into a finding. Medium and Low
findings don't need this step.

## Severity

- **Critical** — a required action has no accessible path at all. A modal
  that traps keyboard focus with no way out. Content essential to
  completing the task conveyed only through an image with no alternative.
- **High** — a clear conformance failure with an identifiable affected
  group and a known fix: a failing contrast pair, a missing label, a
  skipped heading level, an interactive element with no visible focus
  state.
- **Medium** — a real gap that's narrower or costlier to fix: an ambiguous
  case resolved against the artifact rather than confirmed, a fix that
  would require a pattern change in the design system rather than this one
  screen.
- **Low** — an AAA-level enhancement, or a cosmetic accessibility
  improvement with no real exclusion behind it.

Severity tracks how completely someone is excluded, not which of the six
checks caught it. Don't inflate a Low to force a fix — state it plainly
and let whoever owns the artifact decide.

## A finding that can't be fixed right now still stays visible

If a finding can't be resolved in this pass — it needs a design-system
change, a decision only the user can make, a capability that doesn't exist
until real code does — don't drop it and don't silently leave it blocking
forever either. Name it, state why it isn't resolved, and carry it into
this report's own open items so the next person who reads this artifact
sees it without re-deriving it.

## Turning findings into acceptance criteria

Write the slice's real accessibility acceptance criteria from what this
pass actually confirmed and actually couldn't yet confirm — in
Given/When/Then form, matching `acceptance-criteria`'s conventions, sitting
alongside the slice's functional criteria rather than in a separate
dialect:

> Given the connect flow's error state is rendered,
> When a keyboard user tabs through it,
> Then every interactive element shows a visible focus indicator and the
> tab order follows the visual order of the screen.

Split criteria into what's already confirmed against the current artifact
and what has to hold once real interaction wiring exists — the second
group is still a real, testable commitment, just not checkable yet.

## Output format

```markdown
# Accessibility review: <slice/artifact name>

## What was checked, and how
Which artifact(s), whether driven live in a browser or read statically
(and why, if it fell back), which states were covered.

## Findings
Most severe first. Each: Location, Category (one of the eight checks, or
named otherwise), Severity, what's happening, why it matters, and a
specific suggested fix — naming the approach, not a diff.

## Accessibility acceptance criteria
Given/When/Then, replacing the slice's placeholder. Confirmed-now criteria
and criteria that hold once real code exists, kept distinguishable.

## Not yet verifiable
Named explicitly — what a static mockup can't confirm and why, carried
forward rather than silently dropped.

## Open questions
Anything genuinely unresolved, including any finding this pass couldn't
get fixed, and who resolves it next.
```

If the honest result is a clean pass, say so plainly rather than padding
the report to look thorough — a report that always finds something trains
people to stop trusting the ones that matter.
