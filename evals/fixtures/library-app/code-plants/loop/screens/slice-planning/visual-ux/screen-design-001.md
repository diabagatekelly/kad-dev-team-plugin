# Screen design: slice 001, staff cancel a member's hold on a title (screen-design-001)

## Thin path covered
What the desk sees after a cancel: the hold is gone, the cancel was
refused, or the queue could not be reached.

## Layout and composition
The holds desk as it is (screen-design-000), with the notice's three
outcomes. Examples are invented.

- Hold cancelled: `visual-ux/hold-cancelled.html`, as it is today.
- Hold not cancelled: `visual-ux/hold-not-cancelled.html`. The refusal now
  names the card's last four digits, and the notice is tinted and given
  more room so the reason is read before the next member is served.
- Queue failure: `visual-ux/queue-failure.html`. The red edge, untinted:
  nothing was refused, the queue did not answer.

## Interaction flow
A cancel answers with one of the three notices. Dismiss removes it. After
a queue failure the desk tries the cancel again by hand.

## States this slice changes

- `hold-not-cancelled`: changed, the tint and the wider padding
- `queue-failure`: new

## New patterns proposed, if any
None.

## Open questions
None.
