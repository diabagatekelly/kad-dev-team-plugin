# Screen design: slice 001, staff cancel a member's hold from the desk screen (screen-design-001)

Built on `visual-ux/design-system-001.md`. One mockup per state:

- Holds list: `visual-ux/desk-holds.html`. The title's record header, the
  record table of holds (position, card ending, placed on), a quiet
  "Cancel" button per row.
- Cancelled state: `visual-ux/desk-holds-cancelled.html`. The notice in the
  ok tone, "Hold cancelled", the row gone from the table.
- Refused state: `visual-ux/desk-holds-refused.html`. The notice in the
  warn tone with the reason (card ending, title), the table unchanged.

## Interaction flow

Cancel → confirm in the row → the result state renders in place; focus
stays on the row's position in the table.

## States this slice changes

- `desk-holds`: new
- `desk-holds-cancelled`: new
- `desk-holds-refused`: new

The accessibility criteria are in `../accessibility-slice-001.md`.
