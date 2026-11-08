# Accessibility review: pay a fine, slice 1

## What was checked, and how

The declined-state mockup, driven in the browser at design time; the
criteria below are what the built screen is held to.

## Accessibility acceptance criteria

- A1: Given the fines list is rendered, when a keyboard user tabs through
  it, then every Pay control receives a visible focus indicator in the
  order the fines are listed.
- A2: Given a payment is declined, when the declined notice appears, then
  it is announced to a screen reader (a live region or alert role) and
  the fine's Pay control keeps focus.
- A3: Given the fines list is rendered at a 360 px wide viewport, when a
  member reads it, then every fine's title, amount and Pay control are
  visible without horizontal scrolling.
- A4: Given any Pay control, when a member looks for it, then its
  accessible name says which fine it pays.
